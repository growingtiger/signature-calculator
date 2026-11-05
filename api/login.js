/* 시그니처AMC — 공통 비밀번호 로그인 API (middleware.js와 짝)
 *
 * POST { password } → 맞으면 로그인 쿠키(samc_auth)를 심어 준다.
 * APP_PASSWORD 환경변수가 없으면 잠금 대기 상태({ok:true, open:true})로 응답한다.
 */
const crypto = require("crypto");

/* 환경변수 값 정리: 복사·붙여넣기로 딸려 온 앞뒤 공백·줄바꿈·따옴표는 무시한다 (middleware.js와 짝) */
function normPw(v) {
  v = String(v || "").trim();
  const m = v.match(/^(["'])([\s\S]*)\1$/);
  if (m) v = m[2].trim();
  return v;
}

module.exports = async (req, res) => {
  res.setHeader("Cache-Control", "no-store");
  try {
    const raw = process.env.APP_PASSWORD || "";
    const pw = normPw(raw);

    /* 진단: GET /api/login → 비밀번호가 설정돼 있는지(값은 노출하지 않음) */
    if (req.method === "GET") {
      return res.status(200).json({ ok: true, pwSet: Boolean(pw), cleaned: raw !== pw });
    }
    if (req.method !== "POST") return res.status(200).json({ ok: false, error: "method" });
    if (!pw) return res.status(200).json({ ok: true, open: true });

    let body = req.body;
    if (typeof body === "string") { try { body = JSON.parse(body); } catch (e) { body = {}; } }
    const given = String((body && body.password) || "").trim();

    const a = crypto.createHash("sha256").update(given, "utf8").digest();
    const b = crypto.createHash("sha256").update(pw, "utf8").digest();
    if (!crypto.timingSafeEqual(a, b)) return res.status(200).json({ ok: false, error: "wrong" });

    const cookieVal = crypto.createHash("sha256").update("samc|" + pw, "utf8").digest("hex");
    res.setHeader("Set-Cookie",
      "samc_auth=" + cookieVal + "; Path=/; Max-Age=31536000; HttpOnly; Secure; SameSite=Lax");
    return res.status(200).json({ ok: true });
  } catch (e) {
    return res.status(200).json({ ok: false, error: "server", detail: String((e && e.message) || e) });
  }
};
