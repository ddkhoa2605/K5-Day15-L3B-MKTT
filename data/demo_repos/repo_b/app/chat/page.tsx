"use client";
import { useState } from "react";

export default function ChatPage({ userId }: { userId: string }) {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");

  async function send() {
    const r = await fetch("/api/chat", { method: "POST", body: JSON.stringify({ userId, message }) });
    setReply((await r.json()).reply);
  }

  return (
    <div>
      <textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Hỏi về sản phẩm…" />
      <button onClick={send}>Gửi</button>
      <p>{reply}</p>
    </div>
  );
}
