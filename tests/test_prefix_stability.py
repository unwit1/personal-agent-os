"""IMP-0018: shared prefix detection and stabilization for vLLM prefix caching."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_os.orchestrator import prefix_stability  # noqa: E402


class PrefixStabilityTests(unittest.TestCase):
    """Tests for prefix detection, stabilization, and fingerprinting."""

    def test_run_prefix_absent_returns_none(self) -> None:
        """When shared_prefix is absent, run_prefix returns None."""
        self.assertIsNone(prefix_stability.run_prefix({}))
        self.assertIsNone(prefix_stability.run_prefix({"other": "data"}))

    def test_run_prefix_direct_field(self) -> None:
        """Extracts shared_prefix from record's top-level shared_prefix field."""
        prefix = "You are a helpful assistant."
        self.assertEqual(prefix_stability.run_prefix({"shared_prefix": prefix}), prefix)

    def test_run_prefix_nested_in_context_economy(self) -> None:
        """Extracts shared_prefix from context_economy dict."""
        prefix = "You are a helpful assistant."
        self.assertEqual(
            prefix_stability.run_prefix({"context_economy": {"shared_prefix": prefix}}),
            prefix
        )

    def test_run_prefix_prefers_direct_over_nested(self) -> None:
        """Direct shared_prefix takes precedence over context_economy."""
        direct = "direct prefix"
        nested = "nested prefix"
        result = prefix_stability.run_prefix({
            "shared_prefix": direct,
            "context_economy": {"shared_prefix": nested}
        })
        self.assertEqual(result, direct)

    def test_run_prefix_empty_string_returns_none(self) -> None:
        """Empty string is not a valid prefix."""
        self.assertIsNone(prefix_stability.run_prefix({"shared_prefix": ""}))
        self.assertIsNone(prefix_stability.run_prefix({"context_economy": {"shared_prefix": ""}}))

    def test_run_prefix_non_string_returns_none(self) -> None:
        """Non-string values are ignored."""
        self.assertIsNone(prefix_stability.run_prefix({"shared_prefix": 123}))
        self.assertIsNone(prefix_stability.run_prefix({"shared_prefix": None}))
        self.assertIsNone(prefix_stability.run_prefix({"context_economy": {"shared_prefix": []}}))

    def test_stabilize_no_prefix_returns_unchanged(self) -> None:
        """When prefix is None, messages are returned unchanged."""
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"}
        ]
        result = prefix_stability.stabilize(messages, None)
        self.assertEqual(result, messages)

    def test_stabilize_does_not_mutate_input(self) -> None:
        """stabilize never mutates the input messages list or dicts."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"}
        ]
        original = [dict(m) for m in messages]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(messages, original)
        self.assertIsNot(result, messages)
        self.assertIsNot(result[0], messages[0])

    def test_stabilize_prepends_prefix_to_existing_system_message(self) -> None:
        """Prefix is prepended to existing system message content."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": "Original system"},
            {"role": "user", "content": "User message"}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[0]["content"], "shared prefix\n\nOriginal system")

    def test_stabilize_creates_system_message_if_none_exists(self) -> None:
        """If no system message exists, one is created with the prefix."""
        prefix = "shared prefix"
        messages = [
            {"role": "user", "content": "User message"}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[0]["content"], "shared prefix")
        self.assertEqual(result[1]["role"], "user")

    def test_stabilize_handles_empty_messages(self) -> None:
        """Empty message list gets a system message with prefix."""
        prefix = "shared prefix"
        messages = []
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[0]["content"], "shared prefix")

    def test_stabilize_already_starts_with_prefix(self) -> None:
        """If system message already starts with prefix, nothing changes."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": "shared prefixadditional"},
            {"role": "user", "content": "User message"}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(result[0]["content"], "shared prefix\n\nadditional")

    def test_stabilize_repairs_whitespace_drift(self) -> None:
        """Trailing whitespace drift in prefix is repaired."""
        prefix = "P\n\n"
        messages = [
            {"role": "system", "content": "P\nrest"},
            {"role": "user", "content": "User message"}
        ]
        result = prefix_stability.stabilize(messages, prefix)
        self.assertEqual(result[0]["content"], prefix + "rest")

    def test_stabilize_repairs_space_drift(self) -> None:
        """Space drift after prefix is normalized."""
        prefix = "P\n\n"
        messages = [
            {"role": "system", "content": "P  rest"},
            {"role": "user", "content": "User message"}
        ]
        result = prefix_stability.stabilize(messages, prefix)
        self.assertEqual(result[0]["content"], prefix + "rest")

    def test_stabilize_exact_prefix_with_content_unchanged(self) -> None:
        """Content already equal to prefix + rest is returned unchanged."""
        prefix = "P\n\n"
        messages = [
            {"role": "system", "content": prefix + "rest"},
            {"role": "user", "content": "User message"}
        ]
        result = prefix_stability.stabilize(messages, prefix)
        self.assertEqual(result[0]["content"], prefix + "rest")

    def test_stabilize_multiple_system_messages_uses_first(self) -> None:
        """Only the first system message is modified."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": "First system"},
            {"role": "system", "content": "Second system"},
            {"role": "user", "content": "User message"}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(result[0]["content"], "shared prefix\n\nFirst system")
        self.assertEqual(result[1]["content"], "Second system")

    def test_stabilize_identical_prefix_for_different_tasks(self) -> None:
        """Two different task texts produce identical leading bytes when using same prefix."""
        prefix = "shared prefix\nYou are a helpful assistant.\n"

        messages1 = [
            {"role": "system", "content": "Ignored"},
            {"role": "user", "content": "Task 1: do this specific thing"}
        ]
        result1 = prefix_stability.stabilize(messages1, prefix)

        messages2 = [
            {"role": "system", "content": "Also ignored"},
            {"role": "user", "content": "Task 2: do that different thing"}
        ]
        result2 = prefix_stability.stabilize(messages2, prefix)

        prefix_bytes1 = result1[0]["content"][:len(prefix)].encode("utf-8")
        prefix_bytes2 = result2[0]["content"][:len(prefix)].encode("utf-8")

        self.assertEqual(prefix_bytes1, prefix_bytes2)
        self.assertNotEqual(result1[1]["content"], result2[1]["content"])

    def test_prefix_fingerprint_is_stable(self) -> None:
        """Same prefix always produces same fingerprint."""
        prefix = "shared prefix"
        fp1 = prefix_stability.prefix_fingerprint(prefix)
        fp2 = prefix_stability.prefix_fingerprint(prefix)

        self.assertEqual(fp1, fp2)

    def test_prefix_fingerprint_is_unique(self) -> None:
        """Different prefixes produce different fingerprints."""
        prefix1 = "shared prefix 1"
        prefix2 = "shared prefix 2"

        fp1 = prefix_stability.prefix_fingerprint(prefix1)
        fp2 = prefix_stability.prefix_fingerprint(prefix2)

        self.assertNotEqual(fp1, fp2)

    def test_prefix_fingerprint_is_hex(self) -> None:
        """Fingerprint is a valid SHA256 hex string (64 chars)."""
        prefix = "shared prefix"
        fp = prefix_stability.prefix_fingerprint(prefix)

        self.assertEqual(len(fp), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in fp))

    def test_prefix_fingerprint_matches_manual_sha256(self) -> None:
        """Fingerprint matches manual SHA256 computation."""
        import hashlib

        prefix = "shared prefix"
        expected = hashlib.sha256(prefix.encode("utf-8")).hexdigest()
        result = prefix_stability.prefix_fingerprint(prefix)

        self.assertEqual(result, expected)

    def test_prefix_fingerprint_utf8_encoding(self) -> None:
        """Fingerprint correctly encodes non-ASCII characters."""
        prefix = "shared prefix with émojis 🚀"
        result = prefix_stability.prefix_fingerprint(prefix)

        self.assertEqual(len(result), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_stabilize_complex_scenario(self) -> None:
        """Complex scenario with system message followed by multiple user/assistant exchanges."""
        prefix = "You are a helpful assistant in deep-coding mode.\n"
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "First user message"},
            {"role": "assistant", "content": "First assistant response"},
            {"role": "user", "content": "Second user message"}
        ]

        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]["role"], "system")
        self.assertTrue(result[0]["content"].startswith(prefix))
        self.assertEqual(result[1]["role"], "user")
        self.assertEqual(result[1]["content"], "First user message")
        self.assertEqual(result[2]["role"], "assistant")
        self.assertEqual(result[3]["role"], "user")

    def test_stabilize_drift_repair_requires_whitespace_boundary(self) -> None:
        """Drift repair only fires if rest begins with whitespace or is empty.

        If content starts with a stripped prefix but the rest is non-whitespace,
        it's unrelated text (not a drifted prefix) and should prepend instead.
        """
        prefix = "Be brief\n"
        messages = [
            {"role": "system", "content": "Be briefly helpful"}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(result[0]["content"], "Be brief\n\nBe briefly helpful")

    def test_stabilize_drift_repair_with_whitespace_boundary(self) -> None:
        """Drift repair fires when rest starts with whitespace after stripped prefix."""
        prefix = "Be brief\n"
        messages = [
            {"role": "system", "content": "Be brief  helper"}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(result[0]["content"], "Be brief\n\nhelper")

    def test_stabilize_list_content_empty_list(self) -> None:
        """Empty content list gets a text block with the prefix."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": []}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertIsInstance(result[0]["content"], list)
        self.assertEqual(len(result[0]["content"]), 1)
        self.assertEqual(result[0]["content"][0], {"type": "text", "text": prefix})

    def test_stabilize_list_content_text_block(self) -> None:
        """Text block in list content is stabilized like string content."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": [
                {"type": "text", "text": "Original text"}
            ]}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertIsInstance(result[0]["content"], list)
        self.assertEqual(result[0]["content"][0]["text"], prefix + prefix_stability.SEPARATOR + "Original text")

    def test_stabilize_list_content_text_block_already_has_prefix(self) -> None:
        """Text block already starting with prefix is not modified."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": [
                {"type": "text", "text": "shared prefixrest"}
            ]}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(result[0]["content"][0]["text"], "shared prefix\n\nrest")

    def test_stabilize_list_content_non_text_block_first(self) -> None:
        """Non-text block content gets a new text block inserted first."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": [
                {"type": "image_url", "image_url": {"url": "http://example.com"}}
            ]}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertIsInstance(result[0]["content"], list)
        self.assertEqual(len(result[0]["content"]), 2)
        self.assertEqual(result[0]["content"][0], {"type": "text", "text": prefix})
        self.assertEqual(result[0]["content"][1]["type"], "image_url")

    def test_stabilize_list_content_multiple_blocks(self) -> None:
        """Multiple blocks with text first - only first text block is modified."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": [
                {"type": "text", "text": "First text"},
                {"type": "image_url", "image_url": {"url": "http://example.com"}},
                {"type": "text", "text": "Second text"}
            ]}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(result[0]["content"][0]["text"], prefix + prefix_stability.SEPARATOR + "First text")
        self.assertEqual(result[0]["content"][1]["type"], "image_url")
        self.assertEqual(result[0]["content"][2]["text"], "Second text")

    def test_stabilize_list_content_drift_repair_with_whitespace(self) -> None:
        """List content drift repair also respects whitespace boundary."""
        prefix = "Be brief\n"
        messages = [
            {"role": "system", "content": [
                {"type": "text", "text": "Be brief  helper"}
            ]}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(result[0]["content"][0]["text"], "Be brief\n\nhelper")

    def test_stabilize_list_content_no_repair_without_whitespace(self) -> None:
        """List content drift repair respects whitespace boundary - no repair case."""
        prefix = "Be brief\n"
        messages = [
            {"role": "system", "content": [
                {"type": "text", "text": "Be briefly helpful"}
            ]}
        ]
        result = prefix_stability.stabilize(messages, prefix)

        self.assertEqual(result[0]["content"][0]["text"], "Be brief\n\nBe briefly helpful")

    def test_stabilize_list_content_does_not_mutate_text_block(self) -> None:
        """List content with text block is not mutated during stabilization."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": [
                {"type": "text", "text": "Original text"}
            ]}
        ]
        original_content = [dict(b) if isinstance(b, dict) else b for b in messages[0]["content"]]
        original_text = original_content[0]["text"]

        result = prefix_stability.stabilize(messages, prefix)

        # Original message's content should be unchanged
        self.assertEqual(messages[0]["content"][0]["text"], "Original text")
        self.assertEqual(messages[0]["content"][0]["text"], original_text)
        # Result should have the prefix
        self.assertEqual(result[0]["content"][0]["text"], "shared prefix\n\nOriginal text")

    def test_stabilize_list_content_does_not_mutate_non_text_first_block(self) -> None:
        """List content with non-text first block is not mutated during insertion."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": [
                {"type": "image_url", "image_url": {"url": "http://example.com"}}
            ]}
        ]
        original_len = len(messages[0]["content"])

        result = prefix_stability.stabilize(messages, prefix)

        # Original message's content length should be unchanged
        self.assertEqual(len(messages[0]["content"]), original_len)
        self.assertEqual(messages[0]["content"][0]["type"], "image_url")
        # Result should have the prefix inserted
        self.assertEqual(len(result[0]["content"]), 2)
        self.assertEqual(result[0]["content"][0]["type"], "text")

    def test_stabilize_list_content_does_not_mutate_multi_block(self) -> None:
        """List content with multiple blocks is not mutated during modification."""
        prefix = "shared prefix"
        messages = [
            {"role": "system", "content": [
                {"type": "text", "text": "First text"},
                {"type": "image_url", "image_url": {"url": "http://example.com"}},
                {"type": "text", "text": "Second text"}
            ]}
        ]
        original_text_1 = messages[0]["content"][0]["text"]
        original_text_2 = messages[0]["content"][2]["text"]
        original_len = len(messages[0]["content"])

        result = prefix_stability.stabilize(messages, prefix)

        # Original should be unchanged
        self.assertEqual(messages[0]["content"][0]["text"], original_text_1)
        self.assertEqual(messages[0]["content"][2]["text"], original_text_2)
        self.assertEqual(len(messages[0]["content"]), original_len)
        # Result should have modified first block
        self.assertEqual(result[0]["content"][0]["text"], "shared prefix\n\nFirst text")
        self.assertEqual(result[0]["content"][2]["text"], "Second text")


class SeparatorTests(unittest.TestCase):
    def test_requests_share_the_prefix_and_separator_bytes(self) -> None:
        prefix = "Run context: build the thing."
        a = prefix_stability.stabilize([{"role": "system", "content": "Task one"}], prefix)[0]["content"]
        b = prefix_stability.stabilize([{"role": "system", "content": prefix + "  Task two"}], prefix)[0]["content"]
        stable = prefix + prefix_stability.SEPARATOR
        self.assertTrue(a.startswith(stable) and b.startswith(stable))
        self.assertEqual((a[len(stable):], b[len(stable):]), ("Task one", "Task two"))


if __name__ == "__main__":
    unittest.main()
