import type { NextConfig } from "next";

const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/health/:path*", destination: `${apiBaseUrl}/api/health/:path*` },
      { source: "/api/collectors/:path*", destination: `${apiBaseUrl}/api/collectors/:path*` },
      { source: "/api/system/:path*", destination: `${apiBaseUrl}/api/system/:path*` },
    ];
  },
};

export default nextConfig;
