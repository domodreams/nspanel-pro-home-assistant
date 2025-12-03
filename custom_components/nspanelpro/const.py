"""Constants for NSPanel Pro integration."""

DOMAIN = "nspanelpro"

# MQTT Topics
MQTT_BASE_TOPIC = "domodreams/nspanelpro"

# Command topics (Panel → HA)
MQTT_CMD_LIGHT_SET = f"{MQTT_BASE_TOPIC}/cmd/light/+/set"
MQTT_CMD_LIGHT_BRIGHTNESS = f"{MQTT_BASE_TOPIC}/cmd/light/+/brightness"
MQTT_CMD_COVER_SET = f"{MQTT_BASE_TOPIC}/cmd/cover/+/set"
MQTT_CMD_COVER_POSITION = f"{MQTT_BASE_TOPIC}/cmd/cover/+/position"
MQTT_CMD_CLIMATE_MODE = f"{MQTT_BASE_TOPIC}/cmd/climate/+/mode"
MQTT_CMD_CLIMATE_PRESET = f"{MQTT_BASE_TOPIC}/cmd/climate/+/preset"
MQTT_CMD_CLIMATE_TEMPERATURE = f"{MQTT_BASE_TOPIC}/cmd/climate/+/temperature"

# State topics (HA → Panel)
MQTT_STATE_TOPIC = f"{MQTT_BASE_TOPIC}/state"

# Config keys
CONF_PANELS = "panels"
CONF_PANEL_ID = "panel_id"
CONF_PANEL_NAME = "panel_name"

# Defaults
DEFAULT_PANEL_NAME = "NSPanel Pro"
