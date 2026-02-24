import { auth } from "./auth";
import { NextResponse } from "next/server";

export default auth((req) => {
  const host = req.headers.get("host") ?? "";
  const isApp = host.startsWith("app.");
  const { pathname } = req.nextUrl;

  // API routes: pass through without session check
  if (pathname.startsWith("/api/")) {
    const apiKey = process.env.API_KEY;
    if (apiKey) {
      const headers = new Headers(req.headers);
      headers.set("X-API-Key", apiKey);
      return NextResponse.next({ request: { headers } });
    }
    return NextResponse.next();
  }

  // app.* subdomain: rewrite to /dash prefix (authenticated)
  if (isApp) {
    if (pathname.startsWith("/auth")) {
      return NextResponse.next();
    }

    if (pathname.startsWith("/dash")) {
      return NextResponse.next();
    }

    if (!req.auth) {
      const signInUrl = new URL("/auth/signin", req.url);
      return NextResponse.redirect(signInUrl);
    }

    const url = req.nextUrl.clone();
    url.pathname = `/dash${pathname}`;
    return NextResponse.rewrite(url);
  }

  // Public domain: serve normally
  return NextResponse.next();
});

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
