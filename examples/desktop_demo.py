# SPDX-License-Identifier: GPL-3.0-only
"""Start/stop a bounded, disposable EFM trial. Run on the host, as a normal user."""
import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

project = Path(__file__).resolve().parents[1]
base = project/'build/desktop-demo'
view = base/'view'
state = base/'session.json'


def limits():
    resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
    os.nice(5)


def stop():
    if os.path.ismount(view):
        result = subprocess.run(['fusermount3','-u',str(view)],capture_output=True,text=True,timeout=10)
        if os.path.ismount(view): raise RuntimeError(result.stderr)
    # A normal unmount makes the FUSE process exit. Do not kill arbitrary stored PIDs.
    if state.exists():
        saved=json.loads(state.read_text())
        ram=Path(saved['ram'])
        # Only remove our known demo file, leaving any user additions untouched.
        if ram.parent == Path('/dev/shm') and ram.name.startswith('auzix-assigns-demo-'):
            (ram/'About RAM.txt').unlink(missing_ok=True)
            try: ram.rmdir()
            except OSError: pass
        state.unlink()
    print('Demo detached. Fixture folders remain at', base)


def start():
    base.mkdir(parents=True,exist_ok=True)
    view.mkdir(exist_ok=True)
    if state.exists() or os.path.ismount(view): raise RuntimeError('Existing session; run stop first')
    for name in ('local/Albums','external/Albums','programs'):
        (base/name).mkdir(parents=True,exist_ok=True)
    for name,text in {'local/Albums/local.txt':'One source: local collection.\n',
                      'external/Albums/external.txt':'Another source: external collection.\n',
                      'local/duplicate.txt':'This local copy wins.\n',
                      'external/duplicate.txt':'This copy is visible in inspect.\n',
                      'programs/About Programs.txt':'Programs will contain desktop launchers. This trial uses harmless text fixtures.\n'}.items():
        p=base/name
        if not p.exists():p.write_text(text)
    ram=Path(tempfile.mkdtemp(prefix='auzix-assigns-demo-',dir='/dev/shm'))
    (ram/'About RAM.txt').write_text('This source file lives in existing tmpfs (/dev/shm).\nThe Assigns view is still read-only. No dedicated RAM disk was mounted.\n')
    config=base/'assigns.json'
    config.write_text(json.dumps({'version':1,'assigns':{
        'Music':{'sources':[str(base/'local'),str(base/'external')]},
        'Programs':{'sources':[str(base/'programs')]},
        'RAM':{'sources':[str(ram)]}}},indent=2)+'\n')
    with (base/'mount.log').open('w') as log:
        process=subprocess.Popen([sys.executable,'-m','assignfs','-c',str(config),'mount',str(view)],cwd=project,
            stdout=log,stderr=log,stdin=subprocess.DEVNULL,start_new_session=True,preexec_fn=limits)
    state.write_text(json.dumps({'pid':process.pid,'ram':str(ram),'mount':str(view)},indent=2)+'\n')
    for _ in range(100):
        if os.path.ismount(view):break
        if process.poll() is not None:
            stop();raise RuntimeError((base/'mount.log').read_text())
        time.sleep(.05)
    if not os.path.ismount(view):
        process.terminate();process.wait(timeout=5);stop();raise RuntimeError('Mount timeout')
    print('Mounted:',view,'PID:',process.pid)
    print('Stop: python3 examples/desktop_demo.py stop')
    subprocess.run(['enlightenment_remote','-efm-open-dir',str(view)],check=True,timeout=15)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['start','stop','status'])
    args=parser.parse_args()
    if args.action=='start':start()
    elif args.action=='stop':stop()
    else:
        print('Mounted:',os.path.ismount(view))
        if state.exists():print(state.read_text())
