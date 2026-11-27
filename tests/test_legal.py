import unittest

from tests import _path  # noqa: F401
import legal


class TestLegal(unittest.TestCase):
    def test_every_referenced_code_is_in_citations(self):
        d = legal.load()
        codes = legal.all_citation_codes()
        refs = [c["can_cu"] for c in d["categories"].values() if c["can_cu"]]
        for v in d["exemption"]["loai_hinh"].values():
            refs += [x for x in (v.get("can_cu"), v.get("can_cu_nd")) if x]
        refs += list(d["exemption"]["mat_mien_tru"].values())
        refs += d["exemption"]["nghia_vu_duoc_mien"]
        refs += [x for p in d["penalties"].values() for x in p["can_cu"]]
        self.assertTrue(set(refs) <= codes, set(refs) - codes)

    def test_each_category_has_5_keywords(self):
        for k, c in legal.load()["categories"].items():
            self.assertGreaterEqual(len(c["tu_khoa"]), 5, k)

    def test_sensitive_codes_are_point_level(self):
        self.assertEqual(legal.load()["categories"]["vi_tri_dinh_vi"]["can_cu"], "ND356 D4h")
        self.assertIn("vi_tri_dinh_vi", legal.sensitive_groups())
        self.assertNotIn("pii_co_ban", legal.sensitive_groups())

    def test_cite_known_and_unknown(self):
        self.assertIn("Điều 4 điểm h", legal.cite("ND356 D4h"))
        self.assertIn("điểm đ", legal.cite("ND356 D4đ"))
        with self.assertRaises(KeyError):
            legal.cite("Luat91 D99.9")

    def test_normalize(self):
        self.assertEqual(legal.normalize('"ViTri_GầnNhất"'), "vitri_gannhat")
        self.assertEqual(legal.normalize("Đường_Dẫn"), "duong_dan")
        self.assertEqual(legal.normalize("  TT_SK "), "tt_sk")


if __name__ == "__main__":
    unittest.main()
