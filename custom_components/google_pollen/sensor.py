import logging
import requests
import voluptuous as vol
from datetime import datetime, timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_LATITUDE, CONF_LONGITUDE, CONF_LANGUAGE
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Google pollen"
DEFAULT_LANGUAGE = "en"  
BASE_URL = "https://pollen.googleapis.com/v1/forecast:lookup"
SCAN_INTERVAL = timedelta(hours=4)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_LATITUDE): cv.latitude,
    vol.Required(CONF_LONGITUDE): cv.longitude,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): cv.string, 
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    api_key = config.get(CONF_API_KEY)
    latitude = config.get(CONF_LATITUDE)
    longitude = config.get(CONF_LONGITUDE)
    language = config.get(CONF_LANGUAGE) 

    pollen_types = ["BIRCH", "HAZEL", "ALDER", "MUGWORT", "ASH", "COTTONWOOD", "OAK", "PINE", "OLIVE", "GRAMINALES", "RAGWEED", "ELM", "MAPLE", "JUNIPER", "CYPRESS_PINE", "JAPANESE_CEDAR", "JAPANESE_CYPRESS"]
    entities = [GooglePollenSensor(name, api_key, latitude, longitude, language, pollen_type) for pollen_type in pollen_types]
    add_entities(entities, True)

class GooglePollenSensor(Entity):
    def __init__(self, name, api_key, latitude, longitude, language, pollen_type):
        self._name = f"Pollen {pollen_type.lower()}"
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude
        self._language = language
        self._pollen_type = pollen_type
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    @property
    def icon(self):
        return "mdi:flower-pollen-outline"

    @Throttle(SCAN_INTERVAL)
    def update(self):
        try:
            params = {
                "key": self._api_key,
                "location.latitude": self._latitude,
                "location.longitude": self._longitude,
                "days": 4,
                "plantsDescription": 0,
                "languageCode": self._language
            }
            response = requests.get(BASE_URL, params=params)
            data = response.json()
            _LOGGER.debug("Pollen data: %s", data)

            if 'error' in data:
                _LOGGER.error(data['error']['message'])
                self._attributes = {}
                self._state = "Error"
                return

            daily_info = data.get("dailyInfo", [])
            pollen_values = [0, 0, 0, 0]

            for i, day_info in enumerate(daily_info):
                plant_info = day_info.get("plantInfo", [])
                for plant in plant_info:
                    if plant["code"] == self._pollen_type and "indexInfo" in plant:
                        pollen_values[i] = plant["indexInfo"].get("value", 0)
                        _LOGGER.debug(
                            "Code %s got displayName %s, with values %d / %d / %d / %d",
                            code,
                            display_name,
                            pollen_values[code][0],
                            pollen_values[code][1],
                            pollen_values[code][2],
                            pollen_values[code][3],
                        )

            self._attributes = {
                "tomorrow": pollen_values[1],
                "day 3": pollen_values[2],
                "day 4": pollen_values[3],
                "last_update": datetime.now()
            }
            self._state = pollen_values[0]

        except requests.RequestException as err:
            _LOGGER.error("Error fetching data: %s", err)
            self._state = None
            self._attributes = {}
