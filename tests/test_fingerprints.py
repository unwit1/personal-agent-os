import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.fingerprints import nul_joined_sha256  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
