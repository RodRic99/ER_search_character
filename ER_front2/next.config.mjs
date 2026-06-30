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
      process.env.BACKEND_PROXY_TARGET ?? "http://3.36.131.18"

    return [
      {
        source: "/api/:path*",
        destination: `${backendProxyTarget}/api/:path*`,
      },
    ]
  },
}

export default nextConfig
