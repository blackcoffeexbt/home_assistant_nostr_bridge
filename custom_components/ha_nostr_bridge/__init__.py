"""The Home Assistant Nostr Bridge integration."""
import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED, Platform
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONF_ENTITY_ID
from .nostr_client import NostrClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Home Assistant Nostr Bridge integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Assistant Nostr Bridge from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Merge config data with options (options take precedence)
    config_data = {**entry.data, **entry.options}
    
    nostr_client = NostrClient(hass, config_data)
    hass.data[DOMAIN][entry.entry_id] = {"client": nostr_client, "unsub": None}
    
    await nostr_client.connect()
    
    async def handle_state_change(event: Event) -> None:
        """Handle entity state changes."""
        entity_id = config_data.get(CONF_ENTITY_ID)
        if event.data.get("entity_id") == entity_id:
            await nostr_client.publish_state_change(event)
    
    # Store the unsubscribe function to clean up later
    unsub = hass.bus.async_listen(EVENT_STATE_CHANGED, handle_state_change)
    hass.data[DOMAIN][entry.entry_id]["unsub"] = unsub
    
    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    nostr_client = entry_data["client"]
    unsub = entry_data.get("unsub")
    
    await nostr_client.disconnect()
    
    # Unsubscribe from event listener
    if unsub:
        unsub()
    
    hass.data[DOMAIN].pop(entry.entry_id)
    
    return True