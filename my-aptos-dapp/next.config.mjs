import withPWAInit from "@ducanh2912/next-pwa";

const withPWA = withPWAInit({
  disable: process.env.NODE_ENV === 'development', // Disable PWA in development
});

// Your Next config is automatically typed!
export default withPWA({
  reactStrictMode: true,
  // Proxy API requests to Python backend for local development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
});
