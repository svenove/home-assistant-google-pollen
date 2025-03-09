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
