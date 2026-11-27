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
        self.assertEqual(seen, [classify.SYSTEM] * classify.PASSES)


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
                '```json\n[{"table":"u","column":"tt_sk","nhom":"suc_khoe","do_tin_cay":0.9,"can_cu":"tt_sk"}]\n```')):
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
        self.assertEqual(m.call_count, 2 * classify.PASSES)   # mỗi lượt: gọi lại 1 lần khi JSON hỏng
        self.assertEqual((out[0]["nhom"], out[0]["do_tin_cay"]), ("khong_ro", 0.0))

    def test_llm_missing_column_is_khong_ro(self):
        with mock.patch("classify.call_model", return_value=reply('[{"table":"u","column":"a","nhom":"pii_co_ban","do_tin_cay":0.8}]')):
            out = classify.classify_llm([{"table": "u", "column": "a"}, {"table": "u", "column": "b"}], "")
        self.assertEqual([o["nhom"] for o in out], ["pii_co_ban", "khong_ro"])

    def test_prompt_has_no_row_data_and_one_call_per_pass(self):
        cols = [{"table": "u", "column": c} for c in ("a", "b", "c")]
        with mock.patch("classify.call_model", return_value=reply("[]")) as m:
            classify.classify_llm(cols, "mô tả")
        self.assertEqual(m.call_count, classify.PASSES)
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


class TestFreeTextRule(unittest.TestCase):
    """Quyết định của Khoa (28/11): cột chữ tự do tự nó không nhạy cảm → pii_co_ban, C3 kèm lời nhắc. Ví dụ tự dựng."""

    def test_free_text_names(self):
        for yes in ("loi_nhan", "ghi_chu_noi_bo", "message_content", "comment", "noi_dung_gop_y"):
            self.assertTrue(classify.is_free_text(yes), yes)
        for no in ("content_type", "text_color", "so_luong", "body_mass", "trang_thai"):
            self.assertFalse(classify.is_free_text(no), no)

    def test_rule_mode_free_text_is_basic_pii(self):
        r = classify.classify_rule([{"table": "gop_y", "column": "loi_nhan"}])
        self.assertEqual((r[0]["nhom"], r[0]["do_tin_cay"]), ("pii_co_ban", classify.FREE_TEXT_CONF))

    def test_llm_unsure_free_text_becomes_basic_pii_but_sensitive_kept(self):
        rep = ('[{"table": "gop_y", "column": "loi_nhan", "nhom": "khong_ro", "do_tin_cay": 0.0},'
               ' {"table": "kham", "column": "ghi_chu_trieu_chung", "nhom": "suc_khoe", "do_tin_cay": 0.9, "can_cu": "trieu_chung"}]')
        with mock.patch.object(classify, "call_model", lambda *a, **k: reply(rep)):
            r = classify.classify_llm([{"table": "gop_y", "column": "loi_nhan"},
                                       {"table": "kham", "column": "ghi_chu_trieu_chung"}], "app")
        self.assertEqual([(x["nhom"], x["do_tin_cay"]) for x in r], [("pii_co_ban", 0.8), ("suc_khoe", 0.9)])

    def test_prompt_states_rule(self):
        self.assertIn("Cột chữ tự do", classify.SYSTEM)
        self.assertIn("pii_co_ban", classify.SYSTEM)

    def test_c3_keeps_status_and_adds_note(self):
        import rules
        labels = [{"table": "gop_y", "column": "loi_nhan", "nhom": "pii_co_ban", "do_tin_cay": 0.8, "file": None, "line": None}]
        case = {"loai_hinh": "doanh_nghiep_sieu_nho", "so_chu_the_luy_ke": 300}
        c3 = rules.evaluate(case, labels, [], {"tich_san": [], "im_lang_dong_y": []})["C3"]
        self.assertEqual(c3["trang_thai"], "CON_MIEN_TRU")
        self.assertIn("gop_y.loi_nhan", c3["luu_y"])
        self.assertIn("không đọc nội dung", c3["giai_thich"])


class TestEmailRecipientRule(unittest.TestCase):
    """Quyết định của Khoa (28/11): email qua dịch vụ nước ngoài → người nhận quyết bằng nguồn địa chỉ. Ví dụ tự dựng."""

    def _sink(self, snippet):
        return {"file": "lib/thu.ts", "line": 3, "kind": "email", "endpoint": "api.mailjet.com", "snippet": snippet}

    def test_recipient_source(self):
        self.assertEqual(verify.email_recipient('{ to: hoiVien.dia_chi_thu, subject: "Chào" }'), "dong")
        self.assertEqual(verify.email_recipient("{ to: process.env.HOP_THU_CHU, subject: x }"), "co_dinh")
        self.assertEqual(verify.email_recipient("{ to: HOP_THU_QUAN_TRI }"), "co_dinh")
        self.assertEqual(verify.email_recipient("{ to: ['chu@tiem.example'] }"), "co_dinh")
        self.assertEqual(verify.email_recipient("await guiThu(payload)"), "khong_ro")

    def test_dynamic_recipient_activates_c1(self):
        import rules
        res = verify.verify_path_rule(self._sink("await mj.post({ to: hoiVien.hopThu, text: 'Mã giảm giá' })"), [])
        self.assertEqual((res["xac_nhan"], res["nguon"], res["truong_ca_nhan"]), (True, "he_thong", [verify.RECIPIENT]))
        res["sink"] = self._sink("")
        self.assertEqual(rules.evaluate_c1([res])["trang_thai"], "KICH_HOAT")

    def test_fixed_admin_recipient_without_customer_data_not_activated(self):
        res = verify.verify_path_rule(self._sink("await mj.post({ to: process.env.HOP_THU_CHU, text: 'Có đơn mới' })"), [])
        self.assertFalse(res["xac_nhan"])

    def test_fixed_admin_recipient_with_customer_data_activated(self):
        cols = [{"table": "don", "column": "ten_nguoi_dat"}]
        res = verify.verify_path_rule(
            self._sink("await mj.post({ to: process.env.HOP_THU_CHU, text: `Đơn của ${d.ten_nguoi_dat}` })"), cols)
        self.assertEqual((res["xac_nhan"], res["truong_ca_nhan"]), (True, ["don.ten_nguoi_dat"]))

    def test_unknown_recipient_is_unsure_path(self):
        res = verify.verify_path_rule(self._sink("const r = await fetch(\"https://api.mailjet.com/v3.1/send\", opts);"), [])
        self.assertEqual(res, verify.UNSURE)

    def test_model_said_no_but_dynamic_recipient(self):
        with mock.patch.object(verify, "call_model", lambda *a, **k: reply('{"xac_nhan": false, "truong_ca_nhan": [], "nguon": "khong_ro"}')):
            res = verify.verify_path_llm(self._sink("await mj.post({ to: hoiVien.dia_chi_thu })"), [])
        self.assertTrue(res["xac_nhan"])
        self.assertEqual(res["nguon"], "he_thong")

    def test_email_api_via_fetch_is_email_kind(self):
        import scanner
        s = scanner.find_sinks({"t.ts": 'await fetch("https://api.mailjet.com/v3.1/send", { method: "POST" })'})
        self.assertEqual(s[0]["kind"], "email")


class TestClassifyGuardrails(unittest.TestCase):
    """Vòng sửa trước run-3 (comment của Khoa trên PR #15), mục 1, 4, 5, 6. Ví dụ tự dựng."""

    def _run(self, replies, cols, mo_ta="app bán cây cảnh"):
        it = iter(replies)
        with mock.patch.object(classify, "call_model", lambda *a, **k: reply(next(it))):
            return classify.classify_llm(cols, mo_ta)

    def test_sensitive_without_real_evidence_is_demoted(self):
        rep = '[{"table":"don","column":"tong_gia","nhom":"tai_chinh","do_tin_cay":0.9,"can_cu":"thông tin thẻ của khách"}]'
        r = self._run([rep] * 2, [{"table": "don", "column": "tong_gia"}])
        self.assertEqual((r[0]["nhom"], r[0]["do_tin_cay"]), ("khong_ro", 0.0))

    def test_sensitive_with_evidence_from_description_is_kept(self):
        rep = '[{"table":"ho_so","column":"ma_x","nhom":"suc_khoe","do_tin_cay":0.8,"can_cu":"Kết quả xét nghiệm"}]'
        r = self._run([rep] * 2, [{"table": "ho_so", "column": "ma_x"}], "Phòng khám lưu kết quả xét nghiệm của bệnh nhân")
        self.assertEqual(r[0]["nhom"], "suc_khoe")

    def test_keyword_hit_rescues_missing_evidence(self):   # mục 4: chỉ hạ khi CẢ căn cứ lẫn từ khoá cùng thiếu
        col = {"table": "nguoi_dung", "column": "so_tai_khoan_ngan_hang"}
        hit = [h[2] for h in classify._keyword_hits(col["column"])]
        rep = '[{"table":"nguoi_dung","column":"so_tai_khoan_ngan_hang","nhom":"%s","do_tin_cay":0.9,"can_cu":""}]' % hit[0]
        r = self._run([rep] * 2, [col])
        self.assertEqual(r[0]["nhom"], hit[0])

    def test_unknown_group_retried_once(self):   # mục 5
        bad = '[{"table":"t","column":"c","nhom":"tai-chinh","do_tin_cay":0.9}]'
        ok = '[{"table":"t","column":"c","nhom":"pii_co_ban","do_tin_cay":0.9,"can_cu":"c"}]'
        r = self._run([bad, ok] * classify.PASSES, [{"table": "t", "column": "c"}])
        self.assertEqual(r[0]["nhom"], "pii_co_ban")

    def test_vote(self):   # mục 6
        self.assertEqual(classify._vote([("suc_khoe", 0.9, "x"), ("suc_khoe", 0.7, "")])[:2], ("suc_khoe", 0.7))
        self.assertEqual(classify._vote([("suc_khoe", 0.9, "x"), ("pii_co_ban", 0.9, "")])[0], "khong_ro")
        self.assertEqual(classify._vote([("pii_co_ban", 0.9, ""), ("khong_ca_nhan", 0.8, "")])[0], "pii_co_ban")
        self.assertEqual(classify._vote([("khong_ro", 0.0, ""), ("pii_co_ban", 0.8, "")])[0], "khong_ro")

    def test_prompt_has_guardrails(self):
        for must in ("can_cu", "CHÉP NGUYÊN VĂN", "Không suy diễn nhóm nhạy cảm", "KHÔNG phải giá bán",
                     "KHÔNG phải cột nối hai bản ghi", "KHÔNG phải thứ hạng"):
            self.assertIn(must, classify.SYSTEM)

