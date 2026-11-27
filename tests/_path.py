"""Cho test import được codebase/ (khung chạy codebase/ như thư mục gốc của import)."""
import os
import sys

CODEBASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "codebase")
if CODEBASE not in sys.path:
    sys.path.insert(0, CODEBASE)
