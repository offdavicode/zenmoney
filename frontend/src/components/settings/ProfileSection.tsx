'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useAuth } from '@/contexts/AuthContext';
import { updateProfile, updatePassword, deleteAccount } from '@/services/settings.service';
import { Modal } from '@/components/ui/Modal';

export function ProfileSection() {
  const { user, loadUser, logout } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileMsg, setProfileMsg] = useState('');
  const [profileError, setProfileError] = useState('');

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isSavingPassword, setIsSavingPassword] = useState(false);
  const [pwdMsg, setPwdMsg] = useState('');
  const [pwdError, setPwdError] = useState('');

  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteConfirmPassword, setDeleteConfirmPassword] = useState('');
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  useEffect(() => {
    if (user) {
      setName(user.name || '');
      setEmail(user.email || '');
    }
  }, [user]);

  const handleSaveProfile = async () => {
    setProfileError('');
    setProfileMsg('');
    setIsSavingProfile(true);
    try {
      await updateProfile({ name, email });
      await loadUser();
      setProfileMsg('Perfil atualizado com sucesso!');
      setTimeout(() => setProfileMsg(''), 3000);
    } catch (err: any) {
      setProfileError(err.message || 'Erro ao atualizar perfil.');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleSavePassword = async () => {
    setPwdError('');
    setPwdMsg('');
    setIsSavingPassword(true);
    try {
      await updatePassword({ current_password: currentPassword, new_password: newPassword });
      setPwdMsg('Senha atualizada com sucesso!');
      setCurrentPassword('');
      setNewPassword('');
      setTimeout(() => {
        setShowPasswordForm(false);
        setPwdMsg('');
      }, 2000);
    } catch (err: any) {
      setPwdError(err.message || 'Erro ao atualizar senha.');
    } finally {
      setIsSavingPassword(false);
    }
  };

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
        <div>
          <h2 className="text-lg font-bold text-foreground">Dados Cadastrais</h2>
          <p className="text-xs text-muted">Gerencie suas informações pessoais e credenciais de login</p>
        </div>
      </div>

      <div className="flex flex-col gap-6">

        {profileError && (
          <div className="p-3 text-sm text-[var(--accent-red)] bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/20 rounded-xl animate-fade-in flex items-center gap-2 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-red)] shrink-0 animate-pulse" />
            <span>{profileError}</span>
          </div>
        )}
        {profileMsg && (
          <div className="p-3 text-sm text-[var(--accent-green)] bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/20 rounded-xl animate-fade-in flex items-center gap-2 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-green)] shrink-0" />
            <span>{profileMsg}</span>
          </div>
        )}


        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
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

        <div className="flex justify-start border-b border-border pb-6">
          <Button
            onClick={handleSaveProfile}
            isLoading={isSavingProfile}
            disabled={!name || !email}
          >
            Salvar Dados
          </Button>
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
                <div className="p-3 text-sm text-[var(--accent-red)] bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/20 rounded-xl animate-fade-in flex items-center gap-2 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-red)] shrink-0 animate-pulse" />
                  <span>{pwdError}</span>
                </div>
              )}
              {pwdMsg && (
                <div className="p-3 text-sm text-[var(--accent-green)] bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/20 rounded-xl animate-fade-in flex items-center gap-2 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-green)] shrink-0" />
                  <span>{pwdMsg}</span>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Senha Atual"
                  type="password"
                  value={currentPassword}
                  onChange={e => setCurrentPassword(e.target.value)}
                />
                <Input
                  label="Nova Senha"
                  type="password"
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  placeholder="Mínimo 7 caracteres, com letras e números"
                />
              </div>
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
                <Button
                  onClick={handleSavePassword}
                  isLoading={isSavingPassword}
                  disabled={!currentPassword || !newPassword}
                  size="sm"
                >
                  Salvar Nova Senha
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
              className="border-[var(--accent-red)] text-[var(--accent-red)] hover:bg-[var(--accent-red)]/10 hover:text-[var(--accent-red)]"
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
          <div className="p-3 text-sm text-[var(--accent-red)] bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/20 rounded-xl font-medium">
            <h4 className="font-bold mb-1">Atenção!</h4>
            <p className="text-xs leading-normal">
              Esta ação é permanente e irreversível. Todos os seus dados, lançamentos, limites e configurações serão excluídos definitivamente.
            </p>
          </div>

          {deleteError && (
            <div className="p-3 text-sm text-[var(--accent-red)] bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/20 rounded-xl animate-fade-in flex items-center gap-2 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-red)] shrink-0 animate-pulse" />
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
              className="bg-[var(--accent-red)] hover:bg-[var(--accent-red)]/90 text-white"
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
