# Home Assistant Nostr Bridge

A custom Home Assistant integration that publishes entity state changes to Nostr relays as replaceable events.

## Overview

This integration monitors a specified Home Assistant entity and publishes state changes to a Nostr relay using spontaneous addressable events (kind 36107). Each entity gets a stable `d` tag, ensuring that new state changes replace previous events rather than creating duplicates.

## Features

- **Real-time State Publishing**: Automatically publishes entity state changes to Nostr
- **Replaceable Events**: Uses Nostr event kind 36107 with stable `d` tags for replaceability
- **Rich Metadata**: Includes entity domain, state, attributes, and timestamps
- **UI Configuration**: Easy setup through Home Assistant's integration UI
- **Configurable Options**: Modify settings without recreating the integration

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/ha_nostr_bridge` directory to your Home Assistant `config/custom_components/` directory:
   ```bash
   # Create directory if it doesn't exist
   mkdir -p /config/custom_components
   
   # Copy integration files
   cp -r ha_nostr_bridge /config/custom_components/
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Integrations** → **Add Integration**

4. Search for "Home Assistant Nostr Bridge" and click to add

### Method 2: Using SSH/SCP

```bash
# From your development machine
scp -r custom_components/ha_nostr_bridge root@homeassistant.local:/root/config/custom_components/

# Restart Home Assistant
ssh root@homeassistant.local "ha core restart"
```

## Configuration

### Initial Setup

1. **Entity ID**: Select the Home Assistant entity you want to monitor (e.g., `sensor.temperature`, `light.living_room`)

2. **Relay URL**: Nostr relay WebSocket URL (default: `wss://relay.nostriot.com`)

3. **Private Key**: Optional hex-encoded private key. Leave empty to auto-generate a new keypair

4. **Event Kind**: Fixed to 36107 (Spontaneous Addressable Event) for replaceable IoT state events

### Modifying Settings

To change configuration after initial setup:

1. Go to **Settings** → **Integrations**
2. Find "Home Assistant Nostr Bridge"
3. Click the **gear icon** to configure
4. Update settings and save

The integration will automatically reload with new settings.

## Nostr Event Format

Published events use this structure:

```json
{
  "kind": 36107,
  "content": "{\"entity_id\": \"sensor.temperature\", \"state\": \"23.5\", \"attributes\": {\"unit_of_measurement\": \"°C\", \"device_class\": \"temperature\"}, \"timestamp\": \"2025-11-19T10:30:00+00:00\", \"domain\": \"sensor\", \"previous_state\": \"23.2\"}",
  "tags": [
    ["t", "home-assistant"],
    ["entity", "sensor.temperature"], 
    ["domain", "sensor"],
    ["state", "23.5"],
    ["d", "ha-entity-sensor-temperature"]
  ]
}
```

### Tag Explanation

- `t`: Hashtag for categorization (`home-assistant`)
- `entity`: Full entity ID
- `domain`: Entity domain (sensor, light, switch, etc.)
- `state`: Current entity state
- `d`: Stable identifier for replaceability (format: `ha-entity-{entity_id}`)

## Requirements

- Home Assistant 2023.1+
- Python 3.11+
- Network access to Nostr relay

## Dependencies

The integration automatically installs:

- `nostr-sdk>=0.34.0`: Python bindings for the Rust Nostr SDK

### Manual Testing

Test the entity state changes:

```bash
# SSH into Home Assistant  
ssh root@homeassistant.local

# Check integration status
ha core logs | grep "nostr_bridge"

# Trigger state change and monitor logs
```