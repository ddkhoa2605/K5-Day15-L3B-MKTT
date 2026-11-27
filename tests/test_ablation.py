"""Test eval/ablation.py — ablation 3 chế độ, khoảng tin cậy Wilson, khoá holdout (chỉ thư viện chuẩn)."""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eval"))
import ablation  # noqa: E402
import build_benchmark  # noqa: E402


def fake_answer_factory(correct_ids):
    """answer() giả: trả đúng nhãn cho các id trong correct_ids, còn lại trả 'mọi thứ không kích hoạt'."""
    by_input = {ablation.case_input(c): c for c in ablation.load_cases("dev")}

    def answer(text):
        c = by_input[text]
        n = c["nhan"]
        if c["id"] in correct_ids:
            per = n["can_cu_theo_nhom"]
            kq = {g: {"trang_thai": n[g], "can_cu": per[g]} for g in ("C1", "C2", "C3")}
            kq["C3"]["nhom_nhay_cam"] = n["nhom_nhay_cam"]
        else:
            kq = {g: {"trang_thai": "KHONG_KICH_HOAT", "can_cu": []} for g in ("C1", "C2")}
            kq["C3"] = {"trang_thai": "CON_MIEN_TRU", "can_cu": [], "nhom_nhay_cam": []}
        body = {"tu_choi": False, "ket_qua": kq, "da_gui_ra_ngoai": [], "che_do": os.environ.get("SHP_MODE")}
        return {"output": "chữ\n```json\n" + json.dumps(body, ensure_ascii=False) + "\n```"}
    return answer


class TestWilson(unittest.TestCase):
    def test_known_value(self):
        lo, hi = ablation.wilson(10, 12)
        self.assertAlmostEqual(lo, 0.552, places=2)
        self.assertAlmostEqual(hi, 0.953, places=2)

    def test_edges(self):
        self.assertEqual(ablation.wilson(0, 0), (None, None))
        lo, hi = ablation.wilson(0, 5)
        self.assertEqual(lo, 0.0)
        self.assertGreater(hi, 0.0)
        lo, hi = ablation.wilson(5, 5)
        self.assertLess(lo, 1.0)
        self.assertAlmostEqual(hi, 1.0)


class TestCases(unittest.TestCase):
    def test_taps(self):
        self.assertEqual(len(ablation.load_cases("dev")), 50)
        self.assertEqual(len(ablation.load_cases("holdout")), 10)
        self.assertTrue(all(c["id"].startswith("dt-") for c in ablation.load_cases("data_that")))
        with self.assertRaises(ValueError):
            ablation.load_cases("benchmark")

    def test_input_matches_benchmark_and_hides_label(self):
        c = next(x for x in ablation.load_cases("dev") if x["id"] == "c3-vt-001")
        inp = ablation.case_input(c)
        self.assertNotIn('"nhan"', inp)
        self.assertNotIn("c3-vt-001", inp)  # id lộ nhóm/tag nên bị bỏ
        self.assertEqual(inp, build_benchmark.row_of(c)["input"])


class TestRunAndSummarize(unittest.TestCase):
    def setUp(self):
        self._mode = os.environ.get("SHP_MODE")

    def tearDown(self):  # run_mode đặt SHP_MODE; trả lại như cũ để không ảnh hưởng test khác
        if self._mode is None:
            os.environ.pop("SHP_MODE", None)
        else:
            os.environ["SHP_MODE"] = self._mode

    def test_run_mode_sets_env_and_grades(self):
        cases = [c for c in ablation.load_cases("dev") if c["id"] in ("c1-ro-001", "c3-vt-001", "c1-am-001")]
        rows = ablation.run_mode(cases, "rule", answer=fake_answer_factory({"c1-ro-001", "c1-am-001"}))
        got = {r["id"]: r for r in rows}
        self.assertEqual(got["c1-ro-001"]["pass"], 1)
        self.assertEqual(got["c3-vt-001"]["pass"], 0)
        self.assertEqual(got["c3-vt-001"]["phan_loai_viet_tat"], 0)
        self.assertEqual(got["c1-am-001"]["bao_dong_gia"], 0)
        self.assertEqual(os.environ.get("SHP_MODE"), "rule")

    def test_crash_in_answer_is_recorded_not_raised(self):
        def boom(text):
            raise RuntimeError("model hỏng")
        rows = ablation.run_mode(ablation.load_cases("dev")[:2], "hybrid", answer=boom)
        self.assertTrue(all(r["pass"] == 0 and "model hỏng" in r["ghi_chu"] for r in rows))

    def test_summarize_counts_and_by_tag(self):
        cases = ablation.load_cases("dev")
        vt = [c["id"] for c in cases if c["nhan"]["tag"] == "vt"]
        rows = ablation.run_mode(cases, "llm", answer=fake_answer_factory(set(vt[:4])))
        s = ablation.summarize(rows)
        self.assertEqual(s["n"], 50)
        self.assertEqual(s["metrics"]["phan_loai_viet_tat"], [4, len(vt)])
        self.assertEqual(s["by_tag"]["vt"], [4, len(vt)])
        self.assertEqual(s["passed"], sum(r["pass"] for r in rows))

    def test_invalid_output_on_am_is_excluded_and_counted(self):
        # đồng bộ với grade.py (review của Thắng): output hỏng không được làm bao_dong_gia đẹp giả
        cases = [c for c in ablation.load_cases("dev") if c["nhan"]["tag"] == "am"][:3]
        rows = ablation.run_mode(cases, "llm", answer=lambda text: {"output": "model trả rỗng"})
        s = ablation.summarize(rows)
        self.assertEqual(s["metrics"]["bao_dong_gia"], [0, 0])
        self.assertEqual(s["loai"]["bao_dong_gia"], 3)
        self.assertEqual(s["passed"], 0)

    def test_small_n_marked_in_table(self):
        self.assertIn("n nhỏ", ablation._cell(3, 7))
        self.assertNotIn("n nhỏ", ablation._cell(3, 12))

    def test_fake_model_detected(self):
        self.assertTrue(ablation.is_fake({"models": ["fake"], "model_calls": 3}, "llm"))
        self.assertTrue(ablation.is_fake({"models": [], "model_calls": 0}, "hybrid"))
        self.assertFalse(ablation.is_fake({"models": [], "model_calls": 0}, "rule"))  # rule không cần model
        self.assertFalse(ablation.is_fake({"models": ["claude-haiku-5-5"], "model_calls": 50}, "llm"))


class TestReportAndHoldoutLock(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self._mode = os.environ.get("SHP_MODE")

    def tearDown(self):
        shutil.rmtree(self.dir)
        if self._mode is None:
            os.environ.pop("SHP_MODE", None)
        else:
            os.environ["SHP_MODE"] = self._mode

    def test_report_has_all_modes_and_n(self):
        cases = ablation.load_cases("dev")
        res = {m: ablation.run_mode(cases, m, answer=fake_answer_factory({c["id"] for c in cases[:30]}))
               for m in ablation.MODES}
        md = ablation.render_md("dev", {m: ablation.summarize(r) for m, r in res.items()}, meta={"commit": "abc1234"})
        for m in ablation.MODES:
            self.assertIn(m, md)
        self.assertIn("n=50", md)
        self.assertIn("Wilson", md)

    def test_holdout_runs_only_once(self):
        lock = os.path.join(self.dir, "holdout.lock")
        ablation.claim_holdout(lock, {"commit": "abc1234"})
        with self.assertRaises(SystemExit):
            ablation.claim_holdout(lock, {"commit": "def5678"})

    def test_holdout_preflight_blocks_before_lock(self):
        # Có provider thật nhưng thiếu key hoặc ai.py chưa gọi được model → dừng TRƯỚC khi ghi khoá holdout
        lock = os.path.join(self.dir, "holdout.lock")

        def broken(system, user):
            raise NotImplementedError("chưa viết phần gọi model thật cho MODEL_PROVIDER=openai")
        with self.assertRaises(SystemExit):
            ablation.preflight_model(broken, api_key="sk-x")
        with self.assertRaises(SystemExit):
            ablation.preflight_model(lambda s, u: {"text": "ok", "model": "gpt-6-luna"}, api_key="")
        with self.assertRaises(SystemExit):  # gọi "thành công" nhưng là model giả
            ablation.preflight_model(lambda s, u: {"text": "x", "model": "fake"}, api_key="sk-x")
        self.assertFalse(os.path.exists(lock))
        self.assertEqual(ablation.preflight_model(lambda s, u: {"text": "ok", "model": "gpt-6-luna"}, api_key="sk-x"),
                         "gpt-6-luna")

    def test_holdout_refuses_fake_model(self):
        with self.assertRaises(SystemExit):
            ablation.check_can_run("holdout", ["rule", "llm", "hybrid"], provider="fake", limit=None)
        with self.assertRaises(SystemExit):
            ablation.check_can_run("holdout", ["rule"], provider="anthropic", limit=None)  # holdout phải đủ 3 chế độ
        with self.assertRaises(SystemExit):
            ablation.check_can_run("holdout", list(ablation.MODES), provider="anthropic", limit=5)
        ablation.check_can_run("holdout", list(ablation.MODES), provider="anthropic", limit=None)  # không ném
        ablation.check_can_run("dev", ["rule"], provider="fake", limit=3)  # dev thì thử thoải mái


if __name__ == "__main__":
    unittest.main()
