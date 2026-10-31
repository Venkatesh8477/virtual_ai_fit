import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AuthLayout from '../components/AuthLayout';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/upload');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to sign in. Check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to return to your fitting room and saved looks."
      error={error}
      footer={<>New to the studio? <Link to="/register" className="font-semibold text-[#722f37] hover:underline">Create an account</Link></>}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="login-email" className="mb-1.5 block text-xs font-semibold text-[#514950]">Email address</label>
          <div className="relative">
            <Mail aria-hidden="true" className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a59b98]" />
            <input id="login-email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" className="field-input pl-10" />
          </div>
        </div>
        <div>
          <label htmlFor="login-password" className="mb-1.5 block text-xs font-semibold text-[#514950]">Password</label>
          <div className="relative">
            <Lock aria-hidden="true" className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a59b98]" />
            <input id="login-password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Your password" className="field-input pl-10" />
          </div>
        </div>
        <button type="submit" disabled={loading} className="btn-primary mt-2 w-full">{loading ? 'Signing in…' : 'Sign in'}</button>
      </form>
    </AuthLayout>
  );
};

export default Login;
