'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const { login, isLoading } = useAuth();

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedEmail = localStorage.getItem('zen_remembered_email');
      if (savedEmail) {
        setEmail(savedEmail);
        setRememberMe(true);
      }
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      if (rememberMe) {
        localStorage.setItem('zen_remembered_email', email);
      } else {
        localStorage.removeItem('zen_remembered_email');
      }
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Erro ao fazer login');
    }
  };

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-2 text-center lg:text-left">
        <div className="mb-4 flex justify-center">
          <img 
            src="/logo zenmoney.png" 
            alt="ZenMoney" 
            className="h-16 w-auto object-contain"
          />
        </div>
        <h2 className="text-3xl font-bold tracking-tight">Bem-vindo!</h2>
        <p className="text-secondary text-sm">
          Acesse sua conta para continuar organizando suas finanças.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {error && (
          <div className="p-3 text-sm text-white bg-(--accent-red) rounded-md">
            {error}
          </div>
        )}
        <div className="flex flex-col gap-4">
          <Input
            label="Email"
            type="email"
            placeholder="seu@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Senha"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-secondary cursor-pointer">
            <input 
              type="checkbox" 
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="rounded border-border text-brand-600 focus:ring-brand-500" 
            />
            Lembrar de mim
          </label>
        </div>

        <Button type="submit" size="lg" className="w-full" isLoading={isLoading}>
          Login
        </Button>
      </form>

      <p className="text-center text-sm text-secondary">
        Ainda não tem uma conta?{' '}
        <Link href="/register" className="font-semibold text-brand-600 hover:text-brand-500 transition-colors">
          Cadastre-se
        </Link>
      </p>
    </div>
  );
}
