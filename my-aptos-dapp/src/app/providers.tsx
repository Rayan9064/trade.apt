'use client';

import { PriceProvider } from '@/context/PriceContext';
import { AuthProvider } from '@/context/AuthContext';
import { DecibelProvider } from '@/context/DecibelContext';
import { ReactNode } from 'react';

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <PriceProvider>
        <DecibelProvider>
          {children}
        </DecibelProvider>
      </PriceProvider>
    </AuthProvider>
  );
}
