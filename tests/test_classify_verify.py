import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codebase"))
import classify  # noqa: E402
import verify  # noqa: E402


def reply(text):
    return {"text": text, "model": "mock", "tokens_in": 1, "tokens_out": 1}


class TestClassifyPrompt(unittest.TestCase):
    """Giữ quy tắc chung trong prompt phân loại (PR #15): sửa prompt sau này không được vô tình bỏ mất."""

    def test_prompt_keeps_timestamp_rule(self):
        s = classify.SYSTEM
        for must in ("created_at", "khong_ca_nhan", "hanh_vi_mang", "ngày sinh", "nhật ký truy cập", "mã phiên",
                     "bảng ghi thao tác của người dùng"):
            self.assertIn(must, s)

    def test_classify_llm_sends_this_prompt(self):
        seen = []

        def fake(system, user, **kw):
            seen.append(system)
            return reply('[{"table": "t", "column": "created_at", "nhom": "khong_ca_nhan", "do_tin_cay": 0.9}]')
        with mock.patch.object(classify, "call_model", fake):
            classify.classify_llm([{"table": "t", "column": "created_at"}], "app")
        self.assertEqual(seen, [classify.SYSTEM])


class TestClassifyRule(unittest.TestCase):
    def test_rule_matches_abbrev(self):
        r = classify.classify_rule([{"table": "bookings", "column": "vi_tri_gan_nhat"}])
        self.assertEqual(r[0]["nhom"], "vi_tri_dinh_vi")
        self.assertEqual(r[0]["do_tin_cay"], 1.0)

    def test_rule_prefers_sensitive_longest(self):
        r = classify.classify_rule([{"table": "u", "column": "anh_cccd_mat_truoc"}])
        self.assertEqual(r[0]["nhom"], "dinh_danh_dien_tu")
        r = classify.classify_rule([{"table": "u", "column": "so_cccd"}])
        self.assertEqual(r[0]["nhom"], "pii_co_ban")

    def test_rule_short_keyword_needs_whole_token(self):
        self.assertEqual(classify.classify_rule([{"table": "u", "column": "gps_lat"}])[0]["nhom"], "vi_tri_dinh_vi")
        self.assertEqual(classify.classify_rule([{"table": "u", "column": "gpsx"}])[0]["nhom"], "khong_ca_nhan")

    def test_rule_unmatched(self):
        r = classify.classify_rule([{"table": "u", "column": "tt_sk"}])
        self.assertEqual((r[0]["nhom"], r[0]["do_tin_cay"]), ("khong_ca_nhan", 0.5))


class TestClassifyLLM(unittest.TestCase):
    def test_llm_ok(self):
        with mock.patch("classify.call_model", return_value=reply(
                '```json\n[{"table":"u","column":"tt_sk","nhom":"suc_khoe","do_tin_cay":0.9}]\n```')):
            r = classify.classify_llm([{"table": "u", "column": "tt_sk"}], "app khám bệnh")
        self.assertEqual((r[0]["nhom"], r[0]["do_tin_cay"]), ("suc_khoe", 0.9))

    def test_llm_unknown_group_becomes_khong_ro(self):
        with mock.patch("classify.call_model", return_value=reply(
                '[{"table":"u","column":"tt_sk","nhom":"health","do_tin_cay":0.9}]')):
            r = classify.classify_llm([{"table": "u", "column": "tt_sk"}], "")
        self.assertEqual((r[0]["nhom"], r[0]["do_tin_cay"]), ("khong_ro", 0.0))

    def test_llm_bad_json_retries_once_then_khong_ro(self):
        with mock.patch("classify.call_model", return_value=reply("xin lỗi, tôi không chắc")) as m:
            out = classify.classify_llm([{"table": "u", "column": "tt_sk"}], "")
        self.assertEqual(m.call_count, 2)
        self.assertEqual((out[0]["nhom"], out[0]["do_tin_cay"]), ("khong_ro", 0.0))

    def test_llm_missing_column_is_khong_ro(self):
        with mock.patch("classify.call_model", return_value=reply('[{"table":"u","column":"a","nhom":"pii_co_ban","do_tin_cay":0.8}]')):
            out = classify.classify_llm([{"table": "u", "column": "a"}, {"table": "u", "column": "b"}], "")
        self.assertEqual([o["nhom"] for o in out], ["pii_co_ban", "khong_ro"])

    def test_prompt_has_no_row_data_and_one_call(self):
        cols = [{"table": "u", "column": c} for c in ("a", "b", "c")]
        with mock.patch("classify.call_model", return_value=reply("[]")) as m:
            classify.classify_llm(cols, "mô tả")
        self.assertEqual(m.call_count, 1)
        system, user = m.call_args[0][:2]
        self.assertIn("Chỉ trả JSON", system)
        self.assertNotRegex(user, r"D\d+\.\d")

    def test_empty_columns_no_call(self):
        with mock.patch("classify.call_model") as m:
            self.assertEqual(classify.classify_llm([], ""), [])
        m.assert_not_called()


class TestParse(unittest.TestCase):
    def test_parse_json_reply(self):
        self.assertEqual(classify.parse_json_reply('ok\n```json\n[1]\n```', list), [1])
        self.assertEqual(classify.parse_json_reply('{"a":1}', dict), {"a": 1})
        self.assertIsNone(classify.parse_json_reply('{"a":1}', list))
        self.assertIsNone(classify.parse_json_reply("không có json", list))


class TestVerify(unittest.TestCase):
    SINK = {"file": "a.ts", "line": 3, "kind": "ai_nuoc_ngoai", "endpoint": "chat.completions.create",
            "snippet": 'const k="sk-abc123def456ghi789"\nawait openai.chat.completions.create({messages:[{content: user.email}]})'}
    PII = [{"table": "users", "column": "email", "nhom": "pii_co_ban", "do_tin_cay": 1.0}]

    def test_redact(self):
        t = verify.redact('const k="sk-abc123def456ghi789"; SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOi.x.y; '
                          'g="AIzaSyD-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"')
        for s in ("sk-abc", "eyJhbGci", "AIzaSy"):
            self.assertNotIn(s, t)

    def test_rule_path_pii_in_snippet(self):
        p = verify.verify_path_rule(self.SINK, self.PII)
        self.assertEqual((p["xac_nhan"], p["nguon"], p["truong_ca_nhan"]), (True, "he_thong", ["users.email"]))

    def test_rule_path_no_pii(self):
        p = verify.verify_path_rule(dict(self.SINK, snippet="await openai.chat.completions.create({messages:[]})"), self.PII)
        self.assertFalse(p["xac_nhan"])

    def test_llm_path_snippet_redacted(self):
        with mock.patch("verify.call_model", return_value=reply(
                '{"xac_nhan": true, "truong_ca_nhan": ["users.email"], "nguon": "he_thong"}')) as m:
            p = verify.verify_path_llm(self.SINK, self.PII)
        self.assertEqual(p["nguon"], "he_thong")
        self.assertNotIn("sk-abc", m.call_args[0][1])

    def test_llm_path_garbage_needs_human(self):
        with mock.patch("verify.call_model", return_value=reply("???")) as m:
            p = verify.verify_path_llm(self.SINK, self.PII)
        self.assertEqual(m.call_count, 2)
        self.assertEqual((p["xac_nhan"], p["nguon"]), (True, "khong_ro"))

    def test_llm_path_bad_enum_needs_human(self):
        with mock.patch("verify.call_model", return_value=reply('{"xac_nhan": true, "truong_ca_nhan": [], "nguon": "server"}')):
            self.assertEqual(verify.verify_path_llm(self.SINK, self.PII)["nguon"], "khong_ro")


if __name__ == "__main__":
    unittest.main()


class TestVerifyUserTypedVsBusiness(unittest.TestCase):
    """Review của Thịnh (PR #15): chữ người dùng cuối tự gõ ≠ nội dung nghiệp vụ lấy từ request."""

    def test_prompt_distinguishes_end_user_text_from_business_content(self):
        s = verify.SYSTEM
        for must in ("NGƯỜI DÙNG CUỐI", "nguoi_dung_tu_nhap", "Nội dung nghiệp vụ", "mô tả sản phẩm",
                     "xac_nhan = false"):
            self.assertIn(must, s)

    def _c1(self, reply_text):
        import rules
        sink = {"file": "app/api/viet-lai/route.ts", "line": 6, "kind": "ai_nuoc_ngoai", "endpoint": "responses.create",
                "snippet": "const { tieuDe, gioiThieu } = await req.json();\nawait client.responses.create({ input: gioiThieu });"}
        with mock.patch.object(verify, "call_model", lambda *a, **k: reply(reply_text)):
            res = verify.verify_path_llm(sink, [{"table": "khach", "column": "email"}])
        res["sink"] = sink
        return rules.evaluate_c1([res])["trang_thai"]

    def test_business_content_path_is_not_activated(self):
        self.assertEqual(self._c1('{"xac_nhan": false, "truong_ca_nhan": [], "nguon": "khong_ro"}'), "KHONG_KICH_HOAT")

    def test_end_user_free_text_needs_lawyer(self):
        self.assertEqual(self._c1('{"xac_nhan": true, "truong_ca_nhan": [], "nguon": "nguoi_dung_tu_nhap"}'), "CAN_LUAT_SU")

