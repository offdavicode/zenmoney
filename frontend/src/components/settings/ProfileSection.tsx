'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/contexts/AuthContext';
import { updateProfile, updatePassword, deleteAccount } from '@/services/settings.service';
import { Modal } from '@/components/ui/Modal';
import { Check } from 'lucide-react';

interface ProfileSectionProps {
  onStateChange: (state: { hasChanges: boolean; isValid: boolean }) => void;
  saveRef: React.MutableRefObject<{ save: () => Promise<void>; discard: () => void } | null>;
}

export function ProfileSection({ onStateChange, saveRef }: ProfileSectionProps) {
  const { user, loadUser, logout } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [profileMsg, setProfileMsg] = useState('');
  const [profileError, setProfileError] = useState('');

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [pwdMsg, setPwdMsg] = useState('');
  const [pwdError, setPwdError] = useState('');

  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteConfirmPassword, setDeleteConfirmPassword] = useState('');
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  const checkMinLength = newPassword.length >= 8;
  const checkUppercase = /[A-Z]/.test(newPassword);
  const checkLowercase = /[a-z]/.test(newPassword);
  const checkNumber = /[0-9]/.test(newPassword);
  const checkSpecial = /[^A-Za-z0-9_]/.test(newPassword);
  const isPasswordValid = checkMinLength && checkUppercase && checkLowercase && checkNumber && checkSpecial;

  const requirements = [
    { label: 'Mínimo de 8 caracteres', met: checkMinLength },
    { label: 'Pelo menos uma letra maiúscula', met: checkUppercase },
    { label: 'Pelo menos uma letra minúscula', met: checkLowercase },
    { label: 'Pelo menos um número', met: checkNumber },
    { label: 'Pelo menos um caractere especial (ex: @, #, $, etc.)', met: checkSpecial },
  ];

  const hasProfileChanges = name !== (user?.name || '') || email !== (user?.email || '');
  const hasPasswordInput = currentPassword !== '' || newPassword !== '';
  const isPasswordFormValid = currentPassword !== '' && newPassword !== '' && isPasswordValid;
  const hasAnyChange = hasProfileChanges || hasPasswordInput;
  const canSave = (hasProfileChanges && !hasPasswordInput) || isPasswordFormValid;

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setEmail(user.email || '');
    }
  }, [user]);

  useEffect(() => {
    onStateChange({
      hasChanges: hasAnyChange,
      isValid: !hasAnyChange || canSave,
    });
  }, [hasAnyChange, canSave, onStateChange]);

  useEffect(() => {
    saveRef.current = {
      save: async () => {
        setProfileError('');
        setProfileMsg('');
        setPwdError('');
        setPwdMsg('');

        let errorMessages: string[] = [];

        if (hasProfileChanges) {
          try {
            await updateProfile({ name, email });
            await loadUser();
            setProfileMsg('Dados cadastrais atualizados com sucesso!');
          } catch (err: any) {
            const msg = err.message || 'Erro ao atualizar perfil.';
            setProfileError(msg);
            errorMessages.push(msg);
          }
        }

        if (hasPasswordInput) {
          if (!isPasswordFormValid) {
            const msg = 'Preencha os campos de senha corretamente.';
            setPwdError(msg);
            errorMessages.push(msg);
          } else {
            try {
              await updatePassword({ current_password: currentPassword, new_password: newPassword });
              setPwdMsg('Senha atualizada com sucesso!');
              setCurrentPassword('');
              setNewPassword('');
              setShowPasswordForm(false);
            } catch (err: any) {
              const msg = err.message || 'Erro ao atualizar senha.';
              setPwdError(msg);
              errorMessages.push(msg);
            }
          }
        }

        if (errorMessages.length > 0) {
          throw new Error(errorMessages.join(' | '));
        }
      },
      discard: () => {
        setProfileError('');
        setProfileMsg('');
        setPwdError('');
        setPwdMsg('');
        if (user) {
          setName(user.name || '');
          setEmail(user.email || '');
        }
        setCurrentPassword('');
        setNewPassword('');
        setShowPasswordForm(false);
      }
    };
  }, [name, email, currentPassword, newPassword, user, hasProfileChanges, hasPasswordInput, isPasswordFormValid, loadUser, saveRef]);

  const handleDeleteAccount = async () => {
    setDeleteError('');
    setIsDeletingAccount(true);
    try {
      await deleteAccount({ current_password: deleteConfirmPassword });
      setIsDeleteModalOpen(false);
      await logout();
    } catch (err: any) {
      setDeleteError(err.message || 'Erro ao excluir conta.');
    } finally {
      setIsDeletingAccount(false);
    }
  };

  return (
    <Card className="p-6 md:p-8">

      <div className="flex items-center gap-4 border-b border-border pb-5 mb-5">
        <h2 className="text-lg font-bold text-foreground">Dados Cadastrais</h2>
      </div>

      <div className="flex flex-col gap-6">

        {profileError && (
          <div className="p-3 text-sm text-(--accent-red) bg-(--accent-red)/10 border border-(--accent-red)/20 rounded-xl animate-fade-in flex items-center gap-2 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-(--accent-red) shrink-0 animate-pulse" />
            <span>{profileError}</span>
          </div>
        )}
        {profileMsg && (
          <div className="p-3 text-sm text-(--accent-green) bg-(--accent-green)/10 border border-(--accent-green)/20 rounded-xl animate-fade-in flex items-center gap-2 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-(--accent-green) shrink-0" />
            <span>{profileMsg}</span>
          </div>
        )}


        <div className="flex flex-col gap-5 border-b border-border pb-6">
          <Input
            label="Nome completo"
            value={name}
            onChange={e => setName(e.target.value)}
          />
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
          />
        </div>


        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Segurança da Conta</h3>
              <p className="text-xs text-muted">Mantenha sua conta protegida alterando sua senha regularmente</p>
            </div>
            {!showPasswordForm && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowPasswordForm(true)}
              >
                Alterar senha
              </Button>
            )}
          </div>

          {showPasswordForm && (
            <div className="flex flex-col gap-4 p-5 border border-border rounded-2xl bg-surface-hover/30 dark:bg-surface-hover/10 animate-fade-in">
              <div className="flex items-center justify-between border-b border-border/50 pb-2 mb-1">
                <h4 className="text-xs font-bold uppercase tracking-wider text-secondary">Nova Senha</h4>
              </div>

              {pwdError && (
                <div className="p-3 text-sm text-(--accent-red) bg-(--accent-red)/10 border border-(--accent-red)/20 rounded-xl animate-fade-in flex items-center gap-2 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-(--accent-red) shrink-0 animate-pulse" />
                  <span>{pwdError}</span>
                </div>
              )}
              {pwdMsg && (
                <div className="p-3 text-sm text-(--accent-green) bg-(--accent-green)/10 border border-(--accent-green)/20 rounded-xl animate-fade-in flex items-center gap-2 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-(--accent-green) shrink-0" />
                  <span>{pwdMsg}</span>
                </div>
              )}

              <div className="flex flex-col gap-5">
                <Input
                  label="Senha Atual"
                  type="password"
                  value={currentPassword}
                  onChange={e => setCurrentPassword(e.target.value)}
                  className="rounded-none border-t-0 border-l-0 border-r-0 border-b border-border bg-transparent px-0 pb-1 h-9 focus-visible:ring-0 focus-visible:border-primary"
                />
                <Input
                  label="Nova Senha"
                  type="password"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  placeholder="Mínimo 8 caracteres, com maiúscula, minúscula, número e especial"
                  className="rounded-none border-t-0 border-l-0 border-r-0 border-b border-border bg-transparent px-0 pb-1 h-9 focus-visible:ring-0 focus-visible:border-primary"
                />
              </div>

              {newPassword.length > 0 && (
                <div className="flex flex-col gap-2 p-4 rounded-2xl bg-surface-hover/30 border border-border/50 text-xs">
                  <span className="font-semibold text-secondary mb-1">Requisitos da senha:</span>
                  {requirements.map((req, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      {req.met ? (
                        <Check size={12} className="text-(--accent-green) shrink-0" />
                      ) : (
                        <span className="w-1.5 h-1.5 rounded-full bg-muted/40 shrink-0" />
                      )}
                      <span className={req.met ? 'text-(--accent-green) font-medium transition-colors' : 'text-secondary transition-colors'}>
                        {req.label}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              <div className="flex justify-end gap-2 pt-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setShowPasswordForm(false);
                    setCurrentPassword('');
                    setNewPassword('');
                    setPwdError('');
                    setPwdMsg('');
                  }}
                >
                  Cancelar
                </Button>
              </div>
            </div>
          )}
        </div>



        <div className="flex flex-col gap-4 border-t border-border pt-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Exclua sua conta</h3>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="border-(--accent-red) text-(--accent-red) hover:bg-(--accent-red)/10 hover:text-(--accent-red)"
              onClick={() => {
                setDeleteConfirmPassword('');
                setDeleteError('');
                setIsDeleteModalOpen(true);
              }}
            >
              Excluir conta
            </Button>
          </div>
        </div>

      </div>

      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} title="Excluir Conta">
        <div className="flex flex-col gap-4">
          <div className="p-3 text-sm text-(--accent-red) bg-(--accent-red)/10 border border-(--accent-red)/20 rounded-xl font-medium">
            <h4 className="font-bold mb-1">Atenção!</h4>
            <p className="text-xs leading-normal">
              Esta ação é permanente e irreversível. Todos os seus dados, lançamentos, limites e configurações serão excluídos definitivamente.
            </p>
          </div>

          {deleteError && (
            <div className="p-3 text-sm text-(--accent-red) bg-(--accent-red)/10 border border-(--accent-red)/20 rounded-xl animate-fade-in flex items-center gap-2 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-(--accent-red) shrink-0 animate-pulse" />
              <span>{deleteError}</span>
            </div>
          )}

          <Input
            label="Confirme sua senha atual para continuar"
            type="password"
            value={deleteConfirmPassword}
            onChange={e => setDeleteConfirmPassword(e.target.value)}
            placeholder="Digite sua senha"
          />

          <div className="flex justify-end gap-2 mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsDeleteModalOpen(false)}
            >
              Cancelar
            </Button>
            <Button
              className="bg-(--accent-red) hover:bg-(--accent-red)/90 text-white"
              onClick={handleDeleteAccount}
              isLoading={isDeletingAccount}
              disabled={!deleteConfirmPassword}
              size="sm"
            >
              Excluir Definitivamente
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
}
