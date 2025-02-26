import logging
import requests
import voluptuous as vol
from datetime import timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_LATITUDE, CONF_LONGITUDE, CONF_LANGUAGE
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Google pollen"
DEFAULT_LANGUAGE = "en"  
BASE_URL = "https://pollen.googleapis.com/v1/forecast:lookup"
SCAN_INTERVAL = timedelta(hours=6)

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

    add_entities([GooglePollenSensor(name, api_key, latitude, longitude, language)], True)

class GooglePollenSensor(Entity):
    def __init__(self, name, api_key, latitude, longitude, language):
        self._name = name
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude
        self._language = language
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
                "days": 2,
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
            pollen_values = {
                "BIRCH": [0, 0],
                "HAZEL": [0, 0],
                "ALDER": [0, 0],
                "MUGWORT": [0, 0],
                "ASH": [0, 0],
                "COTTONWOOD": [0, 0],
                "OAK": [0, 0],
                "PINE": [0, 0],
                "OLIVE": [0, 0],
                "GRAMINALES": [0, 0],
                "RAGWEED": [0, 0]
            }

            for i, day_info in enumerate(daily_info):
                plant_info = day_info.get("plantInfo", [])
                for plant in plant_info:
                    if plant["code"] in pollen_values and "indexInfo" in plant:
                        pollen_values[plant["code"]][i] = plant["indexInfo"].get("value", 0)

            # Update the attributes with pollen values using displayName
            self._attributes = {}
            for plant in daily_info[0]["plantInfo"]:
                code = plant["code"]
                display_name = plant["displayName"]
                self._attributes[f"{display_name.lower()}_today_({code.lower()})"] = pollen_values[code][0]
                self._attributes[f"{display_name.lower()}_tomorrow_({code.lower()})"] = pollen_values[code][1]

            # Set state to the highest pollen value for today
            today_values = [values[0] for values in pollen_values.values()]
            self._state = max(today_values) if today_values else 0

        except requests.RequestException as err:
            _LOGGER.error("Error fetching data: %s", err)
            self._state = None
            self._attributes = {}
