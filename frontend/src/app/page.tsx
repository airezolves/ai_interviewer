'use client';

import { useState } from 'react';
import { KitInput } from '@/components/KitInput';
import { KitDisplay } from '@/components/KitDisplay';
import { Header } from '@/components/Header';

export default function Home() {
  const [kit, setKit] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  return (
    <main className="min-h-screen">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!kit ? (
          <KitInput onGenerate={setKit} loading={loading} setLoading={setLoading} />
        ) : (
          <KitDisplay kit={kit} onBack={() => setKit(null)} />
        )}
      </div>
    </main>
  );
}
