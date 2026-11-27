"""Test M3: nối model (không gọi mạng — post_json được giả lập)."""
import os
import sys
import io
import socket
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codebase"))
import ai  # noqa: E402
import tracing  # noqa: E402

OPENAI_REPLY = {"choices": [{"message": {"content": "[]"}}], "usage": {"prompt_tokens": 120, "completion_tokens": 30}}
CLAUDE_REPLY = {"content": [{"type": "text", "text": "{}"}], "usage": {"input_tokens": 90, "output_tokens": 12}}


def configured(provider, name="gpt-6-luna", verify="gpt-6.1-terra", key="test-key"):
    return mock.patch.multiple(ai, MODEL_PROVIDER=provider, MODEL_NAME=name, MODEL_NAME_VERIFY=verify, API_KEY=key)


class TestOpenAI(unittest.TestCase):
    def test_default_model_and_tokens(self):
        with configured("openai"), mock.patch("ai.post_json", return_value=OPENAI_REPLY) as post:
            r = ai.call_model("sys", "user")
        self.assertEqual(r, {"text": "[]", "model": "gpt-6-luna", "tokens_in": 120, "tokens_out": 30})
        url, headers, body = post.call_args[0][:3]
        self.assertIn("api.openai.com", url)
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertEqual(body["model"], "gpt-6-luna")
        self.assertEqual([m["role"] for m in body["messages"]], ["system", "user"])

    def test_verify_model_reported_by_name(self):
        """simulate tính giá theo khoá "model" → phải trả đúng tên model đã gọi."""
        with configured("openai"), mock.patch("ai.post_json", return_value=OPENAI_REPLY) as post:
            r = ai.call_model("sys", "user", model=ai.verify_model())
        self.assertEqual(r["model"], "gpt-6.1-terra")
        self.assertEqual(post.call_args[0][2]["model"], "gpt-6.1-terra")

    def test_verify_model_falls_back_to_main(self):
        with configured("openai", verify=""):
            self.assertEqual(ai.verify_model(), "gpt-6-luna")

    def test_null_content_is_empty_text(self):
        reply = {"choices": [{"message": {"content": None}}], "usage": {"prompt_tokens": 5, "completion_tokens": 0}}
        with configured("openai"), mock.patch("ai.post_json", return_value=reply):
            self.assertEqual(ai.call_model("s", "u")["text"], "")


class TestOtherProviders(unittest.TestCase):
    def test_anthropic(self):
        with configured("anthropic", name="claude-haiku-5-5", verify="claude-sonnet-5-5"), \
                mock.patch("ai.post_json", return_value=CLAUDE_REPLY) as post:
            r = ai.call_model("sys", "user", model="claude-sonnet-5-5")
        self.assertEqual((r["model"], r["tokens_in"], r["tokens_out"]), ("claude-sonnet-5-5", 90, 12))
        self.assertEqual(post.call_args[0][1]["x-api-key"], "test-key")

    def test_unknown_provider_is_clear_error(self):
        with configured("gemini"):
            with self.assertRaises(NotImplementedError):
                ai.call_model("s", "u")

    def test_missing_key_or_model_is_clear_error(self):
        with configured("openai", key=""):
            with self.assertRaisesRegex(RuntimeError, "API_KEY"):
                ai.call_model("s", "u")
        with configured("openai", name=""):
            with self.assertRaisesRegex(RuntimeError, "MODEL_NAME"):
                ai.call_model("s", "u")


class TestFakeAndTrace(unittest.TestCase):
    def test_fake_ignores_model_argument(self):
        with configured("fake"):
            r = ai.call_model("s", "u", model="gpt-6.1-terra")
        self.assertEqual((r["model"], r["tokens_in"]), ("fake", 0))

    def test_each_call_is_traced_with_its_model(self):
        with configured("openai"), mock.patch("ai.post_json", return_value=OPENAI_REPLY):
            tracing.begin("t")
            ai.call_model("s", "u")
            ai.call_model("s", "u", model=ai.verify_model())
            summary, events = tracing.end()
        self.assertEqual(summary["model_calls"], 2)
        self.assertEqual(summary["models"], ["gpt-6-luna", "gpt-6.1-terra"])
        self.assertEqual(summary["tokens_in"], 240)

    def test_verify_uses_verify_model_and_classify_uses_main(self):
        import classify
        import verify
        with configured("openai"), mock.patch("ai.post_json", return_value=OPENAI_REPLY) as post:
            classify.classify_llm([{"table": "u", "column": "tt_sk"}], "")
            verify.verify_path_llm({"file": "a.ts", "line": 1, "kind": "ai_nuoc_ngoai", "endpoint": "x", "snippet": "u.email"},
                                   [{"table": "u", "column": "email", "nhom": "pii_co_ban", "do_tin_cay": 1.0}])
        models = [c[0][2]["model"] for c in post.call_args_list]
        self.assertEqual(models[0], "gpt-6-luna")
        self.assertEqual(models[-1], "gpt-6.1-terra")


def http_error(code, body=""):
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(body.encode("utf-8")))


class TestRetryAndMask(unittest.TestCase):
    """Review Khoa PR #8: thử lại khi lỗi tạm thời, che API key trong thông điệp lỗi."""

    def setUp(self):
        self.sleep = mock.patch("ai.time.sleep").start()
        self.addCleanup(mock.patch.stopall)

    def test_retry_429_then_ok(self):
        with configured("openai"), mock.patch("ai._send", side_effect=[http_error(429), OPENAI_REPLY]) as send:
            r = ai.call_model("s", "u")
        self.assertEqual(send.call_count, 2)
        self.assertEqual(r["tokens_in"], 120)
        self.assertEqual([c[0][0] for c in self.sleep.call_args_list], [2])

    def test_retry_5xx_and_timeout_then_give_up_with_error(self):
        errs = [http_error(503), socket.timeout("timed out"), http_error(500, "boom")]
        with configured("openai"), mock.patch("ai._send", side_effect=errs) as send:
            with self.assertRaisesRegex(RuntimeError, "HTTP 500.*sau 3 lần gọi"):
                ai.call_model("s", "u")
        self.assertEqual(send.call_count, 3)
        self.assertEqual([c[0][0] for c in self.sleep.call_args_list], [2, 4])

    def test_no_retry_on_401(self):
        with configured("openai"), mock.patch("ai._send", side_effect=[http_error(401)]) as send:
            with self.assertRaisesRegex(RuntimeError, "HTTP 401"):
                ai.call_model("s", "u")
        self.assertEqual(send.call_count, 1)
        self.sleep.assert_not_called()

    def test_key_masked_in_error(self):
        echo = http_error(400, '{"error": "bad key sk-proj-SECRET123 in header"}')
        with configured("openai", key="sk-proj-SECRET123"), mock.patch("ai._send", side_effect=[echo]):
            with self.assertRaises(RuntimeError) as cm:
                ai.call_model("s", "u")
        self.assertNotIn("sk-proj-SECRET123", str(cm.exception))
        self.assertIn("[KEY]", str(cm.exception))

    def test_failed_call_traced_as_error_without_tokens(self):
        with configured("openai"), mock.patch("ai._send", side_effect=[http_error(500) for _ in range(3)]):
            tracing.begin("t")
            with self.assertRaises(RuntimeError):
                ai.call_model("s", "u")
            summary, _ = tracing.end()
        self.assertEqual(summary["tokens_in"], 0)


class TestOptionalParams(unittest.TestCase):
    def body(self, provider, **env):
        reply = OPENAI_REPLY if provider == "openai" else CLAUDE_REPLY
        with configured(provider), mock.patch.multiple(ai, **env), \
                mock.patch("ai.post_json", return_value=reply) as post:
            ai.call_model("s", "u")
        return post.call_args[0][2]

    def test_openai_defaults_send_nothing_extra(self):
        b = self.body("openai", MODEL_MAX_TOKENS=None, MODEL_TEMPERATURE=None)
        self.assertNotIn("max_completion_tokens", b)
        self.assertNotIn("temperature", b)

    def test_openai_cap_and_temperature(self):
        b = self.body("openai", MODEL_MAX_TOKENS=4000, MODEL_TEMPERATURE=0.0)
        self.assertEqual((b["max_completion_tokens"], b["temperature"]), (4000, 0.0))

    def test_claude_needs_max_tokens(self):
        self.assertEqual(self.body("anthropic", MODEL_MAX_TOKENS=None, MODEL_TEMPERATURE=None)["max_tokens"], 1024)
        self.assertEqual(self.body("anthropic", MODEL_MAX_TOKENS=2048, MODEL_TEMPERATURE=None)["max_tokens"], 2048)

    def test_env_num(self):
        with mock.patch.dict(os.environ, {"X_NUM": " 12 ", "X_BAD": "abc", "X_EMPTY": ""}):
            self.assertEqual(ai._env_num("X_NUM", int), 12)
            self.assertIsNone(ai._env_num("X_EMPTY", int))
            with self.assertRaises(RuntimeError):
                ai._env_num("X_BAD", float)


if __name__ == "__main__":
    unittest.main()
