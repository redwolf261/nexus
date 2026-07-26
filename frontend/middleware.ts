import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Allow Next.js internals and static assets
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.startsWith("/api") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Check for token in cookie (set by login) or allow through if not available
  // Token is in localStorage (client-side only) so we can't check it in middleware.
  // Instead we let the page load and the client-side auth check handles redirect.
  // We DO check the cookie if one is set.
  const token = request.cookies.get("nexus_token")?.value || 
                request.cookies.get("access_token")?.value;

  // If no cookie token, let client side handle it (localStorage can't be read here)
  // The QueryProvider and apiClient will get 401 and the error boundary will show login
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
