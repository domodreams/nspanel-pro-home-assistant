"""Services for NSPanel Pro integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, MQTT_BASE_TOPIC

_LOGGER = logging.getLogger(__name__)

SERVICE_PUBLISH_STATE = "publish_state"
SERVICE_SEND_CONFIG = "send_config"

PUBLISH_STATE_SCHEMA = vol.Schema(
    {
        vol.Required("panel_id"): cv.string,
        vol.Required("entity_id"): cv.entity_id,
    }
)

SEND_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("panel_id"): cv.string,
        vol.Required("config"): dict,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for NSPanel Pro integration."""

    async def handle_publish_state(call: ServiceCall) -> None:
        """Handle the publish_state service call."""
        panel_id = call.data["panel_id"]
        entity_id = call.data["entity_id"]

        state = hass.states.get(entity_id)
        if state is None:
            _LOGGER.warning("Entity %s not found", entity_id)
            return

        # Build state payload
        payload = {
            "entity_id": entity_id,
            "state": state.state,
            "attributes": dict(state.attributes),
            "last_updated": state.last_updated.isoformat(),
        }

        topic = f"{MQTT_BASE_TOPIC}/state/{panel_id}/{entity_id.replace('.', '/')}"

        await mqtt.async_publish(
            hass,
            topic,
            json.dumps(payload),
            retain=True,
        )

        _LOGGER.debug("Published state for %s to %s", entity_id, topic)

    async def handle_send_config(call: ServiceCall) -> None:
        """Handle the send_config service call."""
        panel_id = call.data["panel_id"]
        config = call.data["config"]

        topic = f"{MQTT_BASE_TOPIC}/config/{panel_id}"

        await mqtt.async_publish(
            hass,
            topic,
            json.dumps(config),
            retain=True,
        )

        _LOGGER.debug("Published config to %s", topic)

    hass.services.async_register(
        DOMAIN,
        SERVICE_PUBLISH_STATE,
        handle_publish_state,
        schema=PUBLISH_STATE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_CONFIG,
        handle_send_config,
        schema=SEND_CONFIG_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for NSPanel Pro integration."""
    hass.services.async_remove(DOMAIN, SERVICE_PUBLISH_STATE)
    hass.services.async_remove(DOMAIN, SERVICE_SEND_CONFIG)
