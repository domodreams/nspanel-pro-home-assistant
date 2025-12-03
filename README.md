# NSPanel Pro Integration for Home Assistant by DomoDreams

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/domodreams/nspanel-pro-home-assistant.svg)](https://github.com/domodreams/nspanel-pro-home-assistant/releases)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=domodreams&repository=nspanel-pro-home-assistant&category=integration)

A Home Assistant integration for NSPanel Pro devices with MQTT-based communication and a built-in configuration card.

## Features

- 🔌 **MQTT Bridge**: Seamlessly control Home Assistant entities from your NSPanel Pro
- 💡 **Light Control**: On/Off and brightness control
- 🪟 **Cover Control**: Open/Close/Stop and position control
- 🌡️ **Climate Control**: HVAC mode, preset, and temperature control
- 🎨 **Configuration Card**: Built-in Lovelace card for easy entity selection
- ⚡ **Zero Configuration**: Works out of the box with MQTT

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add `https://github.com/domodreams/nspanelpro_integration` with category "Integration"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/nspanelpro` folder to your `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "NSPanel Pro"
4. Enter your Panel ID and Name
5. Click Submit

## MQTT Topics

Base topic: `domodreams/nspanelpro/`

### Command Topics (Panel → Home Assistant)

| Entity Type | Topic | Payload |
|-------------|-------|---------|
| **Light On/Off** | `domodreams/nspanelpro/cmd/light/{entity}/set` | `ON` / `OFF` |
| **Light Brightness** | `domodreams/nspanelpro/cmd/light/{entity}/brightness` | `0-255` |
| **Cover Control** | `domodreams/nspanelpro/cmd/cover/{entity}/set` | `OPEN` / `CLOSE` / `STOP` |
| **Cover Position** | `domodreams/nspanelpro/cmd/cover/{entity}/position` | `0-100` |
| **Climate Mode** | `domodreams/nspanelpro/cmd/climate/{entity}/mode` | `off` / `heat` / `cool` / `auto` |
| **Climate Preset** | `domodreams/nspanelpro/cmd/climate/{entity}/preset` | `away` / `home` / `eco` |
| **Climate Temperature** | `domodreams/nspanelpro/cmd/climate/{entity}/temperature` | `18.5` |

### Configuration Topic

| Purpose | Topic | Payload |
|---------|-------|---------|
| **Panel Config** | `domodreams/nspanelpro/config/{panel_id}` | JSON config object |

## Configuration Card

The integration includes a built-in Lovelace card for configuring your panel.

### Adding the Card Resource

Add to your Lovelace resources:

```yaml
resources:
  - url: /nspanelpro/nspanelpro-config-card.js
    type: module
```

### Using the Card

```yaml
type: custom:nspanelpro-config-card
title: NSPanel Pro Configuration
panel_id: panel1
```

### Card Features

- View all available lights, covers, and climate entities
- Select entities to expose to your NSPanel Pro
- Publish configuration directly to the panel via MQTT
- Real-time entity state display

## Example MQTT Messages

### Turn on a light

```text
Topic: domodreams/nspanelpro/cmd/light/living_room/set
Payload: ON
```

### Set light brightness

```text
Topic: domodreams/nspanelpro/cmd/light/living_room/brightness
Payload: 128
```

### Set cover position

```text
Topic: domodreams/nspanelpro/cmd/cover/bedroom_blinds/position
Payload: 50
```

### Set thermostat temperature

```text
Topic: domodreams/nspanelpro/cmd/climate/living_room/temperature
Payload: 21.5
```

## Panel Configuration JSON

When you publish configuration from the card, it sends a JSON object:

```json
{
  "panel_id": "panel1",
  "entities": {
    "lights": ["light.living_room", "light.bedroom"],
    "covers": ["cover.blinds"],
    "climates": ["climate.thermostat"]
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## Debugging

Enable debug logging by adding to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.nspanelpro: debug
```

## Support

- [GitHub Issues](https://github.com/domodreams/nspanelpro_integration/issues)
- [Documentation](https://github.com/domodreams/nspanelpro_integration/wiki)

## License

MIT License - see [LICENSE](LICENSE) for details.
