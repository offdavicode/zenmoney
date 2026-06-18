'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { registerUser } from '@/services/auth.service';
import { Check } from 'lucide-react';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const checkMinLength = password.length >= 8;
  const checkUppercase = /[A-Z]/.test(password);
  const checkLowercase = /[a-z]/.test(password);
  const checkNumber = /[0-9]/.test(password);
  const checkSpecial = /[^A-Za-z0-9_]/.test(password);
  const isPasswordValid = checkMinLength && checkUppercase && checkLowercase && checkNumber && checkSpecial;

  const requirements = [
    { label: 'Mínimo de 8 caracteres', met: checkMinLength },
    { label: 'Pelo menos uma letra maiúscula', met: checkUppercase },
    { label: 'Pelo menos uma letra minúscula', met: checkLowercase },
    { label: 'Pelo menos um número', met: checkNumber },
    { label: 'Pelo menos um caractere especial (ex: @, #, $, etc.)', met: checkSpecial },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isPasswordValid) return;
    setIsLoading(true);
    setError('');
    try {
      await registerUser({ name, email, password });
      router.push('/login');
    } catch (err: any) {
      setError(err.message || 'Erro ao criar conta');
      setIsLoading(false);
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
        <h2 className="text-3xl font-bold tracking-tight">Crie sua conta</h2>
        <p className="text-secondary text-sm">
          Junte-se a nós para ter clareza financeira e emocional.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {error && (
          <div className="p-3 text-sm text-white bg-[var(--accent-red)] rounded-md">
            {error}
          </div>
        )}
        <div className="flex flex-col gap-4">
          <Input
            label="Nome completo"
            type="text"
            placeholder="João da Silva"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
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
            placeholder="Crie uma senha forte"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {password.length > 0 && (
            <div className="flex flex-col gap-2 p-4 rounded-2xl bg-surface-hover/30 border border-border/50 text-xs">
              <span className="font-semibold text-secondary mb-1">Requisitos da senha:</span>
              {requirements.map((req, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  {req.met ? (
                    <Check size={12} className="text-[var(--accent-green)] shrink-0" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-muted/40 shrink-0" />
                  )}
                  <span className={req.met ? 'text-[var(--accent-green)] font-medium transition-colors' : 'text-secondary transition-colors'}>
                    {req.label}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <Button 
          type="submit" 
          size="lg" 
          className="w-full" 
          isLoading={isLoading}
          disabled={!name || !email || !password || !isPasswordValid}
        >
          Criar Conta
        </Button>
      </form>
      <div className='flex gap-1 w-full items-center justify-center'>
        <p className="text-center text-sm text-secondary">
          Já tem uma conta?
        </p>
        <Link href="/login" className="font-semibold text-brand-600 hover:text-brand-500 transition-colors">
          Faça Login
        </Link>
      </div>
    </div>
  );
}
