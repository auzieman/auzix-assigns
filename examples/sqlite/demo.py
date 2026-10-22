#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Create a browsable SQLite demo and benchmark disposable RAM/disk databases."""
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import statistics
import tempfile
import time

PROJECT = Path(__file__).resolve().parents[2]
SCHEMA = '''
CREATE TABLE foo(id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL);
CREATE TABLE bar(id INTEGER PRIMARY KEY, foo_id INTEGER NOT NULL REFERENCES foo(id),
 amount_cents INTEGER NOT NULL, note TEXT NOT NULL);
CREATE VIEW category_totals AS SELECT foo.category, count(*) AS records,
 round(sum(bar.amount_cents)/100.0,2) AS total FROM foo JOIN bar ON foo.id=bar.foo_id
 GROUP BY foo.category;
'''


def timed(fn):
    start = time.perf_counter()
    value = fn()
    return value, time.perf_counter() - start


def populate(path, rows):
    con = sqlite3.connect(path)
    try:
        con.execute('PRAGMA foreign_keys=ON')
        con.execute('PRAGMA journal_mode=DELETE')
        con.execute('PRAGMA synchronous=FULL')
        con.executescript(SCHEMA)
        def insert():
            with con:
                con.executemany('INSERT INTO foo VALUES(?,?,?)',
                    ((i, f'Item {i:04}', ('Music','Graphics','Tools','Documents')[i%4]) for i in range(1,201)))
                con.executemany('INSERT INTO bar VALUES(?,?,?,?)',
                    ((i, (i%200)+1, (i*37)%50000, f'Sample record {i}: '+'foo bar '*12) for i in range(1,rows+1)))
        _, load = timed(insert)
        def index():
            con.execute('CREATE INDEX bar_foo ON bar(foo_id)');con.commit()
        _, indexing = timed(index)
        def lookups():
            return sum(con.execute('SELECT sum(amount_cents) FROM bar WHERE foo_id=?',(i,)).fetchone()[0] or 0 for i in range(1,201))
        total, query = timed(lookups)
        def commits():
            for i in range(1,101):
                with con: con.execute('UPDATE bar SET amount_cents=amount_cents+1 WHERE id=?',(i,))
        _, updates = timed(commits)
        assert con.execute('SELECT count(*) FROM bar').fetchone()[0] == rows
        assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not con.execute('PRAGMA foreign_key_check').fetchall()
        return dict(load_seconds=load,index_seconds=indexing,query_seconds=query,
                    commits_100_seconds=updates,bytes=path.stat().st_size,query_checksum=total)
    finally:
        con.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rows',type=int,default=30000)
    parser.add_argument('--rounds',type=int,default=3)
    parser.add_argument('--ram',type=Path,default=Path('/RAM:'))
    parser.add_argument('--disk',type=Path,default=PROJECT/'build/sqlite-benchmark')
    args = parser.parse_args()
    if not 100 <= args.rows <= 100000 or not 1 <= args.rounds <= 5:
        parser.error('Use 100–100000 rows and 1–5 rounds')
    ram = args.ram.resolve()
    if not ram.is_mount(): parser.error('RAM target must be a mounted filesystem')
    if shutil.disk_usage(ram).free < 128*1024*1024: parser.error('Need 128 MiB free RAM-drive space')
    args.disk.mkdir(parents=True,exist_ok=True)
    demo_dir = Path(tempfile.mkdtemp(prefix='sqlite-demo-',dir=ram))
    demo = demo_dir/'foo-bar.sqlite'
    populate(demo,args.rows)
    (demo_dir/'try-these.sql').write_text('SELECT * FROM category_totals;\nSELECT foo.name, bar.* FROM bar JOIN foo ON foo.id=bar.foo_id WHERE foo.id=42 LIMIT 20;\n')
    results = {'sqlite':sqlite3.sqlite_version,'rows':args.rows,'rounds':args.rounds,
        'settings':{'journal_mode':'DELETE','synchronous':'FULL'},'demo':str(demo),'runs':{'ram':[],'disk':[]}}
    for round_id in range(args.rounds):
        for name in (('ram','disk') if round_id%2==0 else ('disk','ram')):
            parent = ram if name=='ram' else args.disk
            with tempfile.TemporaryDirectory(prefix='sqlite-bench-',dir=parent) as folder:
                result = populate(Path(folder)/'bench.sqlite',args.rows)
                results['runs'][name].append(result)
                print(name,round_id+1,json.dumps(result),flush=True)
    checksums = {r['query_checksum'] for runs in results['runs'].values() for r in runs}
    assert len(checksums)==1, 'Workloads produced different results'
    results['medians'] = {name:{key:statistics.median(r[key] for r in runs)
        for key in ('load_seconds','index_seconds','query_seconds','commits_100_seconds')}
        for name,runs in results['runs'].items()}
    receipt = args.disk/'latest.json'
    receipt.write_text(json.dumps(results,indent=2)+'\n')
    print('GUI database:',demo)
    print('Receipt:',receipt)
    print('Medians:',json.dumps(results['medians'],indent=2))


if __name__ == '__main__':
    main()
