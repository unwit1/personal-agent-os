import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("doctor",ROOT/"doctor_toolchain.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

def lock(adapters=None, runtime=None, roots=None):
    return {
      "schema_version":"skyrim-toolchain-lock-v1",
      "project_id":"demo",
      "runtime":runtime or {},
      "adapters":adapters or [],
      "generated_output_roots":roots or []
    }

class DoctorTests(unittest.TestCase):
    def test_native_requires_runtime_pins(self):
        r=MOD.audit(lock(),manifest={"layers":["native"],"targets":["ae-1.7.x"]},check_files=False)
        self.assertEqual(r["status"],"fail")
        self.assertEqual(sum(x["code"]=="NATIVE_RUNTIME_UNPINNED" for x in r["issues"]),3)

    def test_explicit_adapter_must_be_locked(self):
        r=MOD.audit(lock(),manifest={"layers":["records"],"targets":["ae-1.7.x"],"automation":{"preferred_adapters":["xedit"]}},check_files=False)
        self.assertTrue(any(x["code"]=="EXPLICIT_ADAPTER_UNLOCKED" for x in r["issues"]))

    def test_quality_preferred_is_warning_not_blocker(self):
        r=MOD.audit(lock(),quality={"adapters":{"preferred":["xedit"],"supporting":[]}},check_files=False)
        self.assertEqual(r["status"],"warn")
        self.assertTrue(any(x["code"]=="PREFERRED_ADAPTER_UNLOCKED" for x in r["issues"]))

    def test_game_data_output_is_blocked(self):
        r=MOD.audit(lock(roots=["C:/Games/Skyrim Special Edition/Data"]),check_files=False)
        self.assertEqual(r["status"],"fail")
        self.assertTrue(any(x["code"]=="UNSAFE_OUTPUT_ROOT" for x in r["issues"]))

if __name__=="__main__":
    unittest.main()
