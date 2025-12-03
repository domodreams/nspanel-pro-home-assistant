"""NSPanel Pro Integration for Home Assistant."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    MQTT_BASE_TOPIC,
    MQTT_CMD_LIGHT_SET,
    MQTT_CMD_LIGHT_BRIGHTNESS,
    MQTT_CMD_COVER_SET,
    MQTT_CMD_COVER_POSITION,
    MQTT_CMD_CLIMATE_MODE,
    MQTT_CMD_CLIMATE_PRESET,
    MQTT_CMD_CLIMATE_TEMPERATURE,
)
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the NSPanel Pro component."""
    hass.data.setdefault(DOMAIN, {})
    
    # Register frontend once at startup
    await _async_register_frontend(hass)
    
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NSPanel Pro from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "subscriptions": [],
        "config": dict(entry.data),
    }

    # Set up services
    await async_setup_services(hass)

    # Set up MQTT subscriptions
    await _async_setup_mqtt_bridge(hass, entry)

    # Forward to platforms if any
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unsubscribe from MQTT topics
    data = hass.data[DOMAIN].get(entry.entry_id, {})
    for unsubscribe in data.get("subscriptions", []):
        unsubscribe()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Check if there are any config entries left
        # Filter out non-entry keys like 'frontend_registered'
        has_entries = any(k for k in hass.data[DOMAIN] if k != "frontend_registered")
        
        if not has_entries:
            await async_unload_services(hass)

    return unload_ok


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Register the frontend card."""
    # Serve the card JS from the integration
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            "/nspanelpro/nspanelpro-config-card.js",
            hass.config.path("custom_components/nspanelpro/www/nspanelpro-config-card.js"),
            cache_headers=False,
        )
    ])

    # Register as a Lovelace resource
    await _async_add_lovelace_resource(hass)

    hass.data[DOMAIN]["frontend_registered"] = True
    _LOGGER.info("NSPanel Pro frontend card registered at /nspanelpro/nspanelpro-config-card.js")


async def _async_add_lovelace_resource(hass: HomeAssistant) -> None:
    """Add the card to Lovelace resources."""
    url = "/nspanelpro/nspanelpro-config-card.js"
    
    # Get Lovelace resources collection
    # This key is used by the frontend component to store resources
    resources = hass.data.get("lovelace_resources")
    
    if not resources:
        _LOGGER.debug("Lovelace resources not available (likely in YAML mode)")
        return

    # Ensure resources are loaded
    if not resources.loaded:
        await resources.async_load()

    # Check if already exists
    for resource in resources.async_items():
        if resource["url"] == url:
            _LOGGER.debug("Lovelace resource already registered: %s", url)
            return

    # Add resource
    try:
        await resources.async_create_item({
            "res_type": "module",
            "url": url,
        })
        _LOGGER.info("Auto-registered Lovelace resource: %s", url)
    except Exception as err:
        _LOGGER.warning("Could not auto-register Lovelace resource: %s", err)


async def _async_setup_mqtt_bridge(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up MQTT bridge for panel commands."""
    subscriptions = []

    # Light handlers
    @callback
    def handle_light_set(msg: mqtt.ReceiveMessage) -> None:
        """Handle light on/off commands."""
        topic_parts = msg.topic.split("/")
        entity_name = topic_parts[4]  # domodreams/nspanelpro/cmd/light/{entity}/set
        entity_id = f"light.{entity_name}"
        payload = msg.payload.lower()

        _LOGGER.debug("Light set command: %s -> %s", entity_id, payload)

        if payload == "on":
            hass.async_create_task(
                hass.services.async_call("light", "turn_on", {"entity_id": entity_id})
            )
        elif payload == "off":
            hass.async_create_task(
                hass.services.async_call("light", "turn_off", {"entity_id": entity_id})
            )

    @callback
    def handle_light_brightness(msg: mqtt.ReceiveMessage) -> None:
        """Handle light brightness commands."""
        topic_parts = msg.topic.split("/")
        entity_name = topic_parts[4]
        entity_id = f"light.{entity_name}"

        try:
            brightness = int(msg.payload)
            _LOGGER.debug("Light brightness command: %s -> %d", entity_id, brightness)
            hass.async_create_task(
                hass.services.async_call(
                    "light", "turn_on", {"entity_id": entity_id, "brightness": brightness}
                )
            )
        except ValueError:
            _LOGGER.warning("Invalid brightness value: %s", msg.payload)

    # Cover handlers
    @callback
    def handle_cover_set(msg: mqtt.ReceiveMessage) -> None:
        """Handle cover open/close/stop commands."""
        topic_parts = msg.topic.split("/")
        entity_name = topic_parts[4]
        entity_id = f"cover.{entity_name}"
        payload = msg.payload.lower()

        _LOGGER.debug("Cover set command: %s -> %s", entity_id, payload)

        action_map = {
            "open": "open_cover",
            "close": "close_cover",
            "stop": "stop_cover",
        }

        if payload in action_map:
            hass.async_create_task(
                hass.services.async_call("cover", action_map[payload], {"entity_id": entity_id})
            )

    @callback
    def handle_cover_position(msg: mqtt.ReceiveMessage) -> None:
        """Handle cover position commands."""
        topic_parts = msg.topic.split("/")
        entity_name = topic_parts[4]
        entity_id = f"cover.{entity_name}"

        try:
            position = int(msg.payload)
            _LOGGER.debug("Cover position command: %s -> %d", entity_id, position)
            hass.async_create_task(
                hass.services.async_call(
                    "cover", "set_cover_position", {"entity_id": entity_id, "position": position}
                )
            )
        except ValueError:
            _LOGGER.warning("Invalid position value: %s", msg.payload)

    # Climate handlers
    @callback
    def handle_climate_mode(msg: mqtt.ReceiveMessage) -> None:
        """Handle climate mode commands."""
        topic_parts = msg.topic.split("/")
        entity_name = topic_parts[4]
        entity_id = f"climate.{entity_name}"
        hvac_mode = msg.payload.lower()

        _LOGGER.debug("Climate mode command: %s -> %s", entity_id, hvac_mode)
        hass.async_create_task(
            hass.services.async_call(
                "climate", "set_hvac_mode", {"entity_id": entity_id, "hvac_mode": hvac_mode}
            )
        )

    @callback
    def handle_climate_preset(msg: mqtt.ReceiveMessage) -> None:
        """Handle climate preset commands."""
        topic_parts = msg.topic.split("/")
        entity_name = topic_parts[4]
        entity_id = f"climate.{entity_name}"
        preset_mode = msg.payload

        _LOGGER.debug("Climate preset command: %s -> %s", entity_id, preset_mode)
        hass.async_create_task(
            hass.services.async_call(
                "climate", "set_preset_mode", {"entity_id": entity_id, "preset_mode": preset_mode}
            )
        )

    @callback
    def handle_climate_temperature(msg: mqtt.ReceiveMessage) -> None:
        """Handle climate temperature commands."""
        topic_parts = msg.topic.split("/")
        entity_name = topic_parts[4]
        entity_id = f"climate.{entity_name}"

        try:
            temperature = float(msg.payload)
            _LOGGER.debug("Climate temperature command: %s -> %f", entity_id, temperature)
            hass.async_create_task(
                hass.services.async_call(
                    "climate", "set_temperature", {"entity_id": entity_id, "temperature": temperature}
                )
            )
        except ValueError:
            _LOGGER.warning("Invalid temperature value: %s", msg.payload)

    # Subscribe to all command topics
    subscriptions.append(
        await mqtt.async_subscribe(hass, MQTT_CMD_LIGHT_SET, handle_light_set)
    )
    subscriptions.append(
        await mqtt.async_subscribe(hass, MQTT_CMD_LIGHT_BRIGHTNESS, handle_light_brightness)
    )
    subscriptions.append(
        await mqtt.async_subscribe(hass, MQTT_CMD_COVER_SET, handle_cover_set)
    )
    subscriptions.append(
        await mqtt.async_subscribe(hass, MQTT_CMD_COVER_POSITION, handle_cover_position)
    )
    subscriptions.append(
        await mqtt.async_subscribe(hass, MQTT_CMD_CLIMATE_MODE, handle_climate_mode)
    )
    subscriptions.append(
        await mqtt.async_subscribe(hass, MQTT_CMD_CLIMATE_PRESET, handle_climate_preset)
    )
    subscriptions.append(
        await mqtt.async_subscribe(hass, MQTT_CMD_CLIMATE_TEMPERATURE, handle_climate_temperature)
    )

    hass.data[DOMAIN][entry.entry_id]["subscriptions"] = subscriptions
    _LOGGER.info("NSPanel Pro MQTT bridge initialized with base topic: %s", MQTT_BASE_TOPIC)
