import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
SPEC=importlib.util.spec_from_file_location("validate_facegen",ROOT/"validate_facegen.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def manifest(root,**npc):
    row={"form_key":"0012C4:Fixture.esp"}
    row.update(npc)
    return {
        "schema_version":"skyrim-facegen-manifest-v1",
        "asset_root":str(root),
        "npcs":[row],
    }

def write_pair(root,form_key="0012C4:Fixture.esp",nif=b"nif",dds=b"dds"):
    nr,dr=MOD.expected_relatives(form_key)
    np=root/nr
    dp=root/dr
    np.parent.mkdir(parents=True,exist_ok=True)
    dp.parent.mkdir(parents=True,exist_ok=True)
    np.write_bytes(nif)
    dp.write_bytes(dds)
    return np,dp

class FaceGenValidatorTests(unittest.TestCase):
    def test_expected_paths_use_defining_plugin_and_zero_prefixed_local_form_id(self):
        nif,dds=MOD.expected_relatives("920B27:ECTV Merged.esp")
        self.assertEqual(
            nif.as_posix(),
            "meshes/actors/character/FaceGenData/FaceGeom/ECTV Merged.esp/00920B27.nif",
        )
        self.assertEqual(
            dds.as_posix(),
            "textures/actors/character/FaceGenData/FaceTint/ECTV Merged.esp/00920B27.dds",
        )

    def test_complete_pair_passes_with_case_insensitive_path_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            nif=root/"Meshes/Actors/Character/FaceGenData/FaceGeom/FIXTURE.ESP/000012C4.NIF"
            dds=root/"Textures/Actors/Character/FaceGenData/FaceTint/fixture.esp/000012c4.dds"
            nif.parent.mkdir(parents=True)
            dds.parent.mkdir(parents=True)
            nif.write_bytes(b"nif")
            dds.write_bytes(b"dds")
            result=MOD.analyze(manifest(root))
        self.assertEqual(result["status"],"pass")
        self.assertEqual(result["coverage"]["present_pairs"],1)

    def test_missing_half_of_pair_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            nr,_=MOD.expected_relatives("0012C4:Fixture.esp")
            path=root/nr
            path.parent.mkdir(parents=True)
            path.write_bytes(b"nif")
            result=MOD.analyze(manifest(root))
        self.assertEqual(result["status"],"fail")
        self.assertTrue(any(x["rule_id"]=="FACEGEN-PAIR" for x in result["findings"]))

    def test_declared_fingerprint_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            write_pair(root,nif=b"actual")
            result=MOD.analyze(manifest(root,nif_sha256="0"*64))
        self.assertEqual(result["status"],"fail")
        self.assertTrue(any(x["rule_id"]=="FACEGEN-FINGERPRINT" for x in result["findings"]))

    def test_matching_fingerprints_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            nif,dds=write_pair(root,nif=b"nif-bytes",dds=b"dds-bytes")
            result=MOD.analyze(manifest(
                root,
                nif_sha256=hashlib.sha256(nif.read_bytes()).hexdigest(),
                dds_sha256=hashlib.sha256(dds.read_bytes()).hexdigest(),
            ))
        self.assertEqual(result["status"],"pass")
        self.assertEqual(result["coverage"]["fingerprints_checked"],2)

    def test_complete_origin_manifest_surfaces_orphans_as_needs_review(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            nif,_=write_pair(root)
            (nif.parent/"0000DEAD.nif").write_bytes(b"orphan")
            value=manifest(root)
            value["complete_for_origin_mods"]=True
            result=MOD.analyze(value)
        self.assertEqual(result["status"],"needs-review")
        self.assertTrue(any(x["rule_id"]=="FACEGEN-MANIFEST-COVERAGE" for x in result["findings"]))

    def test_report_conforms_to_shared_static_invariant_schema(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            write_pair(root)
            result=MOD.analyze(manifest(root))
        schema=json.loads(
            (REPO/"schemas"/"skyrim-static-invariant-report-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(result)),[])

if __name__=="__main__":
    unittest.main()
