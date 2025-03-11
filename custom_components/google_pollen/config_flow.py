"""Config flow for Google Pollen integration."""
import logging
import re
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_LANGUAGE
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import BASE_URL, DOMAIN, DEFAULT_LANGUAGE, PLANT_TYPES, CONF_POLLEN, CONF_POLLEN_CATEGORIES, POLLEN_CATEGORIES
from .utils import fetch_pollen_data

_LOGGER = logging.getLogger(__name__)

class GooglePollenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Google Pollen."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._init_info = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            if not re.match(r"^AIza[0-9A-Za-z-_]{35}$", api_key):
                errors[CONF_API_KEY] = "invalid_api_key"
            else:
                try:
                    data = await fetch_pollen_data(
                        api_key=api_key,
                        latitude=user_input[CONF_LATITUDE],
                        longitude=user_input[CONF_LONGITUDE],
                        language=user_input.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
                        days=1
                    )

                    latitude = float(user_input[CONF_LATITUDE])
                    longitude = float(user_input[CONF_LONGITUDE])
                    self._init_info = user_input
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
                    vol.Required(CONF_LATITUDE, default=self.hass.config.latitude): cv.latitude,
                    vol.Required(CONF_LONGITUDE, default=self.hass.config.longitude): cv.longitude,
                    vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): cv.language,
                }
            ),
            errors=errors,
        )

    async def async_step_select_pollen(self, user_input=None):
        if user_input is not None:
            self._init_info[CONF_POLLEN_CATEGORIES] = user_input[CONF_POLLEN_CATEGORIES]
            self._init_info[CONF_POLLEN] = user_input[CONF_POLLEN]
            await self.async_set_unique_id(f"{self._init_info[CONF_LATITUDE]}-{self._init_info[CONF_LONGITUDE]}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Pollen ({self._init_info[CONF_LATITUDE]}, {self._init_info[CONF_LONGITUDE]})",
                data=self._init_info
            )

        pollen_categories = POLLEN_CATEGORIES
        pollen = PLANT_TYPES
        return self.async_show_form(
            step_id="select_pollen",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POLLEN_CATEGORIES, default=pollen_categories): cv.multi_select(pollen_categories),
                    vol.Required(CONF_POLLEN, default=pollen): cv.multi_select(pollen)
                }
            )
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return GooglePollenOptionsFlow(config_entry)


class GooglePollenOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_LANGUAGE, default=self.config_entry.options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),): cv.language,
                }
            ),
        )
