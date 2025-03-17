"""Config flow for Google Pollen integration."""

import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
)
import homeassistant.helpers.config_validation as cv

from .const import CONF_POLLEN, CONF_POLLEN_CATEGORIES, DEFAULT_LANGUAGE, DOMAIN
from .utils import fetch_pollen_data

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_schema(DOMAIN)

class GooglePollenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Google Pollen."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._init_info = {}
        self._pollen_categories = []
        self._pollen_types = []
        self._pollen_types_codes = []
        self._pollen_categories_codes = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            if not re.match(r"^AIza[0-9A-Za-z-_]{35}$", api_key):
                errors[CONF_API_KEY] = "invalid_api_key"
            else:
                try:
                    user_input[CONF_LATITUDE] = round(user_input[CONF_LATITUDE], 4)
                    user_input[CONF_LONGITUDE] = round(user_input[CONF_LONGITUDE], 4)
                    await self._fetch_pollen_data(user_input)
                    return await self.async_step_select_pollen()
                except aiohttp.ClientResponseError as error:
                    if error.status == 400:
                        errors[CONF_API_KEY] = "invalid_api_key"
                    else:
                        errors["base"] = "api_error"
                    _LOGGER.error("Error validating API key: %s", error)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): cv.string,
                    vol.Required(
                        CONF_LATITUDE, default=round(self.hass.config.latitude, 4)
                    ): cv.latitude,
                    vol.Required(
                        CONF_LONGITUDE, default=round(self.hass.config.longitude, 4)
                    ): cv.longitude,
                    vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): cv.language,
                }
            ),
            errors=errors,
        )

    async def async_step_select_pollen(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle the step to select pollen categories."""
        if user_input is not None:
            self._init_info[CONF_POLLEN_CATEGORIES] = [
                self._pollen_categories_codes[self._pollen_categories.index(category)]
                for category in user_input[CONF_POLLEN_CATEGORIES]
            ]
            self._init_info[CONF_POLLEN] = [
                self._pollen_types_codes[self._pollen_types.index(pollen)]
                for pollen in user_input[CONF_POLLEN]
            ]
            await self.async_set_unique_id(
                f"{self._init_info[CONF_LATITUDE]}-{self._init_info[CONF_LONGITUDE]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Pollen ({self._init_info[CONF_LATITUDE]}, {self._init_info[CONF_LONGITUDE]})",
                data=self._init_info,
            )

        return self.async_show_form(
            step_id="select_pollen",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLLEN_CATEGORIES, default=self._pollen_categories
                    ): cv.multi_select(self._pollen_categories),
                    vol.Required(
                        CONF_POLLEN, default=self._pollen_types
                    ): cv.multi_select(self._pollen_types),
                }
            ),
        )

    async def _fetch_pollen_data(self, init_info: dict[str, Any], user_input: dict[str, Any] | None = None) -> None:
        """Fetch pollen data from the API."""
        if CONF_API_KEY not in init_info:
            raise KeyError(f"Missing {CONF_API_KEY} in configuration")

        api_key = init_info[CONF_API_KEY]
        latitude = init_info[CONF_LATITUDE]
        longitude = init_info[CONF_LONGITUDE]
        language = user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE) if user_input else init_info.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

        pollen_data = await fetch_pollen_data(
            api_key=api_key,
            latitude=latitude,
            longitude=longitude,
            language=language,
            days=1,
        )

        self._init_info = init_info.copy()
        self._init_info[CONF_LANGUAGE] = language
        self._pollen_categories = [
            item["displayName"]
            for item in pollen_data["dailyInfo"][0]["pollenTypeInfo"]
        ]
        self._pollen_types = [
            item["displayName"]
            for item in pollen_data["dailyInfo"][0]["plantInfo"]
        ]
        self._pollen_categories_codes = [
            item["code"]
            for item in pollen_data["dailyInfo"][0]["pollenTypeInfo"]
        ]
        self._pollen_types_codes = [
            item["code"]
            for item in pollen_data["dailyInfo"][0]["plantInfo"]
        ]
