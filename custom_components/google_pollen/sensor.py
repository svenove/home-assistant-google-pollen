import logging
import requests
import voluptuous as vol
from datetime import datetime, timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_LANGUAGE
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
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

    coordinator = GooglePollenDataUpdateCoordinator(
        hass, api_key, latitude, longitude, language
    )

    await coordinator.async_config_entry_first_refresh()

    pollen_categories = ["GRASS", "TREE", "WEED"]
    plant_types = ["BIRCH", "HAZEL", "ALDER", "MUGWORT", "ASH", "COTTONWOOD", "OAK", "PINE", "OLIVE", "GRAMINALES", "RAGWEED", "ELM", "MAPLE", "JUNIPER", "CYPRESS_PINE", "JAPANESE_CEDAR", "JAPANESE_CYPRESS"]

    entities = []
    entities.extend([GooglePollenSensor(coordinator, category) for category in pollen_categories])
    entities.extend([GooglePollenSensor(coordinator, plant_type) for plant_type in plant_types])
    
    async_add_entities(entities, True)


class GooglePollenSensor(CoordinatorEntity, Entity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, pollen_type):
        super().__init__(coordinator)
        self._pollen_type = pollen_type
        self._attr_unique_id = f"google_pollen_{pollen_type.lower()}_{coordinator.latitude}_{coordinator.longitude}"
        self._attr_name = f"{pollen_type.capitalize()}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{coordinator.latitude}_{coordinator.longitude}")},
            "name": "Google Pollen",
            "manufacturer": "Google",
            "model": "Pollen API",
            "sw_version": "1.0",
            "entry_type": "service"
        }
        self._attr_device_class = "enum"
        self._attr_state_class = "measurement"

    @property
    def state(self):
        return self.coordinator.data.get(self._pollen_type, {}).get("category", "No Data")

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.get(self._pollen_type, {})

    @property
    def icon(self):
        return "mdi:flower-pollen"


class GooglePollenDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_key, latitude, longitude, language):
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.language = language
        
        super().__init__(
            hass,
            _LOGGER,
            name="Google Pollen",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        try:
            params = {
                "key": self.api_key,
                "location.latitude": self.latitude,
                "location.longitude": self.longitude,
                "languageCode": self.language,
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
                return {}

            daily_info = data.get("dailyInfo", [])
            if daily_info:
                today_info = daily_info[0]  # Get today's forecast
                pollen_type_info = today_info.get("pollenTypeInfo", [])
                plant_info = today_info.get("plantInfo", [])
                all_info = pollen_type_info + plant_info
                
                result = {}
                for pollen_info in all_info:
                    index_info = pollen_info.get("indexInfo", {})
                    result[pollen_info.get("code")] = {
                        "category": index_info.get("category", "No Data"),
                        "display_name": pollen_info.get("displayName", ""),
                        "in_season": pollen_info.get("inSeason", False),
                        "health_recommendations": pollen_info.get("healthRecommendations", []),
                        "last_updated": datetime.now().isoformat(),
                        "latitude": self.latitude,
                        "longitude": self.longitude,
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

                return result

            return {}
        except Exception as error:
            _LOGGER.error("Error updating Google Pollen data: %s", error)
            return {}
