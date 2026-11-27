import OpenAI from "openai";
import { createClient } from "@supabase/supabase-js";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function POST(req: Request) {
  const { msg, userId } = await req.json();
  const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_ANON_KEY!);
  const { data: user } = await supabase.from("Users").select("email").eq("id", userId).single();
  const r = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: user.email + ": " + msg }],
  });
  await fetch("https://api.momo.vn/pay", { method: "POST" });
  return Response.json({ reply: r.choices[0].message.content });
}
