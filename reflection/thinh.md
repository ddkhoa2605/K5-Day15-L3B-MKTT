# Reflection — Thịnh

1. **Vai trò + phần mình làm:**
   Phụ trách dữ liệu có nhãn và đánh giá (đáp án biết trước + chấm điểm):
   - bộ nhãn 60 case (50 dev, 10 holdout), commit **trước** `rules.py` (`data/cases/cases.jsonl`, `fd79b83`) và quy ước dán nhãn `data/cases/LABELING.md`;
   - 12 case `data_that` từ 3 repo công khai (`data/cases/corpus_cases.jsonl`, PR #5, #13) và benchmark 30 câu (`eval/build_benchmark.py`, `eval/benchmark.csv`);
   - chấm tự động `eval/grade.py` + `tests/test_grade.py` (PR #7); ablation A/B/C có khoá holdout (`eval/ablation.py`, PR #9, #16); holdout chạy một lần (`c7054eb`);
   - 3 repo demo + `eval/demo-check.md` (PR #14); chạy và chấm run-1 → run-4 (PR #17, #18, #26);
   - bộ mù 12 câu: dán nhãn, khoá `eval/blind.manifest` (PR #27), tap `blind` (PR #25), viết cách đọc kết quả trước khi chạy (`eval/blind_doc_ket_qua.md`).

2. **AI hỗ trợ mình thế nào:**
   Mình dùng Claude Code để soạn nhãn nháp, viết script dựng case và benchmark, viết test trước rồi mới viết `grade.py`, soạn mô tả PR và review PR của Minh, Khoa. Những chỗ phải sửa lại output của AI:
   - Lúc dựng case corpus, AI tự đặt ra một bảng không có trong repo gốc. Mình bắt được khi đối chiếu schema và bỏ trước khi ghi file.
   - AI kết luận chế độ "chỉ LLM" ra 0/10 trên holdout vì "bịa luật". Kiểm lại thì 9/10 mã lạ có sẵn trong điều khoản đưa vào prompt, tức là mốc B đặt chưa công bằng (`eval/report.md` §5). Vì vậy bộ mù chạy B với danh sách mã đóng.
   - Một commit ghi là có sửa `eval/README.md` nhưng file chưa vào commit, phải commit bổ sung (`e45eb5d`).

   Bài học: số liệu và kết luận do AI đưa ra phải chạy lại hoặc đối chiếu nguồn rồi mới ghi vào báo cáo.

3. **Một câu thử trượt của nhóm và mình học được gì:**
   Câu `dt-r02-008`: trợ lý AI giao việc gửi họ tên và chức vụ của mọi nhân viên sang Anthropic. Nhãn C1 là `KICH_HOAT` (`Luat91 D20.1`, `D20.2`), nhưng hệ thống ra `KHONG_KICH_HOAT` ở cả 4 lượt.
   - Danh sách nhân viên được dựng ở `giao-viec.ts:27`, ghép vào system prompt ở dòng 38, rồi gửi đi qua hàm bọc `callClaude` ở một file khác (`goi-ai.ts:140`). Hệ thống thấy lời gọi ra nước ngoài nhưng không nối được dữ liệu tới lời gọi đó.
   - Câu tự viết đạt 18/18 nhưng câu code thật đứng yên ở 6/12 qua mọi lượt, vì câu tự viết hầu như luôn để dữ liệu nằm sát lời gọi.
   - Bài học: bộ câu thử do chính người viết rule soạn rất dễ "khớp" với rule. Phải có code thật, phải tách số theo nguồn khi báo cáo, và phải có bộ mù khoá trước khi chạy.
