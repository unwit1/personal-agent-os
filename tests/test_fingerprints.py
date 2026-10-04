import hashlib
import json
import sys
import unittest
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.fingerprints import json_sha256, nul_joined_sha256, text_sha256  # noqa: E402


class FingerprintTests(unittest.TestCase):
    def test_full_digest_matches_hashlib_for_two_parts(self) -> None:
        """Full digest equals hashlib.sha256('a\\0b'.encode('utf-8')).hexdigest() for parts ['a','b']."""
        result = nul_joined_sha256(["a", "b"])
        expected = hashlib.sha256("a\0b".encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)

    def test_length_12_returns_first_12_chars(self) -> None:
        """length=12 returns the first 12 characters of the digest."""
        result = nul_joined_sha256(["a", "b"], length=12)
        full_digest = hashlib.sha256("a\0b".encode("utf-8")).hexdigest()
        self.assertEqual(result, full_digest[:12])
        self.assertEqual(len(result), 12)

    def test_single_part_equals_sha256_of_that_part(self) -> None:
        """A single part equals sha256 of that part."""
        part = "test_string"
        result = nul_joined_sha256([part])
        expected = hashlib.sha256(part.encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)

    def test_empty_list_equals_sha256_of_empty_bytes(self) -> None:
        """An empty list equals sha256 of b''."""
        result = nul_joined_sha256([])
        expected = hashlib.sha256(b"").hexdigest()
        self.assertEqual(result, expected)

    def test_non_ascii_parts_encoded_as_utf8(self) -> None:
        """Non-ASCII parts are encoded as UTF-8."""
        parts = ["hello", "世界"]
        result = nul_joined_sha256(parts)
        expected = hashlib.sha256("hello\0世界".encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)

    def test_length_0_raises_valueerror(self) -> None:
        """length=0 raises ValueError."""
        with self.assertRaises(ValueError):
            nul_joined_sha256(["a", "b"], length=0)

    def test_length_65_raises_valueerror(self) -> None:
        """length=65 raises ValueError."""
        with self.assertRaises(ValueError):
            nul_joined_sha256(["a", "b"], length=65)

    def test_accepts_generator(self) -> None:
        """It accepts a generator."""
        gen = (x for x in ["a", "b"])
        result = nul_joined_sha256(gen)
        expected = hashlib.sha256("a\0b".encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)

    def test_length_1_minimum_valid(self) -> None:
        """length=1 is the minimum valid value."""
        result = nul_joined_sha256(["a"], length=1)
        expected = hashlib.sha256("a".encode("utf-8")).hexdigest()
        self.assertEqual(result, expected[:1])
        self.assertEqual(len(result), 1)

    def test_length_64_maximum_valid(self) -> None:
        """length=64 is the maximum valid value (full digest)."""
        result = nul_joined_sha256(["a"], length=64)
        expected = hashlib.sha256("a".encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)
        self.assertEqual(len(result), 64)


class TextSha256Tests(unittest.TestCase):
    def test_equals_hashlib_for_abc(self) -> None:
        """text_sha256('abc') equals hashlib.sha256('abc'.encode()).hexdigest()."""
        result = text_sha256("abc")
        expected = hashlib.sha256("abc".encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)

    def test_equals_hashlib_for_empty_string(self) -> None:
        """text_sha256('') equals hashlib.sha256(''.encode()).hexdigest()."""
        result = text_sha256("")
        expected = hashlib.sha256("".encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)

    def test_equals_hashlib_for_non_ascii(self) -> None:
        """text_sha256('世界') equals hashlib.sha256('世界'.encode()).hexdigest()."""
        result = text_sha256("世界")
        expected = hashlib.sha256("世界".encode("utf-8")).hexdigest()
        self.assertEqual(result, expected)

    def test_length_16_prefix(self) -> None:
        """text_sha256 with length=16 returns first 16 characters."""
        result = text_sha256("abc", length=16)
        expected = hashlib.sha256("abc".encode("utf-8")).hexdigest()[:16]
        self.assertEqual(result, expected)
        self.assertEqual(len(result), 16)

    def test_length_0_raises_valueerror(self) -> None:
        """length=0 raises ValueError."""
        with self.assertRaises(ValueError):
            text_sha256("abc", length=0)

    def test_length_65_raises_valueerror(self) -> None:
        """length=65 raises ValueError."""
        with self.assertRaises(ValueError):
            text_sha256("abc", length=65)


class JsonSha256Tests(unittest.TestCase):
    def test_dict_with_sort_keys_true(self) -> None:
        """json_sha256({'b':1,'a':[1,'é']}) equals hashlib on sorted JSON."""
        value = {"b": 1, "a": [1, "é"]}
        result = json_sha256(value)
        expected = hashlib.sha256(
            json.dumps(value, sort_keys=True).encode("utf-8")
        ).hexdigest()
        self.assertEqual(result, expected)

    def test_ensure_ascii_false_differs_from_default(self) -> None:
        """json_sha256 with ensure_ascii=False differs from default for non-ASCII."""
        value = {"text": "世界"}
        default_result = json_sha256(value, ensure_ascii=True)
        ascii_false_result = json_sha256(value, ensure_ascii=False)
        self.assertNotEqual(default_result, ascii_false_result)

    def test_ensure_ascii_false_matches_hashlib(self) -> None:
        """json_sha256 with ensure_ascii=False matches hashlib encoding."""
        value = {"text": "世界"}
        result = json_sha256(value, ensure_ascii=False)
        expected = hashlib.sha256(
            json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        self.assertEqual(result, expected)

    def test_sort_keys_false_on_list(self) -> None:
        """json_sha256 with sort_keys=False on a list works correctly."""
        value = [3, 1, 2]
        result = json_sha256(value, sort_keys=False)
        expected = hashlib.sha256(
            json.dumps(value, sort_keys=False).encode("utf-8")
        ).hexdigest()
        self.assertEqual(result, expected)

    def test_default_callable_on_pathlib(self) -> None:
        """json_sha256 with default=str handles PurePosixPath correctly."""
        value = {"path": PurePosixPath("/foo/bar")}
        result = json_sha256(value, sort_keys=True, default=str)
        expected = hashlib.sha256(
            json.dumps(value, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        self.assertEqual(result, expected)

    def test_dict_key_order_does_not_affect_result(self) -> None:
        """Different key orders in input produce the same hash with sort_keys=True."""
        dict1 = {"a": 1, "b": 2, "c": 3}
        dict2 = {"c": 3, "a": 1, "b": 2}
        result1 = json_sha256(dict1)
        result2 = json_sha256(dict2)
        self.assertEqual(result1, result2)

    def test_length_0_raises_valueerror(self) -> None:
        """length=0 raises ValueError."""
        with self.assertRaises(ValueError):
            json_sha256({"a": 1}, length=0)

    def test_length_65_raises_valueerror(self) -> None:
        """length=65 raises ValueError."""
        with self.assertRaises(ValueError):
            json_sha256({"a": 1}, length=65)


if __name__ == "__main__":
    unittest.main()
