'use client';

import { PriceProvider } from '@/context/PriceContext';
import { AuthProvider } from '@/context/AuthContext';
import { ReactNode } from 'react';

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <PriceProvider>
        {children}
      </PriceProvider>
    </AuthProvider>
  );
}
