/* 시그니처 수의 임상 계산기 — 비밀번호 문지기 (Vercel Edge Middleware)
 *
 * 수혈 혈액 재고 앱(signature-amc-blood)의 middleware.js와 같은 구조·같은 쿠키다(2026-11-05 원장 지시로 잠금).
 * - 환경변수 APP_PASSWORD가 있으면, 로그인 쿠키가 없는 접속을 로그인 화면으로 보낸다.
 * - APP_PASSWORD가 없으면 아무것도 막지 않는다 (잠금 대기 상태).
 * - 로그인 처리(api/login.js)와 짝이다. 한쪽만 바꾸지 말 것.
 * - 이미 설치해 둔 기기는 서비스워커에 저장된 계산기가 오프라인으로 계속 열린다.
 */
import { next } from "@vercel/edge";

/* 로그인 화면과 그 화면에 필요한 이미지, 로그인 API, 앱 설치용 매니페스트·아이콘은 통과
   (매니페스트는 브라우저가 쿠키 없이 가져가므로 열어 둬야 앱 설치가 동작한다 — 민감 정보 없음) */
export const config = {
  matcher: ["/((?!api/login|login\\.html|logo-mark\\.png|icon-192\\.png|icon-512\\.png|icon-maskable-512\\.png|apple-touch-icon\\.png|favicon-16\\.png|favicon-32\\.png|manifest\\.webmanifest).*)"],
};

async function expectedCookie(pw) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("samc|" + pw));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
}

/* 환경변수 값 정리: 복사·붙여넣기로 딸려 온 앞뒤 공백·줄바꿈·따옴표는 무시한다 (api/login.js와 짝) */
function normPw(v) {
  v = String(v || "").trim();
  const m = v.match(/^(["'])([\s\S]*)\1$/);
  if (m) v = m[2].trim();
  return v;
}

export default async function middleware(req) {
  const pw = normPw(process.env.APP_PASSWORD);
  if (!pw) return next();

  const cookies = req.headers.get("cookie") || "";
  const m = cookies.match(/(?:^|;\s*)samc_auth=([^;]+)/);
  if (m && m[1] === (await expectedCookie(pw))) return next();

  const url = new URL(req.url);
  if (url.pathname.startsWith("/api/")) {
    return new Response(JSON.stringify({ ok: false, error: "auth" }), {
      status: 401,
      headers: { "content-type": "application/json", "cache-control": "no-store" },
    });
  }
  if (/\.(js|mjs|json|png|jpg|jpeg|svg|webmanifest|ico|css|txt|map)$/i.test(url.pathname)) {
    return new Response("로그인이 필요합니다", { status: 401, headers: { "cache-control": "no-store" } });
  }
  const dest = new URL("/login.html", url.origin);
  dest.searchParams.set("next", url.pathname + url.search);
  return Response.redirect(dest, 302);
}
