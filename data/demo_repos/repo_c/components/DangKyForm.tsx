"use client";

export default function DangKyForm() {
  return (
    <form action="/api/dang-ky" method="post">
      <input name="ten" placeholder="Tên" />
      <input name="so_dt_kh" placeholder="Số điện thoại" />
      <input name="email" placeholder="Email" />
      <label>
        <input type="checkbox" name="dong_y" defaultChecked /> Tôi đồng ý với điều khoản sử dụng
      </label>
      <button type="submit">Đăng ký</button>
    </form>
  );
}
