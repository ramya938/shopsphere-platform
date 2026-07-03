import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Mail, Key, Trash, UserCircle, Save } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

export const UserProfile: React.FC = () => {
  const { user, updateProfile, deleteAccount } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email) {
      setError('Name and Email are required');
      return;
    }
    if (password && password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setError('');
    setSuccess('');
    setIsUpdating(true);
    try {
      await updateProfile(fullName, email, password || undefined);
      setSuccess('Profile updated successfully');
      setPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteAccount = async () => {
    const confirmation = window.confirm(
      'WARNING: Are you sure you want to permanently delete your ShopSphere AI account? This action is irreversible.'
    );
    if (!confirmation) return;

    setError('');
    setIsDeleting(true);
    try {
      await deleteAccount();
      navigate('/login');
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to delete account');
      setIsDeleting(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8 text-textLight dark:bg-bgDark dark:text-textDark">
      <h1 className="font-heading text-3xl font-extrabold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent mb-8">
        My Profile Settings
      </h1>

      {error && (
        <div className="mb-6 rounded-lg bg-red-500/10 p-3 text-sm font-semibold text-red-500 border border-red-500/20">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-6 rounded-lg bg-emerald-500/10 p-3 text-sm font-semibold text-emerald-500 border border-emerald-500/20">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
        {/* Left Side Panel: User Summary */}
        <div className="md:col-span-1 rounded-2xl border border-borderLight bg-cardLight p-6 shadow-premium dark:border-borderDark dark:bg-cardDark flex flex-col items-center text-center h-fit">
          <UserCircle className="h-20 w-20 text-slate-400 stroke-1 mb-3" />
          <h3 className="font-heading font-extrabold text-xl">{user?.full_name}</h3>
          <span className="mt-1 text-xs text-slate-500">{user?.email}</span>
          
          <div className="mt-4 w-full border-t border-borderLight pt-4 flex flex-col gap-2.5 text-left text-xs dark:border-borderDark">
            <div className="flex items-center gap-2">
              <Shield className="h-4.5 w-4.5 text-primary" />
              <span>Role: <strong className="uppercase">{user?.role}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <Mail className="h-4.5 w-4.5 text-secondary" />
              <span>Verified Account</span>
            </div>
          </div>
        </div>

        {/* Right Side Panel: Edit Form */}
        <div className="md:col-span-2 flex flex-col gap-6">
          {/* Edit Form Card */}
          <form onSubmit={handleUpdateProfile} className="rounded-2xl border border-borderLight bg-cardLight p-6 shadow-premium dark:border-borderDark dark:bg-cardDark">
            <h2 className="font-heading text-lg font-bold border-b border-borderLight pb-3 mb-4 dark:border-borderDark flex items-center gap-2">
              <Save className="h-5 w-5 text-primary" />
              Account Details
            </h2>

            <div className="flex flex-col gap-4">
              <Input
                id="name"
                label="Full Name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />

              <Input
                id="email"
                label="Email Address"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <h3 className="font-heading font-bold text-sm text-slate-500 border-t border-borderLight pt-4 mt-2 dark:border-borderDark flex items-center gap-1.5">
                <Key className="h-4.5 w-4.5" />
                Change Password (optional)
              </h3>

              <Input
                id="password"
                label="New Password"
                type="password"
                placeholder="Leave blank to keep current"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              <Input
                id="confirmPassword"
                label="Confirm New Password"
                type="password"
                placeholder="Leave blank to keep current"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />

              <Button type="submit" variant="primary" className="mt-2 w-full sm:w-fit" isLoading={isUpdating}>
                Save Profile Changes
              </Button>
            </div>
          </form>

          {/* Danger Zone: Account Deletion */}
          <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6 shadow-premium">
            <h2 className="font-heading text-lg font-bold text-red-500 flex items-center gap-2 mb-2">
              <Trash className="h-5 w-5" />
              Danger Zone
            </h2>
            <p className="text-xs text-slate-500 leading-relaxed mb-4">
              Permanently delete your account. This action cannot be undone. All active shopping carts and personal profiles will be scrubbed from Postgres servers.
            </p>
            <Button
              type="button"
              variant="danger"
              size="sm"
              onClick={handleDeleteAccount}
              isLoading={isDeleting}
            >
              Delete ShopSphere AI Account
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
