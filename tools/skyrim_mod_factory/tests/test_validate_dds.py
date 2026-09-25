import importlib.util
import json
import struct
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
SPEC=importlib.util.spec_from_file_location("validate_dds",ROOT/"validate_dds.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def legacy_dds(*,width=4,height=4,mips=1,fourcc=b"DXT1",payload=None):
    data=bytearray(128)
    data[:4]=b"DDS "
    struct.pack_into("<I",data,4,124)
    struct.pack_into("<I",data,8,0x00001007)
    struct.pack_into("<I",data,12,height)
    struct.pack_into("<I",data,16,width)
    struct.pack_into("<I",data,28,mips)
    struct.pack_into("<I",data,76,32)
    struct.pack_into("<I",data,80,0x4)
    data[84:88]=fourcc
    struct.pack_into("<I",data,108,0x1000)
    if payload is None:
        block=8 if fourcc in {b"DXT1",b"BC4U",b"ATI1"} else 16
        payload=b"\0"*MOD.block_payload_size(width,height,mips,block)
    return bytes(data)+payload

def dx10_dds(*,width=4,height=4,mips=1,dxgi=98,array_size=1,dimension=3,misc=0,payload=None):
    data=bytearray(148)
    data[:128]=legacy_dds(width=width,height=height,mips=mips,fourcc=b"DX10",payload=b"")[:128]
    struct.pack_into("<IIIII",data,128,dxgi,dimension,misc,array_size,0)
    if payload is None:
        name=MOD.DXGI.get(dxgi)
        block=MOD.BLOCK_BYTES.get(name,16)
        surfaces=max(1,array_size)*(6 if misc & MOD.DX10_CUBE else 1)
        payload=b"\0"*MOD.block_payload_size(width,height,mips,block,surfaces)
    return bytes(data)+payload

class DDSValidatorTests(unittest.TestCase):
    def test_valid_dxt1_header_and_payload_pass(self):
        result=MOD.analyze_bytes(legacy_dds(),path="fixture.dds",game="sse")
        self.assertEqual(result["status"],"pass")
        self.assertEqual(result["scope"]["format"],"DXT1")
        self.assertTrue(result["coverage"]["payload_size_checked"])

    def test_truncated_block_payload_fails(self):
        result=MOD.analyze_bytes(
            legacy_dds(width=8,height=8,payload=b"\0"*7),
            path="truncated.dds",
        )
        self.assertEqual(result["status"],"fail")
        self.assertTrue(any(x["rule_id"]=="DDS-PAYLOAD" for x in result["findings"]))

    def test_full_mip_policy_is_explicit(self):
        result=MOD.analyze_bytes(
            legacy_dds(width=8,height=8,mips=1),
            require_full_mips=True,
        )
        self.assertEqual(result["status"],"fail")
        row=next(x for x in result["findings"] if x["rule_id"]=="DDS-MIP-CHAIN")
        self.assertEqual(row["evidence"]["expected"],4)

    def test_dx10_bc7_is_typed_and_rejected_for_le_policy(self):
        sse=MOD.analyze_bytes(dx10_dds(dxgi=98),game="sse")
        le=MOD.analyze_bytes(dx10_dds(dxgi=98),game="le")
        self.assertEqual(sse["status"],"pass")
        self.assertEqual(sse["scope"]["format"],"BC7_UNORM")
        self.assertEqual(le["status"],"fail")
        self.assertTrue(any(x["rule_id"]=="DDS-GAME-FORMAT" for x in le["findings"]))

    def test_dx10_cube_array_payload_accounts_for_six_faces_per_cube(self):
        data=dx10_dds(dxgi=98,array_size=2,misc=MOD.DX10_CUBE)
        result=MOD.analyze_bytes(data)
        self.assertEqual(result["status"],"pass")
        self.assertTrue(result["scope"]["is_cube"])
        self.assertEqual(result["coverage"]["minimum_expected_payload"],16*12)

    def test_dx10_zero_array_size_fails(self):
        result=MOD.analyze_bytes(dx10_dds(array_size=0,payload=b"\0"*16))
        self.assertEqual(result["status"],"fail")
        self.assertTrue(any("arraySize" in x["message"] for x in result["findings"]))

    def test_report_conforms_to_shared_static_invariant_schema(self):
        result=MOD.analyze_bytes(legacy_dds())
        schema=json.loads(
            (REPO/"schemas"/"skyrim-static-invariant-report-v1.schema.json").read_text(encoding="utf-8")
        )
        errors=list(Draft202012Validator(schema).iter_errors(result))
        self.assertEqual(errors,[])

if __name__=="__main__":
    unittest.main()
