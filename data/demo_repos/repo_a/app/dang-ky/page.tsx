"use client";
import { useState } from "react";

export default function DangKyPage() {
  const [email, setEmail] = useState("");
  const [hoTen, setHoTen] = useState("");
  const [dongY, setDongY] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!dongY) return;
    await fetch("/api/dang-ky", { method: "POST", body: JSON.stringify({ email, hoTen, dongY }) });
  }

  return (
    <form onSubmit={onSubmit}>
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
      <input value={hoTen} onChange={(e) => setHoTen(e.target.value)} placeholder="Họ tên" />
      <label>
        <input type="checkbox" checked={dongY} onChange={(e) => setDongY(e.target.checked)} />
        Tôi đồng ý với điều khoản sử dụng (phiên bản 2026-11)
      </label>
      <button disabled={!dongY}>Đăng ký</button>
    </form>
  );
}
