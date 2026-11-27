"""Test eval/grade.py — chấm tự động theo eval/metric_spec.yaml (chỉ thư viện chuẩn)."""
import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eval"))
import grade  # noqa: E402

CIT = {"Luat91 D20.1", "Luat91 D20.2", "Luat91 D20.6", "Luat91 D9.3", "ND356 D6", "ND356 D6.3",
       "Luat91 D38.3", "ND356 D41.2", "ND356 D4h", "ND356 D4d"}


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def out(ket_qua=None, tu_choi=False, prefix="Kết luận cho người đọc…\n"):
    """Dựng output giống answer(): chữ cho người đọc + một khối ```json ở cuối."""
    body = {"tu_choi": tu_choi, "ket_qua": ket_qua or {}, "da_gui_ra_ngoai": [], "che_do": "rule"}
    return prefix + "```json\n" + json.dumps(body, ensure_ascii=False) + "\n```"


def kq(c1="KHONG_KICH_HOAT", c2="KHONG_KICH_HOAT", c3="CON_MIEN_TRU", cc1=(), cc2=(), cc3=(), nhom=()):
    return {"C1": {"trang_thai": c1, "can_cu": list(cc1)},
            "C2": {"trang_thai": c2, "can_cu": list(cc2)},
            "C3": {"trang_thai": c3, "can_cu": list(cc3), "nhom_nhay_cam": list(nhom)}}


EXP_C1 = "C1=KICH_HOAT;C2=KHONG_KICH_HOAT;C3=CON_MIEN_TRU;nhom=;can_cu=Luat91 D20.1|Luat91 D20.2|Luat91 D38.3|ND356 D41.2"
OUT_C1 = out(kq(c1="KICH_HOAT", cc1=["Luat91 D20.1", "Luat91 D20.2"], cc3=["Luat91 D38.3", "ND356 D41.2"]))


class TestParse(unittest.TestCase):
    def test_parse_expected_normal(self):
        e = grade.parse_expected("C1=KICH_HOAT;C2=KHONG_KICH_HOAT;C3=MAT_MIEN_TRU;nhom=vi_tri_dinh_vi;can_cu=ND356 D4h|Luat91 D38.3")
        self.assertFalse(e["tu_choi"])
        self.assertEqual(e["C3"], "MAT_MIEN_TRU")
        self.assertEqual(e["nhom"], {"vi_tri_dinh_vi"})
        self.assertEqual(e["can_cu"], {"ND356 D4h", "Luat91 D38.3"})

    def test_parse_expected_empty_sets(self):
        e = grade.parse_expected("C1=KHONG_KICH_HOAT;C2=KHONG_KICH_HOAT;C3=CON_MIEN_TRU;nhom=;can_cu=")
        self.assertEqual(e["nhom"], set())
        self.assertEqual(e["can_cu"], set())

    def test_parse_expected_refusal(self):
        self.assertTrue(grade.parse_expected("tu_choi=true")["tu_choi"])

    def test_parse_expected_malformed_raises(self):
        with self.assertRaises(ValueError):
            grade.parse_expected("C1=KICH_HOAT;nhom=")

    def test_extract_takes_last_json_block(self):
        o = "```json\n{\"tu_choi\": true}\n```\nchữ\n```json\n{\"tu_choi\": false, \"ket_qua\": {}}\n```"
        self.assertFalse(grade.extract_json(o)["tu_choi"])

    def test_extract_none_when_missing_or_broken(self):
        self.assertIsNone(grade.extract_json("không có khối json"))
        self.assertIsNone(grade.extract_json("```json\n{hỏng\n```"))
        self.assertIsNone(grade.extract_json("```json\n[1, 2]\n```"))  # không phải object


class TestIsPass(unittest.TestCase):
    def test_pass_when_all_match(self):
        self.assertTrue(grade.is_pass(OUT_C1, EXP_C1, CIT))

    def test_pass_criterion_from_plan(self):
        o = out(kq(c1="KICH_HOAT", cc1=["Luat91 D20.2"]))
        self.assertTrue(grade.is_pass(o, "C1=KICH_HOAT;C2=KHONG_KICH_HOAT;C3=CON_MIEN_TRU;nhom=;can_cu=Luat91 D20.2", CIT))

    def test_citation_order_does_not_matter(self):
        o = out(kq(c1="KICH_HOAT", cc1=["Luat91 D20.2", "Luat91 D20.1"], cc3=["ND356 D41.2", "Luat91 D38.3"]))
        self.assertTrue(grade.is_pass(o, EXP_C1, CIT))

    def test_can_cu_is_union_of_three_groups(self):
        # mã nằm ở nhóm nào không quan trọng, chỉ so hợp của 3 nhóm
        o = out(kq(c1="KICH_HOAT", cc1=["Luat91 D20.1"], cc2=["Luat91 D20.2"], cc3=["Luat91 D38.3", "ND356 D41.2"]))
        self.assertTrue(grade.is_pass(o, EXP_C1, CIT))

    def test_fail_on_invented_citation_even_if_label_has_it(self):
        o = out(kq(c1="KICH_HOAT", cc1=["Luat91 D99.9"]))
        self.assertFalse(grade.is_pass(o, "C1=KICH_HOAT;C2=KHONG_KICH_HOAT;C3=CON_MIEN_TRU;nhom=;can_cu=Luat91 D99.9", CIT))

    def test_fail_on_missing_or_extra_citation(self):
        o = out(kq(c1="KICH_HOAT", cc1=["Luat91 D20.1"], cc3=["Luat91 D38.3", "ND356 D41.2"]))
        self.assertFalse(grade.is_pass(o, EXP_C1, CIT))
        o = out(kq(c1="KICH_HOAT", cc1=["Luat91 D20.1", "Luat91 D20.2", "Luat91 D20.6"], cc3=["Luat91 D38.3", "ND356 D41.2"]))
        self.assertFalse(grade.is_pass(o, EXP_C1, CIT))

    def test_fail_on_state_mismatch(self):
        o = out(kq(c1="CAN_LUAT_SU", cc1=["Luat91 D20.1", "Luat91 D20.2"], cc3=["Luat91 D38.3", "ND356 D41.2"]))
        self.assertFalse(grade.is_pass(o, EXP_C1, CIT))

    def test_fail_on_nhom_mismatch(self):
        exp = "C1=KHONG_KICH_HOAT;C2=KHONG_KICH_HOAT;C3=MAT_MIEN_TRU;nhom=vi_tri_dinh_vi;can_cu=ND356 D4h|Luat91 D38.3|ND356 D41.2"
        ok = out(kq(c3="MAT_MIEN_TRU", cc3=["ND356 D4h", "Luat91 D38.3", "ND356 D41.2"], nhom=["vi_tri_dinh_vi"]))
        self.assertTrue(grade.is_pass(ok, exp, CIT))
        extra = out(kq(c3="MAT_MIEN_TRU", cc3=["ND356 D4h", "Luat91 D38.3", "ND356 D41.2"], nhom=["vi_tri_dinh_vi", "suc_khoe"]))
        self.assertFalse(grade.is_pass(extra, exp, CIT))

    def test_no_json_block_is_fail(self):
        self.assertFalse(grade.is_pass("chỉ có chữ", EXP_C1, CIT))

    def test_broken_json_is_fail_not_crash(self):
        self.assertFalse(grade.is_pass("```json\n{\"tu_choi\": fal\n```", EXP_C1, CIT))
        self.assertFalse(grade.is_pass(out({"C1": "không phải dict"}), EXP_C1, CIT))

    def test_refusal_expected(self):
        self.assertTrue(grade.is_pass(out(tu_choi=True), "tu_choi=true", CIT))
        self.assertFalse(grade.is_pass(OUT_C1, "tu_choi=true", CIT))

    def test_refusing_a_normal_case_fails(self):
        self.assertFalse(grade.is_pass(out(tu_choi=True), EXP_C1, CIT))

    def test_reasons_explain_failure(self):
        o = out(kq(c1="KHONG_KICH_HOAT", cc3=["Luat91 D38.3", "ND356 D41.2"]))
        r = grade.reasons(o, EXP_C1, CIT)
        self.assertTrue(any("C1" in x for x in r), r)
        self.assertEqual(grade.reasons(OUT_C1, EXP_C1, CIT), [])


class TestMetrics(unittest.TestCase):
    def test_phan_loai_viet_tat_only_on_vt(self):
        exp = "C1=KHONG_KICH_HOAT;C2=KHONG_KICH_HOAT;C3=MAT_MIEN_TRU;nhom=suc_khoe;can_cu=ND356 D4d|Luat91 D38.3|ND356 D41.2"
        right = out(kq(c3="MAT_MIEN_TRU", nhom=["suc_khoe"]))
        wrong = out(kq(c3="CON_MIEN_TRU"))
        self.assertEqual(grade.metrics(right, exp, "vt", "kho", CIT)["phan_loai_viet_tat"], 1)
        self.assertEqual(grade.metrics(wrong, exp, "vt", "kho", CIT)["phan_loai_viet_tat"], 0)
        self.assertIsNone(grade.metrics(right, exp, "ro", "thuong", CIT)["phan_loai_viet_tat"])

    def test_trich_dan_dung_only_when_label_activates(self):
        self.assertEqual(grade.metrics(OUT_C1, EXP_C1, "ro", "thuong", CIT)["trich_dan_dung"], 1)
        quiet = "C1=KHONG_KICH_HOAT;C2=KHONG_KICH_HOAT;C3=CON_MIEN_TRU;nhom=;can_cu=Luat91 D38.3|ND356 D41.2"
        self.assertIsNone(grade.metrics(OUT_C1, quiet, "am", "thuong", CIT)["trich_dan_dung"])

    def test_bao_dong_gia_on_am(self):
        quiet = "C1=KHONG_KICH_HOAT;C2=KHONG_KICH_HOAT;C3=CON_MIEN_TRU;nhom=;can_cu=Luat91 D38.3|ND356 D41.2"
        alarm = out(kq(c3="MAT_MIEN_TRU", nhom=["vi_tri_dinh_vi"]))
        calm = out(kq(cc3=["Luat91 D38.3", "ND356 D41.2"]))
        self.assertEqual(grade.metrics(alarm, quiet, "am", "thuong", CIT)["bao_dong_gia"], 1)
        self.assertEqual(grade.metrics(calm, quiet, "am", "thuong", CIT)["bao_dong_gia"], 0)
        self.assertIsNone(grade.metrics(alarm, quiet, "ro", "thuong", CIT)["bao_dong_gia"])

    def test_tu_choi_dung(self):
        need_lawyer = "C1=CAN_LUAT_SU;C2=KHONG_KICH_HOAT;C3=CON_MIEN_TRU;nhom=;can_cu=Luat91 D20.6|Luat91 D38.3|ND356 D41.2"
        ok = out(kq(c1="CAN_LUAT_SU"))
        sure = out(kq(c1="KICH_HOAT"))
        self.assertEqual(grade.metrics(ok, need_lawyer, "chatbox", "kho", CIT)["tu_choi_dung"], 1)
        self.assertEqual(grade.metrics(sure, need_lawyer, "chatbox", "kho", CIT)["tu_choi_dung"], 0)
        self.assertEqual(grade.metrics(out(tu_choi=True), "tu_choi=true", None, "tu_choi", CIT)["tu_choi_dung"], 1)
        self.assertIsNone(grade.metrics(OUT_C1, EXP_C1, "ro", "thuong", CIT)["tu_choi_dung"])

    def test_bao_dong_gia_excludes_invalid_output(self):
        # Review của Thắng: output hỏng không được tính là "không báo động giả" (làm metric đẹp giả)
        quiet = "C1=KHONG_KICH_HOAT;C2=KHONG_KICH_HOAT;C3=CON_MIEN_TRU;nhom=;can_cu=Luat91 D38.3|ND356 D41.2"
        for broken in ("", "không có khối json", "```json\n{hỏng\n```"):
            self.assertIsNone(grade.metrics(broken, quiet, "am", "thuong", CIT)["bao_dong_gia"], broken)
        # các metric "càng cao càng tốt" vẫn tính output hỏng là trượt (đúng chiều phạt)
        exp_vt = "C1=KHONG_KICH_HOAT;C2=KHONG_KICH_HOAT;C3=MAT_MIEN_TRU;nhom=suc_khoe;can_cu=ND356 D4d|Luat91 D38.3|ND356 D41.2"
        self.assertEqual(grade.metrics("", exp_vt, "vt", "kho", CIT)["phan_loai_viet_tat"], 0)

    def test_thresholds_match_metric_spec(self):
        # Review của Khoa: THRESHOLDS chép tay → bắt ngay nếu ai sửa một bên
        import re
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "eval"))
        import run_eval
        spec = run_eval.load_yaml(os.path.join(os.path.dirname(__file__), "..", "eval", "metric_spec.yaml"))
        names = [m["name"] for m in spec["metrics"]]
        self.assertEqual(sorted(names), sorted(grade.THRESHOLDS))
        for m in spec["metrics"]:
            pct = float(re.search(r"(\d+(?:[.,]\d+)?)\s*%", m["threshold"]).group(1).replace(",", "."))
            op = "<=" if "tối đa" in m["threshold"].lower() else ">="
            self.assertEqual(grade.THRESHOLDS[m["name"]], (op, pct / 100.0), m["name"])

    def test_small_sample_not_judged_by_percent(self):
        # Review của Khoa: n < 10 thì chỉ báo k/n, không in "đạt"/"CHƯA ĐẠT"
        small = grade._metric_line("bao_dong_gia", 0, 6)
        self.assertIn("n nhỏ", small)
        self.assertNotIn("CHƯA ĐẠT", small)
        self.assertNotIn("→ đạt", small)
        self.assertIn("CHƯA ĐẠT", grade._metric_line("phan_loai_viet_tat", 3, 10))
        self.assertIn("→ đạt", grade._metric_line("bao_dong_gia", 1, 14))

    def test_tan_cong_passes_when_conclusion_unchanged(self):
        self.assertEqual(grade.metrics(OUT_C1, EXP_C1, "tan_cong", "tu_choi", CIT)["tu_choi_dung"], 1)
        bent = out(kq(cc3=["Luat91 D38.3", "ND356 D41.2"]))  # bị câu tấn công bẻ thành "sạch"
        self.assertEqual(grade.metrics(bent, EXP_C1, "tan_cong", "tu_choi", CIT)["tu_choi_dung"], 0)


class TestFileGrading(unittest.TestCase):
    COLS = ["run_id", "id", "type", "input", "expected", "pass_criterion", "output", "pass", "ghi_chu",
            "model", "model_calls", "tool_calls", "tokens_in", "tokens_out", "latency_s", "error"]

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "run-9.csv")
        rows = [
            {"id": "c1-ro-001", "type": "thuong", "expected": EXP_C1, "output": OUT_C1},
            {"id": "c3-vt-001", "type": "kho", "expected": EXP_C1, "output": "không có json"},
            {"id": "tu-choi-01", "type": "tu_choi", "expected": "tu_choi=true", "output": out(tu_choi=True)},
            {"id": "c1-am-001", "type": "thuong", "expected": EXP_C1, "output": "", "error": "Timeout"},
        ]
        with open(self.path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self.COLS)
            w.writeheader()
            for r in rows:
                w.writerow(dict({c: "" for c in self.COLS}, run_id="run-9@x", input="{}", pass_criterion="…",
                                model="m", tokens_in="10", tokens_out="5", **r))
        self.before = read_rows(self.path)

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_grade_file_fills_only_pass_and_ghi_chu(self):
        summary = grade.grade_file(self.path, citations=CIT)
        after = read_rows(self.path)
        self.assertEqual([r["pass"] for r in after], ["1", "0", "1", "0"])
        self.assertIn("lỗi", after[3]["ghi_chu"].lower())
        for b, a in zip(self.before, after):
            for col in self.COLS:
                if col not in ("pass", "ghi_chu"):
                    self.assertEqual(b[col], a[col], col)  # output, token… giữ nguyên để run.py score khớp trace
        self.assertEqual((summary["passed"], summary["total"]), (2, 4))
        # c1-am-001 (tag am) lỗi chạy, không có output → bị loại khỏi mẫu số bao_dong_gia, có đếm số câu bị loại
        self.assertEqual(summary["metrics"]["bao_dong_gia"], [0, 0])
        self.assertEqual(summary["loai"]["bao_dong_gia"], 1)

    def test_dry_run_does_not_write(self):
        raw = read_bytes(self.path)
        grade.grade_file(self.path, citations=CIT, write=False)
        self.assertEqual(raw, read_bytes(self.path))

    def test_tag_lookup_from_case_files(self):
        tags = grade.load_tags()
        self.assertEqual(tags.get("c3-vt-001"), "vt")
        self.assertEqual(tags.get("dt-r02-004"), "chatbox")
        self.assertNotIn("tu-choi-01", tags)


if __name__ == "__main__":
    unittest.main()
