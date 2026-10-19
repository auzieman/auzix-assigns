# SPDX-License-Identifier: GPL-3.0-only
"""Create a reusable demo; never mounts or touches existing user collections."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1] / 'build/demo'
for name in ('local/Albums', 'external/Albums', 'view'):
    (root / name).mkdir(parents=True, exist_ok=True)
for name, text in {'local/Albums/local.txt':'From the local collection\n',
                   'external/Albums/external.txt':'From the external collection\n',
                   'local/readme.txt':'Local copy takes priority\n',
                   'external/readme.txt':'External copy remains available in inspect\n'}.items():
    path = root/name
    if not path.exists(): path.write_text(text)
config = root/'assigns.json'
config.write_text(json.dumps({'version':1,'assigns':{'Music':{'sources':[str(root/'local'),str(root/'external')]}}},indent=2)+'\n')
print('Demo ready. From the project directory:')
print('python3 -m assignfs -c build/demo/assigns.json inspect Music:readme.txt')
print('python3 -m assignfs -c build/demo/assigns.json mount build/demo/view')
