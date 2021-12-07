"""
https://github.com/AlexxIT/Updater
python updater.py update - run updates process
python updater.py json - output outdated repositories list in JSON format
python updated.py - check updated once an hour, exit with 0 if no updates
"""
import io
import json
import re
import time
import traceback
import zipfile
from pathlib import Path

from requests import Session

__version__ = 'v1.1.1'


def run(command: str = 'code', interval: int = 0, repos: list = None):
    """
    :param command:
        - update - update components to latest versions
        - json - prints json with new components versions
        - code - return count of updates as app result code
    :param interval: returns the cache if it is not older than the interval in
        seconds. interval<0 disables cache (updater.json) file creation.
    :param repos: list of repositories for updates in "username/repo" or
        "username/repo tree" formats. If empty, the list will be parsed from
        the (updater.txt) file.
    """
    script = Path(__file__)
    cwd = script.parent

    # check script is in config folder
    if not (cwd / 'configuration.yaml').exists():
        return

    # cache file to prevent refresh versions every minute
    cache = cwd / script.name.replace('.py', '.json')

    # if interval - check cache file time
    if interval and cache.exists() and \
            time.time() < cache.stat().st_mtime + interval:
        if command == 'json':
            print(cache.read_text())
        elif command == 'code':
            raw = json.loads(cache.read_text())
            exit(len(raw['repositories']))  # 0 - no updates
        return

    session = Session()
    repositories = []

    if not repos:
        # support custom scriptname
        config = cwd / script.name.replace('.py', '.txt')
        if not config.exists():
            # create empty file and exit if first run
            config.write_text('')
            return

        # read file with urls
        raw = config.read_text()
    else:
        raw = '\n'.join(repos) if isinstance(repos, list) else repos

    repos = re.findall(
        r"^(?:https://github.com/)?([\w-]+/[\w-]+)(?:[ @]+([\w.-]+))?",
        raw, flags=re.MULTILINE
    )

    # name: AlexxIT/SonoffLAN, tree: branch or tag name
    for name, tree in repos:
        try:
            url = "https://github.com/" + name

            if not tree:
                # if not tree - get latest release version from redirect
                r = session.get(url + "/releases/latest",
                                allow_redirects=False)
                _, tree = r.headers.get("location").rsplit("/", 1)

            # will return `releases` if no releases in repo, so loads root
            # branches and tags has same link to page
            r = session.get(
                url if tree == 'releases' else f"{url}/tree/{tree}"
            )

            # check if tree is branch or tag
            m = re.search(r'id="branch-select-menu">.+?</summary>', r.text,
                          flags=re.DOTALL)[0]
            if 'octicon-git-branch' in m:
                if tree == 'releases':
                    # get tree name, because we in repo root
                    tree = re.search(r'data-menu-button>([^<]+)</span>', m)[1]

                zip_url = f"{url}/archive/refs/heads/{tree}.zip"
                # get ver from commit hash
                new_ver = re.search('/tree/([a-f0-9]{7})', r.text)[1]

            elif 'octicon-tag' in m and tree != 'releases':
                zip_url = f"{url}/archive/refs/tags/{tree}.zip"
                # use ver from tag name
                new_ver = tree

            else:
                raise RuntimeError

            # get custom component folder from repo listing
            m = re.search(r'href=".+?/custom_components/(\w+)"', r.text)
            if m:
                # files in custom_components folder
                domain = m[1]
                zip_root = cwd

            elif f"/{name}/blob/{tree}/manifest.json" in r.text:
                # files in root folder
                r = session.get(
                    f"https://raw.github.com/{name}/{tree}/manifest.json"
                )
                domain = r.json()['domain']
                zip_root = cwd / 'custom_components' / domain

            else:
                # try to check custom_components folder
                r = session.get(f"{url}/tree/{tree}/custom_components")
                if not r.ok:
                    continue
                m = re.findall(
                    rf'href="/{name}/tree/{tree}/custom_components/([^"]+)"',
                    r.text
                )
                # if only one folder in custom_components folder
                if len(m) != 1:
                    continue
                domain = m[0]
                zip_root = cwd

            # check installed version
            ver_path = cwd / 'custom_components' / domain / 'version.txt'
            cur_ver = ver_path.read_text() if ver_path.exists() else '-'
            if cur_ver == new_ver:
                # print(folder, "up to date")
                continue

            if command == 'update':
                r = session.get(zip_url)
                raw = io.BytesIO(r.content)
                zf = zipfile.ZipFile(raw)
                for file in zf.filelist:
                    # remove archive name from path
                    _, zip_path = file.filename.split('/', 1)
                    zip_path = zip_root / zip_path

                    # skip files and folders not in custom_components folder
                    if 'custom_components' not in zip_path.parts:
                        continue

                    # support create custom_components folder if it not exists
                    if file.is_dir():
                        zip_path.mkdir(exist_ok=True)
                    # skip files not in custom_components/domain folder
                    elif domain in zip_path.parts:
                        raw = zf.read(file)
                        zip_path.write_bytes(raw)

                ver_path.write_text(new_ver)

                print(domain, "updated to", tree)

            else:
                repositories.append({
                    'name': name,
                    'installed_version': cur_ver,
                    'available_version': new_ver,
                })

        except:
            traceback.print_exc()

    raw = json.dumps({'repositories': repositories})
    if interval >= 0:
        cache.write_text(raw)
    if command == 'json':
        print(raw)
    elif command == 'code':
        exit(len(repositories))  # 0 - no updates


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='version', version=__version__)
    parser.add_argument('command', nargs='?', default='code',
                        choices=('code', 'json', 'update'))
    parser.add_argument('-i', '--interval', type=int, default=0, metavar='0',
                        help="cache interval")
    parser.add_argument('repos', nargs='*', help="format: user/repo tree")
    args = parser.parse_args()

    run(**args.__dict__)
