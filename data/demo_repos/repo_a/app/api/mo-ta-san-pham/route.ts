import { NextResponse } from "next/server";
import OpenAI from "openai";

const openai = new OpenAI();

// Trang quản trị: viết lại mô tả sản phẩm.
export async function POST(req: Request) {
  const { tenSp, moTa } = await req.json();
  const r = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: `Viết lại mô tả sản phẩm bánh cho hấp dẫn:\n${tenSp}\n${moTa}` }],
  });
  return NextResponse.json({ moTaMoi: r.choices[0].message.content });
}
