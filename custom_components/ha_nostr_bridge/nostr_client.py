"""Nostr client for Home Assistant integration."""
import asyncio
import json
import logging
from typing import Any, Dict

from nostr_sdk import Client, Keys, EventBuilder, Kind, Timestamp, NostrSigner, RelayUrl, Tag, TagKind

from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.json import JSONEncoder

from .const import (
    CONF_ENTITY_ID,
    CONF_RELAY_URL,
    CONF_PRIVATE_KEY,
    CONF_EVENT_KIND,
    DEFAULT_RELAY_URL,
    DEFAULT_EVENT_KIND,
)

_LOGGER = logging.getLogger(__name__)


class NostrClient:
    """Nostr client for publishing events to relays."""

    def __init__(self, hass: HomeAssistant, config: Dict[str, Any]) -> None:
        """Initialize the Nostr client."""
        self.hass = hass
        self.config = config
        self.client = None
        self.keys = None
        self._setup_keys()

    def _setup_keys(self) -> None:
        """Setup cryptographic keys."""
        private_key_hex = self.config.get(CONF_PRIVATE_KEY)
        if private_key_hex:
            try:
                self.keys = Keys.parse(private_key_hex)
            except Exception as e:
                _LOGGER.error("Failed to parse private key: %s", e)
                self.keys = Keys.generate()
        else:
            self.keys = Keys.generate()
            _LOGGER.info("Generated new Nostr keypair. Public key: %s", self.keys.public_key().to_hex())

    async def connect(self) -> None:
        """Connect to the Nostr relay."""
        relay_url_str = self.config.get(CONF_RELAY_URL, DEFAULT_RELAY_URL)
        try:
            signer = NostrSigner.keys(self.keys)
            self.client = Client(signer)
            relay_url = RelayUrl.parse(relay_url_str)
            await self.client.add_relay(relay_url)
            await self.client.connect()
            _LOGGER.info("Connected to Nostr relay: %s", relay_url_str)
        except Exception as e:
            _LOGGER.error("Failed to connect to Nostr relay: %s", e)
            raise

    async def disconnect(self) -> None:
        """Disconnect from the Nostr relay."""
        if self.client:
            await self.client.disconnect()
            self.client = None
            _LOGGER.info("Disconnected from Nostr relay")

    async def publish_state_change(self, event: Event) -> None:
        """Publish a Home Assistant state change event to Nostr."""
        if not self.client:
            _LOGGER.error("No Nostr client connection available")
            return

        entity_id = event.data.get("entity_id")
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        
        if not new_state:
            return
        
        content_data = {
            "entity_id": entity_id,
            "state": new_state.state,
            "attributes": dict(new_state.attributes),
            "timestamp": new_state.last_updated.isoformat(),
            "domain": new_state.domain,
        }
        
        if old_state:
            content_data["previous_state"] = old_state.state
        
        content = json.dumps(content_data, cls=JSONEncoder)
        
        try:
            event_kind = self.config.get(CONF_EVENT_KIND, DEFAULT_EVENT_KIND)
            
            # Ensure event_kind is an integer
            if isinstance(event_kind, float):
                event_kind = int(event_kind)
            
            _LOGGER.debug("Publishing event with kind: %s, entity: %s, state: %s", 
                         event_kind, entity_id, new_state.state)
            
            # Create basic tags (ensure all values are strings)
            tags = [
                Tag.hashtag("home-assistant"),
                Tag.parse(["entity", str(entity_id)]),
                Tag.parse(["domain", str(new_state.domain)]),
                Tag.parse(["state", str(new_state.state)]),
            ]
            
            # For spontaneous addressable events (kind 36107), add a d tag for replaceability
            if int(event_kind) == 36107:
                # Create a stable d tag based on entity_id so events replace each other
                d_tag_value = f"ha-entity-{entity_id.replace('.', '-')}"
                tags.append(Tag.parse(["d", d_tag_value]))
            
            # Build the Nostr event with proper Kind and tags
            kind = Kind(int(event_kind))
            builder = EventBuilder(kind, content)
            
            # Add tags one by one (if supported by this version of the API)
            for tag in tags:
                try:
                    builder.add_tag(tag)
                except AttributeError:
                    # If add_tag doesn't exist, we'll build without custom tags
                    pass
            
            # Publish the event
            await self.client.send_event_builder(builder)
            _LOGGER.debug("Published state change for %s to Nostr", entity_id)
            
        except Exception as e:
            _LOGGER.error("Failed to publish state change to Nostr: %s. Event kind: %s, State: %s", 
                         e, self.config.get(CONF_EVENT_KIND, DEFAULT_EVENT_KIND), new_state.state)