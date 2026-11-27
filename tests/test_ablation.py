"""Test eval/ablation.py — ablation 3 chế độ, khoảng tin cậy Wilson, khoá holdout (chỉ thư viện chuẩn)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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
        ablation.claim_holdout(lock, {"commit": "abc1234"}, history=[])  # chỉ kiểm khoá trên máy, không gọi git
        with self.assertRaises(SystemExit):
            ablation.claim_holdout(lock, {"commit": "def5678"}, history=[])

    def test_lock_history_fetches_before_reading_all_branches(self):
        # Review của Khoa (PR #13): máy khác chạy holdout rồi push khoá → phải git fetch trước khi đọc lịch sử
        calls = []

        def fake_run(cmd, **kw):
            calls.append(cmd)
            out = {"log": "9f8e7d6 Holdout: chạy một lần\n", "rev-parse": "false\n"}.get(cmd[1], "")
            return subprocess.CompletedProcess(cmd, 0, stdout=out)
        hist = ablation.holdout_lock_history(os.path.join(ablation.HERE, "holdout.lock"), run=fake_run)
        self.assertEqual(hist, ["9f8e7d6 Holdout: chạy một lần"])
        self.assertEqual(calls[0][:2], ["git", "fetch"])
        self.assertEqual(calls[-1][:2], ["git", "log"])  # đọc lịch sử SAU fetch và sau kiểm clone nông
        self.assertIn("--all", calls[-1])

    def test_shallow_clone_fails_closed(self):
        # Review của Minh (PR #16): clone nông chỉ thấy một phần lịch sử → có thể bỏ sót khoá cũ → DỪNG
        calls = []

        def shallow(cmd, **kw):
            calls.append(cmd)
            out = "true\n" if "--is-shallow-repository" in cmd else ""
            return subprocess.CompletedProcess(cmd, 0, stdout=out)
        with self.assertRaises(SystemExit) as cm:
            ablation.holdout_lock_history(os.path.join(ablation.HERE, "holdout.lock"), run=shallow)
        self.assertIn("unshallow", str(cm.exception.code))
        self.assertFalse(any("log" in c for c in calls))  # không đọc lịch sử khi lịch sử thiếu

    def test_lock_history_fails_closed(self):
        # Review của Khoa (PR #13): không fetch được hoặc không đọc được git → DỪNG, không coi là "chưa chạy"
        lock = os.path.join(ablation.HERE, "holdout.lock")

        def fail_on(word, exc):
            def run(cmd, **kw):
                if word in cmd:
                    raise exc
                return subprocess.CompletedProcess(cmd, 0, stdout="false\n" if "rev-parse" in cmd else "")
            return run
        for run in (fail_on("fetch", subprocess.CalledProcessError(128, "git fetch")),
                    fail_on("log", subprocess.CalledProcessError(128, "git log")),
                    fail_on("fetch", FileNotFoundError("git")),
                    fail_on("log", subprocess.TimeoutExpired("git log", 60)),
                    fail_on("rev-parse", subprocess.CalledProcessError(128, "git rev-parse"))):
            with self.assertRaises(SystemExit):
                ablation.holdout_lock_history(lock, run=run)

    def test_claim_holdout_does_not_lock_when_git_unreadable(self):
        # khoá đặt trong repo (thư mục tạm dưới eval/) để đi tới đúng bước gọi git, không dừng sớm vì khác ổ đĩa
        d = tempfile.mkdtemp(dir=ablation.HERE)
        try:
            lock = os.path.join(d, "holdout.lock")
            calls = []

            def broken(cmd, **kw):
                calls.append(cmd)
                raise subprocess.CalledProcessError(128, cmd)
            with mock.patch.object(ablation.subprocess, "run", broken):
                with self.assertRaises(SystemExit):
                    ablation.claim_holdout(lock, {"commit": "abc1234"})
            self.assertTrue(calls)  # đã thử gọi git
            self.assertFalse(os.path.exists(lock))
        finally:
            shutil.rmtree(d)

    def test_lock_outside_repo_fails_closed(self):
        # Windows: thư mục tạm khác ổ với repo → relpath lỗi. Bản cũ nuốt lỗi và coi là "chưa chạy".
        lock = os.path.join(self.dir, "holdout.lock")
        try:
            os.path.relpath(lock, ablation.ROOT)
        except ValueError:
            with self.assertRaises(SystemExit):
                ablation.holdout_lock_history(lock, run=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, stdout=""))
        else:
            self.skipTest("thư mục tạm cùng ổ với repo")

    def test_holdout_preflight_blocks_before_lock(self):
        # Có provider thật nhưng thiếu key hoặc ai.py chưa gọi được model → dừng TRƯỚC khi ghi khoá holdout
        lock = os.path.join(self.dir, "holdout.lock")
        ok = lambda s, u, model=None: {"text": "ok", "model": model or "gpt-6-luna"}  # noqa: E731

        def broken(system, user, model=None):
            raise NotImplementedError("chưa viết phần gọi model thật cho MODEL_PROVIDER=openai")
        with self.assertRaises(SystemExit):
            ablation.preflight_model(broken, api_key="sk-x")
        with self.assertRaises(SystemExit):
            ablation.preflight_model(ok, api_key="")
        with self.assertRaises(SystemExit):  # gọi "thành công" nhưng là model giả
            ablation.preflight_model(lambda s, u, model=None: {"text": "x", "model": "fake"}, api_key="sk-x")
        self.assertFalse(os.path.exists(lock))
        self.assertEqual(ablation.preflight_model(ok, api_key="sk-x"), ["gpt-6-luna"])

    def test_preflight_also_checks_verify_model(self):
        # Review của Khoa (PR #9): hybrid dùng model kiểm chứng riêng — phải gọi thử cả model đó
        calls = []

        def verify_broken(system, user, model=None):
            calls.append(model)
            if model == "gpt-6.1-terra":
                raise RuntimeError("model không tồn tại hoặc không có quyền")
            return {"text": "ok", "model": model or "gpt-6-luna"}
        with self.assertRaises(SystemExit):
            ablation.preflight_model(verify_broken, api_key="sk-x", verify_model="gpt-6.1-terra")
        self.assertIn("gpt-6.1-terra", calls)
        with self.assertRaises(SystemExit):  # model kiểm chứng trả model giả
            ablation.preflight_model(lambda s, u, model=None: {"text": "ok", "model": "fake" if model else "gpt-6-luna"},
                                     api_key="sk-x", verify_model="gpt-6.1-terra")
        ok = lambda s, u, model=None: {"text": "ok", "model": model or "gpt-6-luna"}  # noqa: E731
        self.assertEqual(ablation.preflight_model(ok, api_key="sk-x", verify_model="gpt-6.1-terra"),
                         ["gpt-6-luna", "gpt-6.1-terra"])
        self.assertEqual(ablation.preflight_model(ok, api_key="sk-x", verify_model="gpt-6-luna"), ["gpt-6-luna"])

    def test_holdout_lock_in_git_history_blocks(self):
        # Review của Khoa: khoá trên máy có thể bị xoá; khoá đã từng commit thì cũng không cho chạy lại
        lock = os.path.join(self.dir, "holdout.lock")
        with self.assertRaises(SystemExit):
            ablation.claim_holdout(lock, {"commit": "abc1234"}, history=["9f8e7d6 Holdout: chạy một lần"])
        self.assertFalse(os.path.exists(lock))
        ablation.claim_holdout(lock, {"commit": "abc1234"}, history=[])
        self.assertTrue(os.path.exists(lock))

    def test_report_name_depends_on_modes(self):
        # Review của Khoa: chạy tập con không được ghi đè bảng so sánh đủ 3 chế độ
        self.assertEqual(ablation.report_name("dev", list(ablation.MODES), None), "ablation-dev.md")
        self.assertEqual(ablation.report_name("dev", ["hybrid", "rule", "llm"], None), "ablation-dev.md")
        self.assertEqual(ablation.report_name("dev", ["rule"], None), "ablation-dev-rule.md")
        self.assertEqual(ablation.report_name("dev", ["rule", "hybrid"], None), "ablation-dev-rule-hybrid.md")
        self.assertEqual(ablation.report_name("dev", list(ablation.MODES), 5), "ablation-dev-thu.md")
        self.assertEqual(ablation.report_name("data_that", ["llm"], 3), "ablation-data_that-llm-thu.md")

    def test_report_notes_on_tuning_and_independence(self):
        cases = ablation.load_cases("dev")[:3]
        sums = {m: ablation.summarize(ablation.run_mode(cases, m, answer=fake_answer_factory(set()))) for m in ablation.MODES}
        dev = ablation.render_md("dev", sums, meta={})
        self.assertIn("sau khi chỉnh", dev)
        dt = ablation.render_md("data_that", sums, meta={})
        self.assertIn("không còn là tập độc lập", dt)
        self.assertNotIn("chưa ai nhìn", dt)
        self.assertNotIn("không** gửi chi tiết", dt)

    def test_holdout_refuses_fake_model(self):
        with self.assertRaises(SystemExit):
            ablation.check_can_run("holdout", ["rule", "llm", "hybrid"], provider="fake", limit=None)
        with self.assertRaises(SystemExit):
            ablation.check_can_run("holdout", ["rule"], provider="anthropic", limit=None)  # holdout phải đủ 3 chế độ
        with self.assertRaises(SystemExit):
            ablation.check_can_run("holdout", list(ablation.MODES), provider="anthropic", limit=5)
        ablation.check_can_run("holdout", list(ablation.MODES), provider="anthropic", limit=None)  # không ném
        ablation.check_can_run("dev", ["rule"], provider="fake", limit=3)  # dev thì thử thoải mái


def _fake_blind(n=2, split="blind"):
    """Case giả, KHÔNG phải dữ liệu bộ mù thật (PR này không chứa input hay nhãn bộ mù)."""
    return [{"id": "blind-%02d" % (i + 1), "mo_ta": "app thử %d" % i, "schema": ["t(id, ten)"], "code": [],
             "loai_hinh": "khong_ro", "so_chu_the_luy_ke": None,
             "nhan": {"split": split, "tag": "ro", "C1": "KHONG_KICH_HOAT", "C2": "KHONG_KICH_HOAT",
                      "C3": "CAN_NGUOI_XAC_NHAN", "nhom_nhay_cam": [], "can_cu": []}} for i in range(n)]


class TestBlindTap(unittest.TestCase):
    """Issue #20 mục 3.3: bộ mù chỉ chạy khi file khớp manifest, khoá riêng, đúng một lần như holdout."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.data = os.path.join(self.dir, "blind_cases.jsonl")
        self.man = os.path.join(self.dir, "blind.manifest")

    def tearDown(self):
        shutil.rmtree(self.dir)

    def _write(self, cases, crlf=False):
        nl = "\r\n" if crlf else "\n"
        with open(self.data, "w", encoding="utf-8", newline="") as f:
            f.write("".join(json.dumps(c, ensure_ascii=False) + nl for c in cases))

    def _manifest(self):
        with open(self.man, "w", encoding="utf-8", newline="\n") as f:
            f.write(ablation.blind_manifest_text(self.data, khoa_duyet="28/11 09:30 (Khoa)"))

    def test_manifest_roundtrip_loads_cases(self):
        self._write(_fake_blind())
        self._manifest()
        text = open(self.man, encoding="utf-8").read()
        self.assertIn("sha256: ", text)
        self.assertIn("so_cau: 2", text)
        self.assertIn("blind-01 ", text)
        self.assertNotIn("app thử", text)  # manifest chỉ có mã băm, không có input hay nhãn
        cases = ablation.load_blind(self.data, self.man)
        self.assertEqual([c["id"] for c in cases], ["blind-01", "blind-02"])

    def test_any_change_after_manifest_refuses(self):
        self._write(_fake_blind())
        self._manifest()
        changed = _fake_blind()
        changed[1]["nhan"]["C1"] = "KICH_HOAT"  # sửa nhãn sau khi khoá manifest
        self._write(changed)
        with self.assertRaises(SystemExit):
            ablation.load_blind(self.data, self.man)

    def test_line_hash_checked_even_if_file_hash_edited(self):
        self._write(_fake_blind())
        self._manifest()
        changed = _fake_blind()
        changed[0]["mo_ta"] = "đổi input"
        self._write(changed)
        good = ablation.blind_manifest_text(self.data, khoa_duyet="x").split("\n")
        old = open(self.man, encoding="utf-8").read().split("\n")
        # chỉ sửa dòng sha256 của cả file cho khớp, giữ mã băm từng câu cũ
        patched = [g if g.startswith("sha256:") else o for g, o in zip(good, old)]
        with open(self.man, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(patched))
        with self.assertRaises(SystemExit):
            ablation.load_blind(self.data, self.man)

    def test_crlf_checkout_still_matches(self):
        # git trên Windows có thể đổi LF thành CRLF lúc checkout: nội dung không đổi thì vẫn khớp
        self._write(_fake_blind())
        self._manifest()
        self._write(_fake_blind(), crlf=True)
        self.assertEqual(len(ablation.load_blind(self.data, self.man)), 2)

    def test_missing_files_or_wrong_split_refuse(self):
        with self.assertRaises(SystemExit):
            ablation.load_blind(self.data, self.man)  # chưa có file nào
        self._write(_fake_blind())
        with self.assertRaises(SystemExit):
            ablation.load_blind(self.data, self.man)  # chưa có manifest
        self._write(_fake_blind(split="dev"))
        self._manifest()
        with self.assertRaises(SystemExit):
            ablation.load_blind(self.data, self.man)  # case không phải split blind

    def test_blind_has_its_own_lock_and_holdout_rules(self):
        self.assertNotEqual(ablation.LOCKS["blind"], ablation.LOCKS["holdout"])
        self.assertTrue(ablation.LOCKS["blind"].endswith("blind.lock"))
        for bad in (dict(modes=["rule"], provider="openai", limit=None),
                    dict(modes=list(ablation.MODES), provider="fake", limit=None),
                    dict(modes=list(ablation.MODES), provider="openai", limit=3)):
            with self.assertRaises(SystemExit):
                ablation.check_can_run("blind", bad["modes"], provider=bad["provider"], limit=bad["limit"])
        ablation.check_can_run("blind", list(ablation.MODES), provider="openai", limit=None)  # không ném
        lock = os.path.join(self.dir, "blind.lock")
        ablation.claim_holdout(lock, {"tap": "blind"}, history=[], ten="bộ mù")
        with self.assertRaises(SystemExit) as cm:
            ablation.claim_holdout(lock, {"tap": "blind"}, history=[], ten="bộ mù")
        self.assertIn("bộ mù", str(cm.exception.code))
        with self.assertRaises(SystemExit) as cm:
            ablation.claim_holdout(os.path.join(self.dir, "x.lock"), {}, history=["abc Bộ mù"], ten="bộ mù")
        self.assertIn("bộ mù", str(cm.exception.code))


if __name__ == "__main__":
    unittest.main()
