"""Config flow for Home Assistant Nostr Bridge integration."""
import logging
import voluptuous as vol
from typing import Any, Dict

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_ENTITY_ID,
    CONF_RELAY_URL,
    CONF_PRIVATE_KEY,
    CONF_EVENT_KIND,
    DEFAULT_RELAY_URL,
    DEFAULT_EVENT_KIND,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="Nostr Bridge"): selector.TextSelector(),
        vol.Required(CONF_ENTITY_ID): selector.EntitySelector(),
        vol.Optional(CONF_RELAY_URL, default=DEFAULT_RELAY_URL): selector.TextSelector(),
        vol.Optional(CONF_PRIVATE_KEY): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_EVENT_KIND, default="36107"): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    {"value": "36107", "label": "36107 - Spontaneous Addressable Event (Replaceable IoT State)"}
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)


class NostrBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Home Assistant Nostr Bridge."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ENTITY_ID])
            self._abort_if_unique_id_configured()

            try:
                # Validate relay URL format
                relay_url = user_input[CONF_RELAY_URL]
                if not relay_url.startswith(("ws://", "wss://")):
                    errors["base"] = "invalid_relay_url"
                else:
                    # Ensure event_kind is stored as integer
                    if CONF_EVENT_KIND in user_input:
                        user_input[CONF_EVENT_KIND] = int(user_input[CONF_EVENT_KIND])
                    
                    return self.async_create_entry(
                        title=user_input[CONF_NAME], data=user_input
                    )
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Ensure event_kind is stored as integer
            if CONF_EVENT_KIND in user_input:
                user_input[CONF_EVENT_KIND] = int(user_input[CONF_EVENT_KIND])
            return self.async_create_entry(title="", data=user_input)

        # Get current values from the stored config entry
        current_data = self._config_entry.data
        current_options = self._config_entry.options

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENTITY_ID,
                    default=current_options.get(CONF_ENTITY_ID, current_data.get(CONF_ENTITY_ID))
                ): selector.EntitySelector(),
                vol.Required(
                    CONF_RELAY_URL,
                    default=current_options.get(CONF_RELAY_URL, current_data.get(CONF_RELAY_URL, DEFAULT_RELAY_URL))
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_PRIVATE_KEY,
                    default=current_options.get(CONF_PRIVATE_KEY, current_data.get(CONF_PRIVATE_KEY, ""))
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(
                    CONF_EVENT_KIND,
                    default="36107"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "36107", "label": "36107 - Spontaneous Addressable Event (Replaceable IoT State)"}
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )