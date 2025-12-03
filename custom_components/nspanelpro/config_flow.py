"""Config flow for NSPanel Pro integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_PANEL_ID, CONF_PANEL_NAME, DEFAULT_PANEL_NAME

_LOGGER = logging.getLogger(__name__)


class NSPanelProConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NSPanel Pro."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the panel ID is unique
            panel_id = user_input[CONF_PANEL_ID]
            await self.async_set_unique_id(panel_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_PANEL_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PANEL_ID): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        )
                    ),
                    vol.Required(
                        CONF_PANEL_NAME, default=DEFAULT_PANEL_NAME
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "mqtt_topic": "domodreams/nspanelpro",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> NSPanelProOptionsFlow:
        """Get the options flow for this handler."""
        return NSPanelProOptionsFlow(config_entry)


class NSPanelProOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for NSPanel Pro."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PANEL_NAME,
                        default=self.config_entry.data.get(
                            CONF_PANEL_NAME, DEFAULT_PANEL_NAME
                        ),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        )
                    ),
                }
            ),
        )
