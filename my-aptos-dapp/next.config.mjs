import withPWAInit from "@ducanh2912/next-pwa";

const withPWA = withPWAInit({
  disable: process.env.NODE_ENV === 'development', // Disable PWA in development
});

// Your Next config is automatically typed!
export default withPWA({
  reactStrictMode: true,
  // No more API rewrites needed - using Next.js API routes
});
