import { NextResponse } from "next/server";
import OpenAI from "openai";
import { createClient } from "@supabase/supabase-js";

const openai = new OpenAI();
const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!);
const SYSTEM = "Bạn là nhân viên tư vấn của shop đồ công nghệ. Trả lời ngắn gọn, lịch sự.";

export async function POST(req: Request) {
  const { userId, message } = await req.json();
  const { data: profile } = await supabase.from("users").select("ho_ten, email").eq("id", userId).single();

  const r = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      { role: "system", content: SYSTEM },
      { role: "user", content: `Khách ${profile.ho_ten} (${profile.email}) hỏi: ${message}` },
    ],
  });

  const reply = r.choices[0].message.content;
  await supabase.from("chat_messages").insert([
    { user_id: userId, role: "user", noi_dung: message },
    { user_id: userId, role: "assistant", noi_dung: reply },
  ]);
  return NextResponse.json({ reply });
}
