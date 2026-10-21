# SPDX-License-Identifier: GPL-3.0-only
"""Bounded read-only trial of real workstation mappings; no RAM or autostart."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from desktop_demo import limits

project = Path(__file__).resolve().parents[1]
base = project/'build/workstation-trial'
view = base/'view'
config = project/'configs/alpine-workstation.json'
trial_config = base/'assigns.json'
if trial_config.exists(): config = trial_config
state = base/'session.json'


def stop():
    if os.path.ismount(view):
        result = subprocess.run(['fusermount3','-u',str(view)],capture_output=True,text=True,timeout=10)
        if os.path.ismount(view):
            raise RuntimeError(result.stderr)
    state.unlink(missing_ok=True)
    print('Workstation view detached; original files unchanged.')


def verify():
    sys.path.insert(0,str(project))
    from assignfs.core import Registry
    registry = Registry.load(config)
    assert os.path.ismount(view), 'Not mounted'
    rows=[]
    for name in registry.sources:
        expected = registry.listing((name,))
        actual = sorted(os.listdir(view/name))
        assert actual == expected, name
        rows.append({'assign':name,'entries':len(actual)})
    source=Path('/usr/share/applications/e-control.desktop')
    assert hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256((view/'Programs/e-control.desktop').read_bytes()).digest()
    assert os.statvfs(view).f_flag & os.ST_RDONLY, 'Mount is not read-only'
    result={'listings':rows,'sample':'Programs/e-control.desktop matches installed source','read_only':True}
    (base/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


def start():
    base.mkdir(parents=True,exist_ok=True)
    view.mkdir(exist_ok=True)
    if state.exists() or os.path.ismount(view):
        raise RuntimeError('Existing trial; use status or stop first')
    subprocess.run([sys.executable,'-m','assignfs','-c',str(config),'check'],cwd=project,check=True)
    with (base/'mount.log').open('w') as log:
        process=subprocess.Popen([sys.executable,'-m','assignfs','-c',str(config),'mount',str(view)],cwd=project,
            stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,preexec_fn=limits)
    state.write_text(json.dumps({'pid':process.pid,'mount':str(view),'config':str(config)},indent=2)+'\n')
    try:
        for _ in range(100):
            if os.path.ismount(view):break
            if process.poll() is not None:raise RuntimeError((base/'mount.log').read_text())
            time.sleep(.05)
        if not os.path.ismount(view):raise RuntimeError('Mount timeout')
        subprocess.run([sys.executable,__file__,'verify'],check=True,timeout=90)
    except BaseException:
        stop()
        if process.poll() is None:process.terminate();process.wait(timeout=5)
        raise
    print('Real workstation view:',view)
    subprocess.run(['enlightenment_remote','-efm-open-dir',str(view)],check=True,timeout=15)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['start','stop','status','verify'])
    args=parser.parse_args()
    if args.action=='start':start()
    elif args.action=='stop':stop()
    elif args.action=='verify':verify()
    else:
        print('Mounted:',os.path.ismount(view))
        if state.exists():print(state.read_text())
