"""Constants for the Google Pollen integration."""

DOMAIN = "google_pollen"
DEFAULT_LANGUAGE = "en"

BASE_URL = "https://pollen.googleapis.com/v1/forecast:lookup"

POLLEN_CATEGORIES = ["GRASS", "TREE", "WEED"]
PLANT_TYPES = [
    "ALDER",
    "ASH",
    "BIRCH",
    "COTTONWOOD",
    "CYPRESS_PINE",
    "ELM",
    "GRAMINALES",
    "HAZEL",
    "JAPANESE_CEDAR",
    "JUNIPER",
    "MAPLE",
    "MUGWORT",
    "OAK",
    "OLIVE",
    "PINE",
    "RAGWEED",
]

CONF_POLLEN_CATEGORIES = "conf_pollen_categories"
CONF_POLLEN = "conf_pollen"
