import logging
import requests
from datetime import datetime, timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://pollen.googleapis.com/v1/forecast:lookup"
SCAN_INTERVAL = timedelta(hours=4)

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
                "days": 4  # Fetch data for 4 days
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
            result = {}

            for day_index, day_info in enumerate(daily_info):
                pollen_type_info = day_info.get("pollenTypeInfo", [])
                plant_info = day_info.get("plantInfo", [])
                all_info = pollen_type_info + plant_info

                for pollen_info in all_info:
                    pollen_code = pollen_info.get("code")
                    if pollen_code not in result:
                        result[pollen_code] = {}
                    result[pollen_code][day_index] = {
                        "category": pollen_info.get("indexInfo", {}).get("category", "No Data"),
                        "display_name": pollen_info.get("displayName", ""),  # Ensure displayName is included
                        "in_season": pollen_info.get("inSeason", False),
                        "health_recommendations": pollen_info.get("healthRecommendations", []),
                        "last_updated": datetime.now().isoformat(),
                        "latitude": self.latitude,
                        "longitude": self.longitude,
                        "description": pollen_info.get("indexInfo", {}).get("indexDescription", ""),
                        "index_value": pollen_info.get("indexInfo", {}).get("value", 0),
                        "index_display_name": pollen_info.get("indexInfo", {}).get("displayName", ""),
                        "color": pollen_info.get("indexInfo", {}).get("color", {}),
                        "index_category": pollen_info.get("indexInfo", {}).get("category", ""),
                        "index_level": pollen_info.get("indexInfo", {}).get("level", 0)
                    }
            # Add the new attributes
            for pollen_code, pollen_data in result.items():
                result[pollen_code][0]["tomorrow"] = pollen_data.get(1, {}).get("index_value", 0)
                result[pollen_code][0]["day 3"] = pollen_data.get(2, {}).get("index_value", 0)
                result[pollen_code][0]["day 4"] = pollen_data.get(3, {}).get("index_value", 0)

            _LOGGER.debug("Result data: %s", result)

            return result

        except Exception as error:
            _LOGGER.error("Error updating Google Pollen data: %s", error)
            return {}
