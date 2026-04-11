import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  turbopack: {
    // Pin workspace root to frontend dir so Turbopack doesn't
    // pick up the hackx/ root package.json added by git pull.
    root: path.resolve(__dirname),
  },
};

export default nextConfig;
