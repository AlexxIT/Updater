"""
https://github.com/AlexxIT/Updater
python updater.py update - run updates process
python updater.py json - output outdated repositories list in JSON format
python updated.py - check updated once an hour, exit with 0 if no updates
"""
import io
import json
import re
import sys
import time
import traceback
import zipfile
from pathlib import Path

from requests import Session

__version__ = 'v1.0.0'

script = Path(__file__)
cwd = script.parent

# check we in config folder
if not (cwd / 'configuration.yaml').exists():
    exit(0)

# support custom scriptname
config = cwd / script.name.replace('.py', '.txt')
if not config.exists():
    config.write_text('')
    exit(0)

cache = cwd / script.name.replace('.py', '.json')

command = sys.argv[1] if len(sys.argv) == 2 else None
if command is None:
    interval = globals().get('interval', 60 * 60)
    if cache.exists() and time.time() < cache.stat().st_mtime + interval:
        raw = json.loads(cache.read_bytes())
        exit(len(raw['repositories']))  # 0 - no updates

session = Session()
repositories = []

raw = config.read_text()
for name, new_ver in re.findall(
        r"https://github.com/([\w-]+/[\w-]+)(?: +([\w.-]+))?", raw
):
    try:
        url = "https://github.com/" + name

        if not new_ver:
            # load version
            r = session.get(url + "/releases/latest", allow_redirects=False)
            # ver will return `releases` in no releases in repo
            _, new_ver = r.headers.get("location").rsplit("/", 1)

        if new_ver in ('releases', 'master'):
            zip_url = f"{url}/archive/refs/heads/master.zip"
            r = session.get(url + "/tree/master")
            # get ver from commit hash
            new_ver = re.search('/tree/([a-f0-9]{7})', r.text)[1]
        else:
            zip_url = f"{url}/archive/refs/tags/{new_ver}.zip"
            r = session.get(f"{url}/tree/{new_ver}")

        folder = re.search(r'href=".+/custom_components/(\w+)"', r.text)[1]

        # check installed version
        ver_path = cwd / 'custom_components' / folder / 'version.txt'
        cur_ver = ver_path.read_text() if ver_path.exists() else '-'
        if cur_ver == new_ver:
            # print(folder, "up to date")
            continue

        if command == 'update':
            r = session.get(zip_url)
            raw = io.BytesIO(r.content)
            zf = zipfile.ZipFile(raw)
            for file in zf.filelist:
                if 'custom_components' not in file.filename:
                    continue

                # remove archive name from path
                _, zip_path = file.filename.split('/', 1)
                zip_path = cwd / zip_path

                if file.is_dir():
                    zip_path.mkdir(exist_ok=True)
                else:
                    raw = zf.read(file)
                    zip_path.write_bytes(raw)

            ver_path.write_text(new_ver)

            print(folder, "updated to", new_ver)

        else:
            repositories.append({
                'name': name,
                'installed_version': cur_ver,
                'available_version': new_ver,
            })

    except:
        traceback.print_exc()

raw = json.dumps({'repositories': repositories})
cache.write_text(raw)

if command == 'json':
    print(raw)
elif command is None:
    exit(len(repositories))  # 0 - no updates
