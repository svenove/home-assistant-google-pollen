"""Utility functions for Google Pollen integration."""
import logging

import aiohttp

from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)


async def fetch_pollen_data(api_key, latitude, longitude, language, days=1):
    """Fetch pollen data from the API."""
    try:
        params = {
            "key": api_key,
            "location.latitude": latitude,
            "location.longitude": longitude,
            "languageCode": language,
            "days": days,
            "plantsDescription": "false",
        }
        async with aiohttp.ClientSession() as session, session.get(BASE_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()

        _LOGGER.debug("API-result: %s", data)
        return data

    except aiohttp.ClientResponseError as error:
        _LOGGER.error("Error fetching pollen data: %s", error)
        raise

    except Exception as error:
        _LOGGER.error("Unexpected error: %s", error)
        raise
