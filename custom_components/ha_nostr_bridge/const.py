"""Constants for the Home Assistant Nostr Bridge integration."""

DOMAIN = "ha_nostr_bridge"

CONF_ENTITY_ID = "entity_id"
CONF_RELAY_URL = "relay_url"
CONF_PRIVATE_KEY = "private_key"
CONF_EVENT_KIND = "event_kind"

DEFAULT_RELAY_URL = "wss://relay.nostriot.com"
DEFAULT_EVENT_KIND = 36107  # Spontaneous addressable event - replaceable for IoT device states

# Common Nostr event kinds:
# 1 = Text note (not replaceable)
# 36107 = Spontaneous addressable event (replaceable, good for IoT device states)