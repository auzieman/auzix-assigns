# Foo/bar SQLite RAM demonstration

From the assigns project:

```sh
python3 examples/sqlite/demo.py
```

Requires Python's sqlite3 module and an active `/RAM:` mount. Defaults: 30,000
records, three alternating RAM/disk rounds. Maximum accepted workload is 100,000
records and five rounds. Creates a uniquely named RAM sample, preserving earlier
samples, plus `build/sqlite-benchmark/latest.json`. Temporary benchmark databases
are removed automatically; the GUI sample remains until explicitly removed or
RAM is unmounted/rebooted. GUI installation is separate (`sqlitebrowser`).

Open the printed `foo-bar.sqlite` path in SQLite Browser. Browse **foo**, **bar**
and **category_totals**, or execute the SQL in the neighboring `try-these.sql`:

```sql
SELECT * FROM category_totals;
SELECT foo.name, bar.* FROM bar
JOIN foo ON foo.id=bar.foo_id WHERE foo.id=42 LIMIT 20;
```

Save/export to persistent storage if you want to retain edits. Sample databases
contain generated data only. They are approximately 4.2 MiB at default size.

## Benchmark meaning

Both locations use SQLite DELETE journal mode and synchronous=FULL. Each round
measures one bulk-insert transaction, index construction, 200 indexed aggregate
queries, and 100 separate update/commit transactions. Integrity, foreign keys,
row count and cross-run query checksums are checked outside timed sections.
Workload generation is included in insertion timing. Caches are not flushed;
this is a small application demonstration, not a raw-device or cold-cache test.
RAM's FULL sync cannot provide power-loss/reboot persistence like disk storage.

2026-10-22 medians (seconds), three rounds, 30,000 rows:

| Work | RAM | Disk |
| --- | ---: | ---: |
| Bulk insert | 0.140 | 0.169 |
| Create index | 0.020 | 0.032 |
| Queries | 0.041 | 0.033 |
| 100 individual commits | 0.011 | 0.765 |

These results show reduced commit overhead, not universally faster queries.
The receipt includes exact SQLite version, per-run values and checksum.
