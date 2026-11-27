import datetime as dt
import unittest

import weekly_agent as a

SLOTS = [{"id": 1, "time": "11:00", "message": "a"}, {"id": 2, "time": "16:00", "message": "b"}, {"id": 3, "time": "19:00", "message": "c"}]
D = dt.datetime


class PickDueTests(unittest.TestCase):
    def test_before_first(self):
        self.assertEqual(a.pick_due(D(2026, 11, 27, 10, 59), SLOTS, set()), (None, []))

    def test_exactly_first(self):
        slot, silent = a.pick_due(D(2026, 11, 27, 11, 0), SLOTS, set())
        self.assertEqual(slot["id"], 1)
        self.assertEqual(silent, [])

    def test_already_fired(self):
        self.assertEqual(a.pick_due(D(2026, 11, 27, 11, 30), SLOTS, {1}), (None, []))

    def test_late_start_shows_latest_and_silences_earlier(self):
        slot, silent = a.pick_due(D(2026, 11, 27, 16, 20), SLOTS, set())
        self.assertEqual(slot["id"], 2)
        self.assertEqual(silent, [1])

    def test_too_late_is_silenced(self):
        slot, silent = a.pick_due(D(2026, 11, 27, 23, 30), SLOTS, set())
        self.assertIsNone(slot)
        self.assertEqual(sorted(silent), [1, 2, 3])

    def test_three_per_day(self):
        fired, shown = set(), []
        for hh, mm in [(11, 0), (11, 20), (16, 0), (16, 5), (19, 0), (19, 30)]:
            slot, silent = a.pick_due(D(2026, 11, 27, hh, mm), SLOTS, fired)
            fired |= set(silent)
            if slot:
                shown.append(slot["id"])
                fired.add(slot["id"])
        self.assertEqual(shown, [1, 2, 3])


class ServerUrlTests(unittest.TestCase):
    def test_normalize(self):
        n = a.normalize_server
        self.assertEqual(n("192.168.0.52"), "http://192.168.0.52:8000")
        self.assertEqual(n("http://192.168.0.52"), "http://192.168.0.52:8000")
        self.assertEqual(n("http://192.168.0.52:8000/"), "http://192.168.0.52:8000")
        self.assertEqual(n("  192.168.0.52:9000 "), "http://192.168.0.52:9000")
        self.assertEqual(n(""), "")


if __name__ == "__main__":
    unittest.main()
