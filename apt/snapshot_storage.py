"""Stable, compact JSON snapshots at the existing public data URLs."""

import json
from pathlib import Path


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def trade_sort_key(row):
    # Keep the existing date/price priority; break ties independently of the
    # order in which concurrent API requests finish.
    return (
        row.get("date", ""),
        row.get("price_manwon", 0),
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    )


def write_snapshot(path, metadata, records_key, records):
    # One record per line makes small updates small diffs, while JSON.parse
    # still receives exactly the same object schema and values.
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write("{\n")
            for key, value in metadata.items():
                stream.write(compact(key) + ":" + compact(value) + ",\n")
            stream.write(compact(records_key) + ":[\n")
            for index, record in enumerate(records):
                if index:
                    stream.write(",\n")
                stream.write(compact(record))
            stream.write("\n]}\n")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
