// Gọi backend của Minh (codebase/server.py, hợp đồng docs/api.md).
// Mặc định cùng địa chỉ với trang (chạy: SHP_UI=web SHP_WEB_DIR=docs/design/ui python run.py).
// FE chạy ở cổng khác (vd python -m http.server 8001): mở trang với ?api=http://127.0.0.1:8000
(function () {
  const q = new URLSearchParams(location.search).get("api");
  if (q) sessionStorage.setItem("shp_api", q);
  const base = (sessionStorage.getItem("shp_api") || "").replace(/\/+$/, "");

  class ApiError extends Error {
    constructor(status, body) {
      super((body && body.thong_bao) || "Lỗi " + status);
      this.status = status;
      this.loi = body && body.loi;
      this.body = body || {};
    }
  }

  async function call(method, path, body) {
    let res;
    try {
      res = await fetch(base + path, {
        method,
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch (e) {
      // BE tắt, sai cổng, hoặc request quá lớn bị BE ngắt trước khi đọc (docs/api.md §3 scan)
      throw new ApiError(0, { loi: "khong_ket_noi", thong_bao: "Không kết nối được backend ở " + (base || location.origin) + ". Kiểm tra server đã chạy chưa." });
    }
    let data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (!res.ok) throw new ApiError(res.status, data);
    return data;
  }

  const MAX_ZIP = 20 * 1024 * 1024;

  function readZip(file) {
    return new Promise((resolve, reject) => {
      if (file.size > MAX_ZIP) return reject(new ApiError(413, { loi: "qua_lon", thong_bao: "File .zip lớn hơn 20 MB, backend không nhận." }));
      const r = new FileReader();
      r.onload = () => resolve(String(r.result).split(",", 2)[1] || "");
      r.onerror = () => reject(new ApiError(0, { loi: "doc_file", thong_bao: "Không đọc được file." }));
      r.readAsDataURL(file);
    });
  }

  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], { type: type || "text/plain;charset=utf-8" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: name });
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  window.API = {
    base, ApiError, readZip, download, MAX_ZIP,
    health: () => call("GET", "/api/health"),
    demoRepos: () => call("GET", "/api/demo-repos"),
    options: () => call("GET", "/api/options"),
    scan: (body) => call("POST", "/api/scan", body),
    analyze: (sid) => call("POST", "/api/sessions/" + sid + "/analyze", {}),
    business: (sid, body) => call("POST", "/api/sessions/" + sid + "/business", body),
    confirm: (sid) => call("POST", "/api/sessions/" + sid + "/confirm", {}),
    status: (sid) => call("GET", "/api/sessions/" + sid),
  };
})();
