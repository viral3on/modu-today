import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apt.snapshot_storage import trade_sort_key, write_snapshot


class SnapshotStorageTests(unittest.TestCase):
    def test_concurrent_completion_order_does_not_change_snapshot(self):
        rows = [
            {"date": "2026-09-15", "price_manwon": 50000, "apt": name,
             "region_code": code, "area": "84.9"}
            for name, code in [("가람", "11110"), ("나래", "11680"), ("가람", "11680")]
        ]
        rows += [{"date": "2026-09-14", "price_manwon": 90000, "apt": "어제"}]
        expected = sorted(rows, key=trade_sort_key, reverse=True)
        for seed in range(20):
            shuffled = rows[:]
            random.Random(seed).shuffle(shuffled)
            self.assertEqual(sorted(shuffled, key=trade_sort_key, reverse=True), expected)
        self.assertEqual(expected[-1]["date"], "2026-09-14")

    def test_round_trip_preserves_all_current_data(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            for filename, key in [("trades.json", "trades"), ("apartments.json", "apartments")]:
                original = json.loads((root / "apt/data" / filename).read_text(encoding="utf-8"))
                path = Path(directory) / filename
                metadata = {k: v for k, v in original.items() if k != key}
                write_snapshot(path, metadata, key, original[key])
                self.assertEqual(json.loads(path.read_text(encoding="utf-8")), original)
                self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_failed_serialization_keeps_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trades.json"
            path.write_text('{"trades":[]}', encoding="utf-8")
            with self.assertRaises(TypeError):
                write_snapshot(path, {}, "trades", [{"invalid": object()}])
            self.assertEqual(path.read_text(), '{"trades":[]}')
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_one_record_change_only_changes_one_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trades.json"
            rows = [{"apt": "가람", "price_manwon": i} for i in range(100)]
            write_snapshot(path, {"updated_at": "same-check-time"}, "trades", rows)
            before = path.read_text(encoding="utf-8").splitlines()
            rows[50]["price_manwon"] = 12345
            write_snapshot(path, {"updated_at": "same-check-time"}, "trades", rows)
            after = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(sum(a != b for a, b in zip(before, after)), 1)


if __name__ == "__main__":
    unittest.main()
