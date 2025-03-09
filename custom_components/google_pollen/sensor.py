import logging
import requests
import voluptuous as vol
from datetime import datetime, timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_LATITUDE, CONF_LONGITUDE, CONF_LANGUAGE
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from .const import DOMAIN, DEFAULT_LANGUAGE

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://pollen.googleapis.com/v1/forecast:lookup"
SCAN_INTERVAL = timedelta(hours=4)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_LATITUDE): cv.latitude,
    vol.Required(CONF_LONGITUDE): cv.longitude,
    vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): cv.string, 
})

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Google Pollen sensor from a config entry."""
    api_key = config_entry.data[CONF_API_KEY]
    latitude = config_entry.data[CONF_LATITUDE]
    longitude = config_entry.data[CONF_LONGITUDE]
    language = config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

    # Create sensors for both pollen categories and specific plant types
    pollen_categories = ["GRASS", "TREE", "WEED"]
    plant_types = ["BIRCH", "HAZEL", "ALDER", "MUGWORT", "ASH", "COTTONWOOD", "OAK", "PINE", "OLIVE", "GRAMINALES", "RAGWEED", "ELM", "MAPLE", "JUNIPER", "CYPRESS_PINE", "JAPANESE_CEDAR", "JAPANESE_CYPRESS"]
    
    entities = []
    entities.extend([GooglePollenSensor(category, api_key, latitude, longitude, language, category) for category in pollen_categories])
    entities.extend([GooglePollenSensor(plant_type, api_key, latitude, longitude, language, plant_type) for plant_type in plant_types])
    
    async_add_entities(entities, True)

# Keep the setup_platform for backwards compatibility
def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    api_key = config.get(CONF_API_KEY)
    latitude = config.get(CONF_LATITUDE)
    longitude = config.get(CONF_LONGITUDE)
    language = config.get(CONF_LANGUAGE)

    pollen_types = ["BIRCH", "HAZEL", "ALDER", "MUGWORT", "ASH", "COTTONWOOD", "OAK", "PINE", "OLIVE", "GRAMINALES", "RAGWEED", "ELM", "MAPLE", "JUNIPER", "CYPRESS_PINE", "JAPANESE_CEDAR", "JAPANESE_CYPRESS"]
    entities = [GooglePollenSensor(pollen_type, api_key, latitude, longitude, language, pollen_type) for pollen_type in pollen_types]
    add_entities(entities, True)

class GooglePollenSensor(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, name, api_key, latitude, longitude, language, pollen_type):
        self._attr_unique_id = f"google_pollen_{pollen_type.lower()}_{latitude}_{longitude}"
        self._attr_name = f"{name.capitalize()}"
        self._code = f"{pollen_type.upper()}"
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude
        self._language = language
        self._pollen_type = pollen_type
        self._state = None
        self._attributes = {}
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{latitude}_{longitude}")},
            "name": "Google Pollen",
            "manufacturer": "Google",
            "model": "Pollen API",
            "sw_version": "1.0",
            "entry_type": "service"
        }
        self._attr_device_class = "enum"
        self._attr_state_class = "measurement"

    @property
    def name(self):
        return self._attr_name
    @property
    def unique_id(self):
        return self._attr_unique_id
    @property
    def device_info(self):
        return self._attr_device_info
    @property
    def state(self):
        return self._state
    @property
    def extra_state_attributes(self):
        return self._attributes
    @property
    def icon(self):
        return "mdi:flower-pollen"
    @Throttle(SCAN_INTERVAL)
    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            params = {
                "key": self._api_key,
                "location.latitude": self._latitude,
                "location.longitude": self._longitude,
                "languageCode": self._language,
                "days": 1
            }
            response = await self.hass.async_add_executor_job(
                lambda: requests.get(BASE_URL, params=params)
            )
            response.raise_for_status()
            data = response.json()
            _LOGGER.debug("Pollen data: %s", data)

            if 'error' in data:
                _LOGGER.error(data['error']['message'])
                self._attributes = {}
                self._state = "Error"
                return

            daily_info = data.get("dailyInfo", [])
            if daily_info:
                today_info = daily_info[0]  # Get today's forecast
                # Check both pollenTypeInfo and plantInfo sections
                pollen_type_info = today_info.get("pollenTypeInfo", [])
                plant_info = today_info.get("plantInfo", [])
                
                # Combine both lists for processing
                all_info = pollen_type_info + plant_info
                
                for pollen_info in all_info:
                    if pollen_info.get("code") == self._code:
                        index_info = pollen_info.get("indexInfo", {})
                        self._state = index_info.get("category", "No Data")
                        self._attributes = {
                            "display_name": pollen_info.get("displayName", ""),
                            "in_season": pollen_info.get("inSeason", False),
                            "health_recommendations": pollen_info.get("healthRecommendations", []),
                            "last_updated": datetime.now().isoformat(),
                            "latitude": self._latitude,
                            "longitude": self._longitude,
                            "plant_description": pollen_info.get("plantDescription", ""),
                            "cross_reactions": pollen_info.get("crossReactions", []),
                            "season_start": pollen_info.get("seasonStart", ""),
                            "season_end": pollen_info.get("seasonEnd", ""),
                            "season_peak": pollen_info.get("seasonPeak", ""),
                            "season_info": pollen_info.get("seasonInfo", {}),
                            "description": index_info.get("indexDescription", ""),
                            "index_value": index_info.get("value", 0),
                            "index_display_name": index_info.get("displayName", ""),
                            "color": index_info.get("color", {}),
                            "index_category": index_info.get("category", ""),
                            "index_level": index_info.get("level", 0),
                            "index_trigger": index_info.get("trigger", {}),
                            "index_scale": index_info.get("scale", {})
                        }
                        
                        break
                else:
                    self._state = "Not Available"
                    self._attributes = {}

        except Exception as error:
            _LOGGER.error("Error updating Google Pollen sensor: %s", error)
            self._state = None
            self._attributes = {}
