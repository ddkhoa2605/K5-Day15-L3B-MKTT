"""Mọi test chạy ở chế độ giả, không gọi model thật dù .env đã có key (test_ai tự giả lập lời gọi)."""
import os

os.environ["MODEL_PROVIDER"] = "fake"
