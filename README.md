# Updater for Home Assistant

[![Donate](https://img.shields.io/badge/donate-Coffee-yellow.svg)](https://www.buymeacoffee.com/AlexxIT)
[![Donate](https://img.shields.io/badge/donate-Yandex-red.svg)](https://money.yandex.ru/to/41001428278477)

This is a lightweight script for updating custom components for [Home Assistant](https://www.home-assistant.io/). If for some reason you do not want to use [HACS](https://hacs.xyz/) or cannot install it.

Only custom components with a `custom_components` folder in the root of the repository are supported. Frontend integrations are not supported.

## Setup

1. Add to your `configuration.yaml`:

```yaml
switch:
  - platform: command_line
    switches:
      updater:
        friendly_name: Updater
        command_on: python updater.py update  # run updates process
        command_off: python updater.py json  # force reload witout timeout
        command_state: |
          python -B -c "exec('''try: import updater\nexcept ModuleNotFoundError: from urllib.request import urlretrieve; urlretrieve('https://raw.github.com/AlexxIT/Updater/master/updater.py', 'updater.py'); import updater''')"
        command_timeout: 60  # this is timeout, not update interval!
```

2. Go to Configuration > Server Controls > Reload: Command line entities

3. Wait 30 seconds (default delay from the moment the switch is added)

4. Edit file `updater.txt` in your config folder:

By default updates to latest release version. But you can point to the master version. Or point to specific version. Remember, some developers use the letter `v` in version name, some don't.

```
https://github.com/AlexxIT/SonoffLAN
https://github.com/AlexxIT/XiaomiGateway3 master
https://github.com/AlexxIT/WebRTC v2.0.1
```

## Using

You should wait 30 seconds after Home Assistant starts for first update check.

If switch is ON - all componenst is up to date. You can turn it OFF to force an update check.

If switch OFF - you have an update. Turn it ON for the update.

You can delete `custom_components/NAME/version.txt` to force update on same version.

You can delete `updater.py` to update this script when the new version comes out.

You can delete `updater.json` to force an update check. The command line switch updates the data once an hour and caches the response in this file. To minimize the number of requests to the Internet

Also you can create sensor if you want. The sensor value may not be synchronized with the switch!

```yaml
sensor:
  - platform: command_line
    name: Updater
    command: python updater.py json
    unit_of_measurement: updates
    scan_interval: 3600  # 1 hour
    value_template: '{{ value_json.repositories|length }}'
    json_attributes:
      - repositories
```

PS: working directory should point to the Hass configuration folder. This works by default for most users.
