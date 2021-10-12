# Updater for Home Assistant

[![Donate](https://img.shields.io/badge/donate-Coffee-yellow.svg)](https://www.buymeacoffee.com/AlexxIT)
[![Donate](https://img.shields.io/badge/donate-Yandex-red.svg)](https://money.yandex.ru/to/41001428278477)

This is a lightweight script for updating custom components for [Home Assistant](https://www.home-assistant.io/). If for some reason you do not want to use [HACS](https://hacs.xyz/) or cannot install it.

Pros:

- Instant ready to use, no need to install or Hass reboot
- No need GitHub account and token
- Support update to latest release or latest defaul branch, even if it's not a "master"
- Support update to specific branch or tag (version), even if the tag is not a release

Cons:

- There is no GUI
- Frontend integrations are not supported

## Setup

1. Add to your `configuration.yaml`:

```yaml
switch:
  - platform: command_line
    switches:
      updater:
        friendly_name: Updater
        command_on: python updater.py update  # run updates process
        command_off: python updater.py        # force reload witout timeout
        command_state: |
          python -B -c "exec('''try: import updater\nexcept ModuleNotFoundError: from urllib.request import urlretrieve; urlretrieve('https://raw.github.com/AlexxIT/Updater/master/updater.py', 'updater.py'); import updater'''); updater.run(interval=3600)"
        command_timeout: 60  # this is timeout, not update interval!
```

2. Go to Configuration > Server Controls > Reload: Command line entities

3. Wait 30 seconds (default delay from the moment the switch is added)

4. Edit file `updater.txt` in your config folder:

By default, updates to the latest release version or default branch. But you can point to any branch or any tag (version), even if the tag is not a release. Remember, some developers use the letter `v` in version name, some don't.

```
https://github.com/AlexxIT/SonoffLAN             # latest release or default branch
https://github.com/AlexxIT/Dataplicity mater     # master branch
https://github.com/AlexxIT/XiaomiGateway3 async  # custom branch
https://github.com/AlexxIT/WebRTC v2.0.1         # custom tag (version)
# https://github.com/hacs/integration            # any comments
```

## Using

You should wait 30 seconds after Home Assistant starts for first update check.

If switch is ON - all componenst is up-to-date. You can turn it OFF to force an update check.

If switch OFF - you have an update. Turn it ON for the update.

You can delete `custom_components/NAME/version.txt` to force update on same version.

You can delete `updater.py` to update this script when the new version comes out.

You can delete `updater.json` to force an update check. The command line switch updates the data once an hour and caches the response in this file. To minimize the number of requests to the Internet.

You can comment line in `updater.txt` file to disable component update.

You can use script from command line:

```shell
python updater.py update AlexxIT/SonoffLAN AlexxIT/Dataplicity@mater AlexxIT/WebRTC@v2.0.1
python updater.py -i 3600 json AlexxIT/SonoffLAN
```

Also, you can create sensor if you want. The sensor value can be updated with a delay up to 60 seconds.

```yaml
sensor:
  - platform: command_line
    name: Updater
    command: python updater.py -i 3600 json
    value_template: '{{ value_json.repositories|length }}'
    unit_of_measurement: updates
    json_attributes:
      - repositories
```

PS: working directory should point to the Hass configuration folder. This works by default for most users.
