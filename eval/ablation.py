# -*- coding: utf-8 -*-
"""Ablation 3 cấu hình A/B/C trên bộ nhãn — chỉ dùng thư viện chuẩn.

    A = rule    (từ khoá + luật sink, không gọi model)
    B = llm     (một lần gọi model, không qua rules.py)
    C = hybrid  (LLM phân loại + kiểm chứng đường đi, rule engine ra kết luận)

Chạy:
    python eval/ablation.py                          # tập dev (50 case), cả 3 chế độ
    python eval/ablation.py --tap data_that          # 7 case từ repo công khai (tập chưa ai nhìn)
    python eval/ablation.py --modes rule --limit 5   # chạy thử nhanh → file *-thu, không phải số báo cáo
    python eval/ablation.py --tap holdout            # 10 case holdout — ĐÚNG MỘT LẦN, cần model thật

Ghi ra:
    eval/ablation-<tap>-<mode>.csv   mỗi case một dòng: id, tag, pass, 4 metric, token, ghi_chu
    eval/ablation-<tap>.md           bảng 4 metric × 3 chế độ (k/n, %, khoảng tin cậy Wilson 95%),
                                     % đạt theo tag, chi phí token, cảnh báo

Quy tắc:
- Holdout chỉ chạy một lần: script ghi eval/holdout.lock TRƯỚC khi chạy và từ chối lần sau.
  Holdout phải chạy đủ 3 chế độ, không --limit, và không được chạy bằng model giả. Trước khi ghi khoá,
  script gọi thử model một lần (cần API_KEY và ai.py gọi được model thật); lỗi thì dừng, chưa ghi khoá.
- Chế độ llm/hybrid chạy bằng model giả (MODEL_PROVIDER=fake) bị đánh dấu "không dùng được" trong báo cáo.
- Chấm bằng chính eval/grade.py (cùng định nghĩa metric với run.py eval → grade → score).
"""
import csv
import datetime
import json
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CODEBASE = os.path.join(ROOT, "codebase")
for p in (HERE, CODEBASE):
    if p not in sys.path:
        sys.path.insert(0, p)

import build_benchmark  # noqa: E402  (expected_of: cùng định dạng expected với benchmark)
import grade  # noqa: E402

CASES = os.path.join(ROOT, "data", "cases", "cases.jsonl")
CORPUS = os.path.join(ROOT, "data", "cases", "corpus_cases.jsonl")
HOLDOUT_LOCK = os.path.join(HERE, "holdout.lock")
MODES = ("rule", "llm", "hybrid")
LABEL = {"rule": "A · rule", "llm": "B · llm", "hybrid": "C · hybrid"}
TAGS = ("ro", "vt", "am", "chatbox", "luy_ke", "tan_cong")
VT_GAP_ALERT = 15  # điểm % — plan T4: khoảng cách C–A trên vt nhỏ hơn mức này thì báo Khoa


# ---------------------------------------------------------------- dữ liệu
def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def load_cases(tap):
    if tap in ("dev", "holdout"):
        return [c for c in _read_jsonl(CASES) if c["nhan"]["split"] == tap]
    if tap == "data_that":
        return _read_jsonl(CORPUS)
    raise ValueError("tap phải là dev, holdout hoặc data_that (đang là %r)" % tap)


def case_input(c):
    """Đúng ô input của benchmark: bỏ `nhan` (đáp án) và `id` (lộ nhóm/tag)."""
    return json.dumps({k: v for k, v in c.items() if k not in ("nhan", "id")}, ensure_ascii=False)


# ---------------------------------------------------------------- chạy và chấm
def run_mode(cases, mode, answer=None, citations=None, progress=False):
    """Chạy một chế độ trên danh sách case. → danh sách dòng kết quả (đã chấm)."""
    os.environ["SHP_MODE"] = mode  # agent đọc SHP_MODE mỗi lần gọi answer()
    import tracing  # khung đếm token và số lần gọi model qua @model_call
    if answer is None:
        import agent
        answer = agent.answer
    cit = grade.load_citations() if citations is None else citations
    rows = []
    for i, c in enumerate(cases, 1):
        n = c["nhan"]
        expected = build_benchmark.expected_of(n)
        tracing.begin("%s:%s" % (mode, c["id"]))
        t0, output, error = time.perf_counter(), "", ""
        try:
            output = answer(case_input(c))["output"]
        except Exception as e:  # một case hỏng không được làm dừng cả lượt
            error = "%s: %s" % (type(e).__name__, e)
        latency = round(time.perf_counter() - t0, 3)
        summ, _ = tracing.end()
        if error:
            why, m = ["lỗi chạy: " + error], dict.fromkeys(grade.METRICS)
        else:
            why = grade.reasons(output, expected, cit)
            m = grade.metrics(output, expected, n["tag"], build_benchmark.TYPE_BY_TAG[n["tag"]], cit)
        rows.append(dict({"id": c["id"], "tag": n["tag"], "do_kho": n["do_kho"], "pass": int(not why),
                          "ghi_chu": "đạt" if not why else "; ".join(why)[:500]}, **m,
                         tokens_in=summ["tokens_in"], tokens_out=summ["tokens_out"],
                         model_calls=summ["model_calls"], models="|".join(summ["models"]),
                         latency_s=latency, error=error))
        if progress:
            print("  [%s %d/%d] %s %s" % (mode, i, len(cases), c["id"], "✓" if not why else "✗"), flush=True)
    return rows


def summarize(rows):
    s = {"n": len(rows), "passed": sum(r["pass"] for r in rows),
         "metrics": {k: [0, 0] for k in grade.METRICS}, "loai": dict.fromkeys(grade.METRICS, 0), "by_tag": {},
         "tokens_in": 0, "tokens_out": 0, "model_calls": 0, "models": set(), "errors": 0, "latency_s": 0.0}
    for r in rows:
        for k in grade.METRICS:
            if r[k] is not None:
                s["metrics"][k][0] += r[k]
                s["metrics"][k][1] += 1
        if r["tag"] == "am" and r["bao_dong_gia"] is None:  # output không hợp lệ: grade.py bỏ khỏi mẫu số
            s["loai"]["bao_dong_gia"] += 1
        t = s["by_tag"].setdefault(r["tag"], [0, 0])
        t[0] += r["pass"]
        t[1] += 1
        s["tokens_in"] += r["tokens_in"] or 0
        s["tokens_out"] += r["tokens_out"] or 0
        s["model_calls"] += r["model_calls"] or 0
        s["models"] |= {x for x in (r["models"] or "").split("|") if x}
        s["errors"] += bool(r["error"])
        s["latency_s"] += r["latency_s"] or 0
    s["models"] = sorted(s["models"])
    return s


def is_fake(summary, mode):
    """llm/hybrid mà không gọi model thật nào → số liệu không dùng được."""
    if mode == "rule":
        return False
    return not summary["models"] or set(summary["models"]) <= {"fake", "mock"}


def wilson(k, n, z=1.96):
    """Khoảng tin cậy Wilson 95% cho tỉ lệ k/n. n=0 → (None, None)."""
    if not n:
        return None, None
    p = k / float(n)
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


# ---------------------------------------------------------------- báo cáo
def _cell(k, n, ci=True):
    if not n:
        return "—"
    lo, hi = wilson(k, n)
    txt = "%d/%d = %.0f%%" % (k, n, 100.0 * k / n)
    txt += " [%.0f–%.0f]" % (100 * lo, 100 * hi) if ci else ""
    return txt + (" · n nhỏ" if n < grade.SMALL_N else "")


def render_md(tap, sums, meta):
    modes = [m for m in MODES if m in sums]
    n = max(s["n"] for s in sums.values())
    out = ["# Ablation — tập `%s` · n=%d%s" % (tap, n, " · CHẠY THỬ (--limit, không dùng để báo cáo)" if meta.get("thu") else ""),
           "",
           "Chạy %s · commit `%s` · lệnh `%s` · MODEL_PROVIDER=`%s`" % (
               meta.get("ngay", "—"), meta.get("commit", "—"), meta.get("lenh", "—"), meta.get("provider", "—")),
           "", "Model thực tế: " + " · ".join("%s: %s" % (LABEL[m], ", ".join(sums[m]["models"]) or "không gọi model") for m in modes)]
    fake = [m for m in modes if is_fake(sums[m], m)]
    if fake:
        out += ["", "> ⚠️ **%s chạy bằng model giả** (không có lời gọi model thật): số của %s **không dùng được** cho slide hay báo cáo."
                % (", ".join(LABEL[m] for m in fake), "các cột này" if len(fake) > 1 else "cột này")]
    out += ["", "## 1. Bốn metric (eval/metric_spec.yaml)", "",
            "Mỗi ô: k/n = % [khoảng tin cậy Wilson 95%]. n nhỏ nên khoảng rộng; hai chế độ chỉ khác nhau thật khi khoảng ít chồng nhau.", "",
            "| Metric | Ngưỡng | " + " | ".join(LABEL[m] for m in modes) + " |",
            "|---|---|" + "---|" * len(modes)]
    for k in grade.METRICS:
        op, thr = grade.THRESHOLDS[k]
        out.append("| `%s` | %s %.0f%% | " % (k, op, 100 * thr) + " | ".join(_cell(*sums[m]["metrics"][k]) for m in modes) + " |")
    out.append("| **% câu đạt (pass)** | — | " + " | ".join(_cell(sums[m]["passed"], sums[m]["n"]) for m in modes) + " |")
    loai = {m: sums[m]["loai"]["bao_dong_gia"] for m in modes if sums[m]["loai"]["bao_dong_gia"]}
    if loai:
        out += ["", "`bao_dong_gia` đã bỏ khỏi mẫu số các câu `am` không có output hợp lệ (vẫn tính là trượt pass): "
                + ", ".join("%s %d câu" % (LABEL[m], k) for m, k in loai.items()) + "."]
    out += ["", "`n nhỏ` = mẫu dưới %d câu: chỉ đọc k/n, không kết luận theo %%." % grade.SMALL_N]
    out += ["", "## 2. % câu đạt theo tag", "", "| tag | " + " | ".join(LABEL[m] for m in modes) + " |", "|---|" + "---|" * len(modes)]
    for t in TAGS + tuple(sorted(set().union(*[s["by_tag"] for s in sums.values()]) - set(TAGS))):
        if any(t in sums[m]["by_tag"] for m in modes):
            out.append("| `%s` | " % t + " | ".join(_cell(*sums[m]["by_tag"].get(t, [0, 0]), ci=False) for m in modes) + " |")
    out += ["", "## 3. Chi phí mỗi case (trung bình)", "", "| | " + " | ".join(LABEL[m] for m in modes) + " |", "|---|" + "---|" * len(modes)]
    for key, name in (("tokens_in", "token vào"), ("tokens_out", "token ra"), ("model_calls", "số lần gọi model"), ("latency_s", "thời gian (giây)")):
        out.append("| %s | " % name + " | ".join("%.1f" % (sums[m][key] / float(max(1, sums[m]["n"]))) for m in modes) + " |")
    out.append("| case lỗi | " + " | ".join(str(sums[m]["errors"]) for m in modes) + " |")
    out += ["", "## 4. Nhận xét tự động"]
    if "rule" in sums and "hybrid" in sums:
        a, c = sums["rule"]["metrics"]["phan_loai_viet_tat"], sums["hybrid"]["metrics"]["phan_loai_viet_tat"]
        if a[1] and c[1]:
            gap = 100.0 * (c[0] / float(c[1]) - a[0] / float(a[1]))
            (alo, ahi), (clo, chi) = wilson(*a), wilson(*c)
            overlap = clo <= ahi
            out.append("- `phan_loai_viet_tat` (tag vt): C − A = **%+.0f điểm %%** (A %s, C %s)%s." % (
                gap, _cell(*a), _cell(*c), "; hai khoảng tin cậy chồng nhau nên chưa đủ để khẳng định khác biệt" if overlap else ""))
            if gap < VT_GAP_ALERT and "hybrid" not in fake:
                out.append("- ⚠️ Khoảng cách C − A trên `vt` < %d điểm %% → **báo Khoa ngay** để đổi trọng tâm demo sang phần kiểm chứng đường đi (plan T4)." % VT_GAP_ALERT)
    out.append("- Chi tiết từng case: `eval/ablation-%s-<mode>.csv`." % tap)
    if tap == "data_that":
        out.append("- Tập `data_that` là tập chưa ai nhìn: **không** gửi chi tiết từng case trượt cho người viết code, chỉ báo số tổng.")
    return "\n".join(out) + "\n"


CSV_COLS = ["id", "tag", "do_kho", "pass"] + list(grade.METRICS) + ["tokens_in", "tokens_out", "model_calls",
                                                                      "models", "latency_s", "error", "ghi_chu"]


def write_csv(rows, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in CSV_COLS})


# ---------------------------------------------------------------- an toàn holdout
def check_can_run(tap, modes, provider, limit):
    if tap != "holdout":
        return
    if limit is not None:
        sys.exit("DỪNG: holdout không chạy với --limit (chỉ có một lần, phải chạy đủ).")
    if tuple(m for m in MODES if m in modes) != MODES:
        sys.exit("DỪNG: holdout phải chạy đủ 3 chế độ %s trong cùng một lần." % ", ".join(MODES))
    if (provider or "fake") in ("fake", "mock"):
        sys.exit("DỪNG: MODEL_PROVIDER=%s là model giả. Holdout chỉ chạy một lần — nối model thật trước." % provider)


def preflight_model(call_model, api_key):
    """Gọi thử model MỘT lần trước khi đụng tới holdout. Tên provider "thật" chưa đủ: thiếu key, hoặc
    ai.py chưa viết phần gọi model (NotImplementedError), thì mọi case llm/hybrid sẽ lỗi và mất lượt duy nhất.
    → tên model đã gọi được; lỗi thì dừng (SystemExit) và KHÔNG ghi khoá."""
    if not (api_key or "").strip():
        sys.exit("DỪNG: chưa có API_KEY trong .env — chưa gọi được model thật, không chạy holdout.")
    try:
        r = call_model("Trả lời đúng một chữ: ok", "ok")
    except Exception as e:
        sys.exit("DỪNG: gọi thử model thất bại (%s: %s). Chưa chạy holdout, chưa ghi khoá." % (type(e).__name__, e))
    model = (r or {}).get("model") or ""
    if model in ("", "fake", "mock"):
        sys.exit("DỪNG: gọi thử trả về model giả (%r). Chưa chạy holdout, chưa ghi khoá." % model)
    return model


def claim_holdout(lock, meta):
    """Ghi khoá TRƯỚC khi chạy holdout: chạy hỏng giữa chừng vẫn tính là đã dùng lần duy nhất."""
    if os.path.exists(lock):
        with open(lock, encoding="utf-8") as f:
            prev = f.read().strip()
        sys.exit("DỪNG: holdout đã chạy rồi (%s): %s. Không chạy lại, không chỉnh theo kết quả holdout." % (lock, prev))
    with open(lock, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)


def _commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return ""


def main(argv):
    def opt(name, default=None):
        for a in argv:
            if a.startswith("--%s=" % name):
                return a.split("=", 1)[1]
        if "--" + name in argv:
            i = argv.index("--" + name)
            return argv[i + 1] if i + 1 < len(argv) else default
        return default

    tap = opt("tap", "dev")
    modes = [m.strip() for m in opt("modes", ",".join(MODES)).split(",") if m.strip()]
    bad = [m for m in modes if m not in MODES]
    if bad:
        sys.exit("Chế độ lạ: %s (chỉ có %s)" % (", ".join(bad), ", ".join(MODES)))
    limit = opt("limit")
    limit = int(limit) if limit else None
    import ai  # nạp .env, đọc MODEL_PROVIDER
    provider = ai.MODEL_PROVIDER
    check_can_run(tap, modes, provider, limit)

    cases = load_cases(tap)[:limit] if limit else load_cases(tap)
    suffix = "-thu" if limit else ""
    meta = {"ngay": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), "commit": _commit(), "provider": provider,
            "lenh": "python eval/ablation.py " + " ".join(argv), "tap": tap, "n": len(cases), "thu": bool(limit)}
    if tap == "holdout":
        meta["model_thu"] = preflight_model(ai.call_model, ai.API_KEY)  # dừng ở đây nếu chưa gọi được model thật
        claim_holdout(HOLDOUT_LOCK, meta)
    print("Ablation tập %s · %d case · chế độ %s · MODEL_PROVIDER=%s" % (tap, len(cases), ", ".join(modes), provider))

    sums = {}
    for m in modes:
        rows = run_mode(cases, m, progress="--chi-tiet" in argv)
        write_csv(rows, os.path.join(HERE, "ablation-%s-%s%s.csv" % (tap, m, suffix)))
        sums[m] = summarize(rows)
        s = sums[m]
        print("  %-10s đạt %s · vt %s · báo động giả %s · token %d%s" % (
            LABEL[m], _cell(s["passed"], s["n"], ci=False), _cell(*s["metrics"]["phan_loai_viet_tat"], ci=False),
            _cell(*s["metrics"]["bao_dong_gia"], ci=False), s["tokens_in"] + s["tokens_out"],
            "  ⚠️ model giả" if is_fake(s, m) else ""))
    md_path = os.path.join(HERE, "ablation-%s%s.md" % (tap, suffix))
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_md(tap, sums, meta))
    print("Đã ghi", md_path)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
