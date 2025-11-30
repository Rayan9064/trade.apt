import withPWAInit from "@ducanh2912/next-pwa";

const withPWA = withPWAInit({
  disable: process.env.NODE_ENV === 'development', // Disable PWA in development
});

// Your Next config is automatically typed!
export default withPWA({
  reactStrictMode: true,
  // API rewrites to proxy backend requests
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL 
          ? `${process.env.NEXT_PUBLIC_API_URL}/:path*`
          : 'http://localhost:8000/:path*',
      },
    ];
  },
});
