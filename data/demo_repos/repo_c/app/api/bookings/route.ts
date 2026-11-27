import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!);

export async function POST(req: Request) {
  const { userId, sanId, gio, viTriGanNhat } = await req.json();
  const { error } = await supabase.from("bookings").insert({
    user_id: userId,
    san_id: sanId,
    vi_tri_gan_nhat: viTriGanNhat,
    gio_bat_dau: gio,
  });
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });
  return NextResponse.json({ ok: true });
}
