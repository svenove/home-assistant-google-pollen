"""Constants for the Google Pollen integration."""

DOMAIN = "google_pollen"
DEFAULT_LANGUAGE = "en"

BASE_URL = "https://pollen.googleapis.com/v1/forecast:lookup"

POLLEN_CATEGORIES = ["GRASS", "TREE", "WEED"]
PLANT_TYPES = ["BIRCH", "HAZEL", "ALDER", "MUGWORT", "ASH", "COTTONWOOD", "OAK", "PINE", "OLIVE", "GRAMINALES", "RAGWEED", "ELM", "MAPLE", "JUNIPER", "CYPRESS_PINE", "JAPANESE_CEDAR"]

CONF_POLLEN_CATEGORIES = "conf_pollen_categories"
CONF_POLLEN = "conf_pollen"
