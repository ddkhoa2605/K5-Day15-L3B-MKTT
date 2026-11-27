"""Test cho các lỗi review sau CP2 (chế độ llm, cổng xác nhận bản nháp, consent, kiểu trả về của model, giới hạn sink)."""
import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

os.environ["MODEL_PROVIDER"] = "fake"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "codebase"))
import agent  # noqa: E402
import scanner  # noqa: E402
import verify  # noqa: E402

SECRET = "sk-proj-abcdef1234567890XYZ"
CASE = {"mo_ta": "App đặt sân", "schema": ["users(id, email)", "bookings(id, user_id, vi_tri_gan_nhat)"],
        "code": [{"file": "a.ts", "line": 3, "text": 'const k = "%s"; await openai.chat.completions.create({messages:[{content: user.email}]})' % SECRET}],
        "loai_hinh": "doanh_nghiep_sieu_nho", "so_chu_the_luy_ke": 4200}


def rep(text):
    return {"text": text, "model": "mock", "tokens_in": 1, "tokens_out": 1}


def report_json(out):
    return json.loads(re.findall(r"```json\s*(.*?)```", out, re.S)[-1])


def run(text, mode="rule"):
    with mock.patch.dict(os.environ, {"SHP_MODE": mode}):
        return agent.answer(text)["output"]


class TestLlmMode(unittest.TestCase):
    def test_prompt_is_redacted(self):
        with mock.patch("agent.call_model", return_value=rep("{}")) as m:
            run(json.dumps(CASE), mode="llm")
        self.assertNotIn(SECRET, m.call_args[0][1])
        self.assertIn("[REDACTED]", m.call_args[0][1])

    def test_invented_codes_kept_but_flagged(self):
        ans = '{"C1": {"trang_thai": "KICH_HOAT", "can_cu": ["Luat91 D20.2", "Luat91 D99.9"]}, "C2": {"trang_thai": "KHONG_KICH_HOAT", "can_cu": "ND356 D6"}, "C3": {"trang_thai": "CON_MIEN_TRU", "can_cu": []}}'
        with mock.patch("agent.call_model", return_value=rep(ans)):
            out = run(json.dumps(CASE), mode="llm")
        j = report_json(out)
        self.assertEqual(j["ket_qua"]["C1"]["can_cu"], ["Luat91 D20.2", "Luat91 D99.9"])  # giữ nguyên để đo (ablation B)
        self.assertEqual(j["ket_qua"]["C2"]["can_cu"], ["ND356 D6"])  # chuỗi không bị tách thành ký tự
        self.assertEqual(j["ma_ngoai_bang_luat"], ["Luat91 D99.9"])
        self.assertIn("ABLATION", out)


class TestDraftGate(unittest.TestCase):
    def test_no_draft_without_confirmation(self):
        agent._LAST.clear()
        out = run(json.dumps(CASE))
        self.assertNotIn("BẢN NHÁP", out)
        self.assertIn("xac_nhan", out)

    def test_draft_after_confirmation(self):
        run(json.dumps(CASE))
        out = run("xac_nhan")
        self.assertIn("BẢN NHÁP", out)
        self.assertFalse(report_json(out)["tu_choi"])

    def test_confirmation_without_result_refused(self):
        agent._LAST.clear()
        self.assertTrue(report_json(run("xác nhận"))["tu_choi"])


class TestConsentRoundtrip(unittest.TestCase):
    def test_terms_columns_on_users(self):
        cols = scanner.parse_sql("create table users(id uuid, email text, terms_accepted_at timestamptz, terms_version text);")
        c = scanner.find_consent({}, cols)
        self.assertEqual((c["bang_consent"], c["du_3_truong"]), ("users", True))

    def test_terms_columns_need_time_and_version(self):
        cols = scanner.parse_sql("create table users(id uuid, terms_accepted boolean);")
        self.assertFalse(scanner.find_consent({}, cols)["du_3_truong"])

    def test_repo_to_case_keeps_consent_insert(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "supabase", "migrations"))
            os.makedirs(os.path.join(d, "app"))
            with open(os.path.join(d, "supabase", "migrations", "1.sql"), "w", encoding="utf-8") as f:
                f.write("create table nhat_ky(id int, member_id uuid, doc_version text, logged_at timestamptz);")
            with open(os.path.join(d, "app", "c.ts"), "w", encoding="utf-8") as f:
                f.write("\n" * 20 + 'await db.from("nhat_ky").insert({ member_id: u.id, loai: "consent_given", doc_version: V })\n')
            direct = scanner.find_consent(scanner.load_repo(d), scanner.repo_columns(scanner.load_repo(d)))
            case = scanner.case_from_repo(d)
            again = scanner.find_consent(scanner.files_from_case(case), scanner.columns_from_case(case))
        self.assertEqual(direct["bang_consent"], "nhat_ky")
        self.assertEqual((again["bang_consent"], again["du_3_truong"]), ("nhat_ky", True))


class TestVerifyTypes(unittest.TestCase):
    SINK = {"file": "a.ts", "line": 1, "kind": "ai_nuoc_ngoai", "endpoint": "x", "snippet": "user.email"}
    PII = [{"table": "users", "column": "email", "nhom": "pii_co_ban", "do_tin_cay": 1.0}]

    def test_wrong_field_types_no_crash(self):
        for bad in ('{"xac_nhan": true, "truong_ca_nhan": 5, "nguon": "he_thong"}',
                    '{"xac_nhan": true, "truong_ca_nhan": "users.email", "nguon": "he_thong"}',
                    '{"xac_nhan": "true", "truong_ca_nhan": [], "nguon": "he_thong"}'):
            with mock.patch("verify.call_model", return_value=rep(bad)):
                p = verify.verify_path_llm(self.SINK, self.PII)
            self.assertIn(p["nguon"], verify.NGUON)
            self.assertIsInstance(p["truong_ca_nhan"], list)


class TestSinkLimit(unittest.TestCase):
    def test_rule_mode_checks_every_sink(self):
        code = [{"file": "f%d.ts" % i, "line": 1, "text": "await openai.chat.completions.create({c: user.email})"} for i in range(8)]
        j = report_json(run(json.dumps(dict(CASE, code=code))))
        self.assertEqual(len(j["ket_qua"]["C1"]["bang_chung"]), 8)


if __name__ == "__main__":
    unittest.main()
