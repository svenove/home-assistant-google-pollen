"""Coordinator for Google Pollen data updates."""
from datetime import datetime, timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .utils import fetch_pollen_data

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=4)


class GooglePollenDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching and updating Google Pollen data."""
    def __init__(self, hass, api_key, latitude, longitude, language):
        self.api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.language = language

        super().__init__(
            hass,
            _LOGGER,
            name="Pollen",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        try:
            data = await fetch_pollen_data(
                api_key=self.api_key,
                latitude=self.latitude,
                longitude=self.longitude,
                language=self.language,
                days=4,
            )

            _LOGGER.debug("Pollen data: %s", data)

            if "error" in data:
                _LOGGER.error(data["error"]["message"])
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
                        "category": str(
                            pollen_info.get("indexInfo", {}).get("category", "No Data")
                        ),
                        "display_name": str(pollen_info.get("displayName", "")),
                        "in_season": str(pollen_info.get("inSeason", "False")),
                        "last_updated": datetime.now().isoformat(),
                        "description": str(
                            pollen_info.get("indexInfo", {}).get("indexDescription", "")
                        ),
                        "index_value": float(
                            pollen_info.get("indexInfo", {}).get("value", 0)
                        ),
                    }

            for pollen_code, pollen_data in result.items():
                result[pollen_code][0]["tomorrow"] = float(
                    pollen_data.get(1, {}).get("index_value", 0)
                )
                result[pollen_code][0]["day 3"] = float(
                    pollen_data.get(2, {}).get("index_value", 0)
                )
                result[pollen_code][0]["day 4"] = float(
                    pollen_data.get(3, {}).get("index_value", 0)
                )

            _LOGGER.debug("Result data: %s", result)

            return result

        except (ConnectionError, TimeoutError) as error:
            _LOGGER.error("Network error updating Google Pollen data: %s", error)
            return {}
        except ValueError as error:
            _LOGGER.error("Data error updating Google Pollen data: %s", error)
            return {}
