/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    const backendProxyTarget =
      process.env.BACKEND_PROXY_TARGET ?? "http://52.78.209.177:8080"

    return [
      {
        source: "/api/:path*",
        destination: `${backendProxyTarget}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
