import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import free_catalog  # noqa: E402

FIX = Path(__file__).parent / "fixtures"


def fixture(name):
    return json.loads((FIX / f"openrouter-models-{name}.json").read_text(encoding="utf-8"))


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeOpener:
    def __init__(self, payload=None, error=None):
        self.payload, self.error, self.calls = payload, error, 0

    def __call__(self, request, timeout=None):
        self.calls += 1
        if self.error:
            raise self.error
        return FakeResponse(json.dumps(self.payload).encode())


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


class FreeCatalogTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name)

    def test_free_detection_excludes_paid(self):
        models = free_catalog.normalize_openrouter(fixture("v1"))
        self.assertEqual(len(models), 2)
        self.assertTrue(all(m["slug"].endswith(":free") for m in models))
        self.assertTrue(free_catalog.is_free({"prompt": "0", "completion": "0.0"}))
        self.assertFalse(free_catalog.is_free({"prompt": "0", "completion": "0.1"}))
        self.assertFalse(free_catalog.is_free({"prompt": "0", "completion": "0", "image": "0.01"}))
        self.assertFalse(free_catalog.is_free({}))
        self.assertFalse(free_catalog.is_free(None))
        payload = {"data": [
            {"id": "x/zero", "pricing": {"prompt": "0", "completion": "0"}},
            {"id": "x/y:free"},
            {"id": "x/paid", "pricing": {"prompt": "1", "completion": "1"}},
        ]}
        self.assertEqual([m["slug"] for m in free_catalog.normalize_openrouter(payload)], ["x/y:free", "x/zero"])
        flags = {(m["supports_tools"], m["supports_structured_output"]) for m in models}
        self.assertEqual(flags, {(True, False), (False, True)})

    def test_cache_hit_and_ttl_refresh(self):
        opener, clock = FakeOpener(fixture("v1")), Clock()
        first = free_catalog.discover(home=self.home, opener=opener, now=clock)
        self.assertEqual(first["source"], "live")
        self.assertEqual(first["schema_version"], free_catalog.SCHEMA_VERSION)
        second = free_catalog.discover(home=self.home, opener=opener, now=clock)
        self.assertEqual((second["source"], opener.calls), ("cache", 1))
        self.assertEqual(second["catalog_version"], first["catalog_version"])
        clock.t += free_catalog.CACHE_SECONDS + 1
        opener.payload = fixture("v2")
        third = free_catalog.discover(home=self.home, opener=opener, now=clock)
        self.assertEqual((third["source"], opener.calls), ("live", 2))
        self.assertNotEqual(third["catalog_version"], first["catalog_version"])
        forced = free_catalog.discover(refresh=True, home=self.home, opener=opener, now=clock)
        self.assertEqual((forced["source"], opener.calls), ("live", 3))
        self.assertEqual(forced["catalog_version"], third["catalog_version"])

    def test_first_seen_kept_last_seen_updated(self):
        clock = Clock()
        v1 = free_catalog.discover(home=self.home, opener=FakeOpener(fixture("v1")), now=clock)
        with mock.patch.object(free_catalog, "utc_now_iso", lambda: "2026-10-02T00:00:00Z"):
            v2 = free_catalog.discover(refresh=True, home=self.home, opener=FakeOpener(fixture("v2")), now=clock)
        old = {m["slug"]: m for m in v1["models"]}
        for m in v2["models"]:
            self.assertEqual(m["last_seen"], "2026-10-02T00:00:00Z")
            if m["slug"] in old:
                self.assertEqual(m["first_seen"], old[m["slug"]]["first_seen"])
            else:
                self.assertEqual(m["first_seen"], "2026-10-02T00:00:00Z")

    def test_diff(self):
        a = {"models": free_catalog.normalize_openrouter(fixture("v1"))}
        b = {"models": free_catalog.normalize_openrouter(fixture("v2"))}
        d = free_catalog.diff(a, b)
        self.assertEqual(len(d["added"]), 1)
        self.assertEqual(len(d["removed"]), 1)
        self.assertEqual(len(d["changed"]), 1)
        self.assertEqual(d["changed"][0]["fields"]["context_length"], [65536, 131072])
        self.assertEqual(free_catalog.diff(a, a), {"added": [], "removed": [], "changed": []})

    def test_network_error_is_data(self):
        out = free_catalog.discover(home=self.home, opener=FakeOpener(error=OSError("boom")), now=Clock())
        self.assertEqual(out["models"], [])
        self.assertIn("OSError", out["error"])
        free_catalog.discover(home=self.home, opener=FakeOpener(fixture("v1")), now=Clock())
        out = free_catalog.discover(refresh=True, home=self.home, opener=FakeOpener(error=OSError("down")), now=Clock())
        self.assertTrue(out["stale"])
        self.assertEqual(len(out["models"]), 2)
        self.assertIn("error", out)

    def test_cache_write_failure_is_data(self):
        with mock.patch("agent_os.storage.write_json", side_effect=OSError("disk full")):
            out = free_catalog.discover(home=self.home, opener=FakeOpener(fixture("v1")), now=Clock())
        self.assertEqual(out["source"], "live")
        self.assertEqual(len(out["models"]), 2)
        self.assertIn("OSError", out["cache_error"])

    def test_corrupt_fetched_epoch_forces_refresh(self):
        opener, clock = FakeOpener(fixture("v1")), Clock(1_800_000_000.0)
        free_catalog.discover(home=self.home, opener=opener, now=clock)
        cache = free_catalog._cache_path(self.home)
        data = json.loads(cache.read_text(encoding="utf-8"))
        data["fetched_epoch"] = "garbage"
        cache.write_text(json.dumps(data), encoding="utf-8")
        out = free_catalog.discover(home=self.home, opener=opener, now=clock)
        self.assertEqual((out["source"], opener.calls), ("live", 2))

    def test_no_model_literals_in_source(self):
        source = Path(free_catalog.__file__).read_text(encoding="utf-8")
        for name in ("v1", "v2"):
            for item in fixture(name)["data"]:
                self.assertNotIn(item["id"], source)
        self.assertIsNone(re.search(r"[\w-]+/[\w.-]+:free", source))


if __name__ == "__main__":
    unittest.main()
