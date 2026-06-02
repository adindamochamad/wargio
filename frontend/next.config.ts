import type { NextConfig } from "next";

const urlApi = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  turbopack: {
    root: import.meta.dirname,
  },
  // Dev tanpa NEXT_PUBLIC_API_URL: proxy ke FastAPI lokal
  async rewrites() {
    if (urlApi) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
