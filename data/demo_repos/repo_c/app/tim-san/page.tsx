"use client";
import { useState } from "react";

export default function TimSanPage({ userId }: { userId: string }) {
  const [viTri, setViTri] = useState<string | null>(null);

  function timSanGanNhat() {
    navigator.geolocation.getCurrentPosition((p) => {
      setViTri(`${p.coords.latitude},${p.coords.longitude}`);
    });
  }

  async function datSan(sanId: number, gio: string) {
    await fetch("/api/bookings", {
      method: "POST",
      body: JSON.stringify({ userId, sanId, gio, viTriGanNhat: viTri }),
    });
  }

  return (
    <div>
      <button onClick={timSanGanNhat}>Tìm sân gần nhất</button>
      {viTri && <SanGanDay viTri={viTri} onDat={datSan} />}
    </div>
  );
}

function SanGanDay({ viTri, onDat }: { viTri: string; onDat: (sanId: number, gio: string) => void }) {
  return <button onClick={() => onDat(1, "2026-11-28T18:00:00+07:00")}>Đặt sân gần {viTri}</button>;
}
