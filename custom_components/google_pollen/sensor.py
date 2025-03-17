"""Integration for Google Pollen sensors."""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_POLLEN,
    CONF_POLLEN_CATEGORIES,
    DEFAULT_LANGUAGE,
    DOMAIN,
    PLANT_TYPES,
    POLLEN_CATEGORIES,
)
from .coordinator import GooglePollenDataUpdateCoordinator
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_LATITUDE): cv.latitude,
        vol.Required(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): cv.string,
    }
)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities):
    """Set up the Google Pollen sensor from a config entry."""
    api_key = config_entry.data[CONF_API_KEY]
    latitude = config_entry.data[CONF_LATITUDE]
    longitude = config_entry.data[CONF_LONGITUDE]
    language = config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)

    coordinator = GooglePollenDataUpdateCoordinator(
        hass, api_key, latitude, longitude, language
    )

    await coordinator.async_config_entry_first_refresh()

    pollen_categories = config_entry.data.get(CONF_POLLEN_CATEGORIES, POLLEN_CATEGORIES)
    plant_types = config_entry.data.get(CONF_POLLEN, PLANT_TYPES)

    entities = []
    entities.extend(
        [GooglePollenSensor(coordinator, category) for category in pollen_categories]
    )
    entities.extend(
        [GooglePollenSensor(coordinator, plant_type) for plant_type in plant_types]
    )

    async_add_entities(entities, True)


class GooglePollenSensor(CoordinatorEntity, Entity):
    """Representation of a Google Pollen sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, pollen_type):
        """Initialize the Google Pollen sensor."""

        super().__init__(coordinator)
        self._pollen_type = pollen_type
        self._attr_unique_id = f"google_pollen_{pollen_type.lower()}_{coordinator.latitude}_{coordinator.longitude}"
        self._attr_name = self.get_display_name(pollen_type)
        self._attr_device_info = {
            "identifiers": {
                (DOMAIN, f"{coordinator.latitude}_{coordinator.longitude}")
            },
            "name": "Google Pollen",
            "manufacturer": "Google",
            "model": "Pollen API",
            "sw_version": "1.0",
            "entry_type": "service",
        }
        self._attr_device_class = "enum"
        self._attr_state_class = "measurement"

    def get_display_name(self, pollen_type):
        """Get the display name for the pollen type."""
        return (
            self.coordinator.data.get(pollen_type, {})
            .get(0, {})
            .get("display_name", pollen_type.capitalize())
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        return (
            self.coordinator.data.get(self._pollen_type, {})
            .get(0, {})
            .get("category", "No data")
        )

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes of the sensor."""
        return self.coordinator.data.get(self._pollen_type, {}).get(0, {})

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:flower-pollen"
