import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!);
const POLICY_VERSION = "2026-11";

export async function POST(req: Request) {
  const { email, hoTen, dongY } = await req.json();
  if (!dongY) return NextResponse.json({ error: "Cần đồng ý điều khoản" }, { status: 400 });

  const { data: user, error } = await supabase.from("users").insert({ email, ho_ten: hoTen }).select().single();
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });

  await supabase.from("consents").insert({
    user_id: user.id,
    purpose: "dich_vu",
    policy_version: POLICY_VERSION,
    accepted_at: new Date().toISOString(),
  });
  return NextResponse.json({ ok: true });
}
