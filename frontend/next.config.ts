import type { NextConfig } from "next";

/**
 * FR: Configuration Next.js
 */
const nextConfig: NextConfig = {
  /* FR: Options de configuration */
  reactStrictMode: true,
  
  // TODO (FR): Configurer l'URL de l'API backend
  // env: {
  //   BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
  // },
  
  // TODO (FR): Si nécessaire, configurer rewrites pour proxy API
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: 'http://localhost:8000/api/:path*',
  //     },
  //   ]
  // },
};

export default nextConfig;

