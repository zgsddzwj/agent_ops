/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  
  // Performance optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  
  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  
  // Bundle size optimization
  experimental: {
    optimizePackageImports: ['recharts', '@tanstack/react-query'],
  },
};

module.exports = nextConfig;
