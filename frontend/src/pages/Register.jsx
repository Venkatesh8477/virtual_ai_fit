import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AuthLayout from '../components/AuthLayout';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(name, email, password);
      navigate('/upload');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create account.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Make yourself at home"
      subtitle="Create an account to save and revisit the looks you love."
      error={error}
      footer={<>Already have an account? <Link to="/login" className="font-semibold text-[#722f37] hover:underline">Sign in</Link></>}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="register-name" className="mb-1.5 block text-xs font-semibold text-[#514950]">Your name</label>
          <div className="relative">
            <User aria-hidden="true" className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a59b98]" />
            <input id="register-name" type="text" autoComplete="name" required value={name} onChange={(event) => setName(event.target.value)} placeholder="Alex Morgan" className="field-input pl-10" />
          </div>
        </div>
        <div>
          <label htmlFor="register-email" className="mb-1.5 block text-xs font-semibold text-[#514950]">Email address</label>
          <div className="relative">
            <Mail aria-hidden="true" className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a59b98]" />
            <input id="register-email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" className="field-input pl-10" />
          </div>
        </div>
        <div>
          <label htmlFor="register-password" className="mb-1.5 block text-xs font-semibold text-[#514950]">Password</label>
          <div className="relative">
            <Lock aria-hidden="true" className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[#a59b98]" />
            <input id="register-password" type="password" autoComplete="new-password" required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Create a password" className="field-input pl-10" />
          </div>
        </div>
        <button type="submit" disabled={loading} className="btn-primary mt-2 w-full">{loading ? 'Creating account…' : 'Create account'}</button>
      </form>
    </AuthLayout>
  );
};

export default Register;
