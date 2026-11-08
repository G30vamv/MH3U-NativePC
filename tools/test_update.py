"""Checks that users on the previous release can update to a new one, with the previous release's own updater.py.

  local  before publishing: the old updater against a manifest built from the staged release folder
  real   after publishing:  the old updater against the published manifest (releases/latest/download)

Examples (run from anywhere; WORK is any scratch folder):
  python tools/test_update.py local WORK --old-zip MH3U_Port_Launcher_v0.9.6.zip --old-version v0.9.6 \
      --new-version v0.9.7 --staging release_prep/MH3U_Port_Launcher
  python tools/test_update.py real WORK --old-zip MH3U_Port_Launcher_v0.9.6.zip --old-version v0.9.6 \
      --new-zip dist-release/MH3U_Port_Launcher_v0.9.7.zip

The old updater is read from git (`git show <old-ref>:launcher/updater.py`; old-ref defaults to the old-version tag)
unless --old-updater is given.
Nothing is installed outside WORK.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def install_old(work, old_zip):
    inst = os.path.join(work, 'install')
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(inst)
    with zipfile.ZipFile(old_zip) as z:
        for n in z.namelist():
            if n.endswith('/'):
                continue
            t = os.path.join(inst, n.split('/', 1)[1])
            os.makedirs(os.path.dirname(t), exist_ok=True)
            with open(t, 'wb') as f:
                f.write(z.read(n))
    return inst


def load_old_updater(work, old_ref, old_updater):
    if old_updater:
        src = open(old_updater, 'rb').read()
    else:
        src = subprocess.run(['git', '-C', REPO, 'show', f'{old_ref}:launcher/updater.py'],
                             check=True, capture_output=True).stdout
    path = os.path.join(work, 'oldupd', 'updater.py')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(src)
    spec = importlib.util.spec_from_file_location('oldupdater', path)
    u = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(u)
    return u


def local_manifest(work, staging, new_version):
    files = []
    for dp, _, fs in os.walk(staging):
        for f in fs:
            p = os.path.join(dp, f)
            with open(p, 'rb') as fh:
                data = fh.read()
            files.append({'path': os.path.relpath(p, staging).replace(os.sep, '/'),
                          'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data),
                          'url': 'file:///' + p.replace(os.sep, '/')})
    path = os.path.join(work, 'manifest.json')
    with open(path, 'w') as f:
        json.dump({'version': new_version, 'notes': 'test', 'files': files}, f, indent=1)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['local', 'real'])
    ap.add_argument('work')
    ap.add_argument('--old-zip', required=True)
    ap.add_argument('--old-version', required=True, help='e.g. v0.9.6 (also the git tag with its updater.py)')
    ap.add_argument('--old-ref', help='git tag or commit holding the old updater.py (default: --old-version)')
    ap.add_argument('--old-updater', help='path to the old updater.py instead of git show')
    ap.add_argument('--new-version', help='local: version written in the test manifest')
    ap.add_argument('--staging', help='local: folder with the new release files (MH3U_Port_Launcher)')
    ap.add_argument('--new-zip', help='real: the published zip, to compare the downloaded files with')
    a = ap.parse_args()

    work = os.path.abspath(a.work)
    inst = install_old(work, a.old_zip)
    u = load_old_updater(work, a.old_ref or a.old_version, a.old_updater)
    if a.mode == 'local':
        if not (a.staging and a.new_version):
            ap.error('local needs --staging and --new-version')
        manifest = local_manifest(work, os.path.abspath(a.staging), a.new_version)
        os.environ['MH3U_UPDATE_MANIFEST'] = 'file:///' + manifest.replace(os.sep, '/')
    else:
        if not a.new_zip:
            ap.error('real needs --new-zip')
        os.environ.pop('MH3U_UPDATE_MANIFEST', None)

    man = u.fetch_manifest()
    print('manifest', man['version'], '| newer than', a.old_version + ':', u.is_newer(man, a.old_version),
          '| newer than itself:', u.is_newer(man, man['version']))
    rejected = [e['path'] for e in man['files'] if not u._safe_rel(e['path'])]
    print('paths rejected by the OLD updater:', rejected)
    todo = u.files_to_update(man, inst)
    print('to download:', sorted(t['rel'] for t in todo))
    u.download_files(todo, inst)
    print('downloaded; sha256 verified by the old updater')
    bad = len(rejected)
    if a.mode == 'real':
        with zipfile.ZipFile(a.new_zip) as zz:
            differ = 0
            for e in todo:
                with open(os.path.join(inst, '_update', e['rel']), 'rb') as f:
                    got = hashlib.sha256(f.read()).hexdigest()
                differ += got != hashlib.sha256(zz.read('MH3U_Port_Launcher/' + e['rel'].replace(os.sep, '/'))).hexdigest()
        print('files that differ from the published zip:', differ)
        bad += differ
    print('RESULT:', 'OK' if not bad else 'PROBLEMS')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
