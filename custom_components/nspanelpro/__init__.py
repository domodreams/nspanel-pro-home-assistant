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
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NSPanel Pro from a config entry."""
    _LOGGER.info("=== async_setup_entry called for entry: %s ===", entry.entry_id)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "subscriptions": [],
        "config": dict(entry.data),
    }

    # Register frontend (only once, protected by guard in the function)
    _LOGGER.info("About to call _async_register_frontend")
    await _async_register_frontend(hass)
    _LOGGER.info("Returned from _async_register_frontend")

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
    # Check if already registered to prevent duplicates
    if hass.data[DOMAIN].get("frontend_registered"):
        _LOGGER.debug("Frontend already registered, skipping")
        return
    
    _LOGGER.info("Starting frontend registration for NSPanel Pro")
    
    # Serve the card JS from the integration
    card_path = hass.config.path("custom_components/nspanelpro/www/nspanelpro-config-card.js")
    _LOGGER.debug("Card file path: %s", card_path)
    
    # Check if file exists
    import os
    if os.path.exists(card_path):
        _LOGGER.info("Card file exists at: %s", card_path)
    else:
        _LOGGER.error("Card file NOT FOUND at: %s", card_path)
        return
    
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                "/nspanelpro/nspanelpro-config-card.js",
                card_path,
                cache_headers=False,
            )
        ])
        _LOGGER.info("Successfully registered static path: /nspanelpro/nspanelpro-config-card.js")
    except RuntimeError as err:
        _LOGGER.warning("Could not register static path (likely already registered): %s", err)
    except Exception as err:
        _LOGGER.error("Unexpected error registering static path: %s", err, exc_info=True)

    # Register as a Lovelace resource
    await _async_add_lovelace_resource(hass)

    hass.data[DOMAIN]["frontend_registered"] = True
    _LOGGER.info("NSPanel Pro frontend card registration complete")


async def _async_add_lovelace_resource(hass: HomeAssistant) -> None:
    """Add the card to Lovelace resources."""
    _LOGGER.info("Attempting to register Lovelace resource")
    
    # Add version to force cache refresh
    url = "/nspanelpro/nspanelpro-config-card.js?v=1.0.7"
    _LOGGER.debug("Resource URL: %s", url)
    
    # Get Lovelace resources collection
    # This key is used by the frontend component to store resources
    resources = hass.data.get("lovelace_resources")
    
    if not resources:
        _LOGGER.warning("Lovelace resources not available - you may be using YAML mode")
        _LOGGER.warning("Add this to your configuration.yaml:")
        _LOGGER.warning("lovelace:")
        _LOGGER.warning("  resources:")
        _LOGGER.warning("    - url: %s", url)
        _LOGGER.warning("      type: module")
        return

    _LOGGER.debug("Lovelace resources collection found")
    
    # Ensure resources are loaded
    if not resources.loaded:
        _LOGGER.debug("Loading Lovelace resources...")
        await resources.async_load()

    # List all current resources for debugging
    current_resources = list(resources.async_items())
    _LOGGER.debug("Current Lovelace resources count: %d", len(current_resources))
    for res in current_resources:
        _LOGGER.debug("  - %s (type: %s)", res.get("url"), res.get("res_type"))

    # Check if already exists or needs update
    for resource in resources.async_items():
        if resource["url"].startswith("/nspanelpro/nspanelpro-config-card.js"):
            if resource["url"] == url:
                _LOGGER.info("Lovelace resource already registered with correct version: %s", url)
                return
            else:
                # Update existing resource with new version
                _LOGGER.info("Updating Lovelace resource from %s to %s", resource["url"], url)
                try:
                    await resources.async_update_item(resource["id"], {"url": url})
                    _LOGGER.info("Successfully updated Lovelace resource")
                    return
                except Exception as err:
                    _LOGGER.error("Could not update Lovelace resource: %s", err, exc_info=True)
                    return

    # Add resource
    _LOGGER.info("Adding new Lovelace resource: %s", url)
    try:
        await resources.async_create_item({
            "res_type": "module",
            "url": url,
        })
        _LOGGER.info("Successfully auto-registered Lovelace resource: %s", url)
    except Exception as err:
        _LOGGER.error("Could not auto-register Lovelace resource: %s", err, exc_info=True)


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
