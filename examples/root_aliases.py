# SPDX-License-Identifier: GPL-3.0-only
"""Install/remove only this trial's root navigation links; never overwrite paths."""
import argparse
import os
from pathlib import Path
import subprocess

project = Path(__file__).resolve().parents[1]
view = project/'build/workstation-trial/view'
links = {Path('/'+name+':'): view/name for name in ('C','Programs','Libraries','Sys_Libraries','RAM')}
links[Path('/c:')] = view/'C'
links[Path('/RAM:')] = project/'build/ram-drive'


def matches(link, target):
    return link.is_symlink() and os.readlink(link) == str(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install','remove','status'])
    action = parser.parse_args().action
    if action == 'install':
        if not os.path.ismount(view):
            raise RuntimeError('Start the workstation assign mount first')
        if not os.path.ismount(project/'build/ram-drive'):
            raise RuntimeError('Start the dedicated RAM filesystem first')
        for link,target in links.items():
            if not target.is_dir(): raise RuntimeError('Missing assign: '+str(target))
            if os.path.lexists(link) and not matches(link,target):
                raise RuntimeError('Refusing existing path: '+str(link))
        for link,target in links.items():
            if not os.path.lexists(link):
                subprocess.run(['sudo','-n','ln','-s','--',str(target),str(link)],check=True)
    elif action == 'remove':
        for link,target in links.items():
            if matches(link,target):
                subprocess.run(['sudo','-n','unlink',str(link)],check=True)
    for link,target in links.items():
        print(str(link), '->', os.readlink(link) if link.is_symlink() else '(not our link)',
              'available' if matches(link,target) and link.is_dir() else 'unavailable')


if __name__ == '__main__':
    main()
