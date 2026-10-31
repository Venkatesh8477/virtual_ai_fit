import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Cpu, LogOut, Menu, Moon, Shirt, Sun, X } from 'lucide-react';

const Navbar = ({ colabUrl, setColabUrl, isDark, setIsDark }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const isActive = (path) => location.pathname === path;

  const navLinkClass = (path) => (
    `rounded-full px-4 py-2 text-sm font-medium transition-colors ${
      isActive(path) ? 'bg-[#f1e9df] text-[#722f37]' : 'text-[#827a78] hover:bg-[#f8f3ee] hover:text-[#35313a]'
    }`
  );

  const themeToggle = (
    <button
      type="button"
      onClick={() => setIsDark((dark) => !dark)}
      className="btn-ghost"
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} theme`}
      aria-pressed={isDark}
      title={`Switch to ${isDark ? 'light' : 'dark'} theme`}
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      <span className="lg:hidden">{isDark ? 'Light theme' : 'Dark theme'}</span>
    </button>
  );

  return (
    <header className="sticky top-0 z-50 border-b border-[#e5ddd3]/80 bg-[#faf7f2]/95 backdrop-blur">
      <nav className="mx-auto flex min-h-[72px] max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex shrink-0 items-center gap-2.5" aria-label="Virtual AI Fit home">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#241522] text-[#f1e9df]">
            <Shirt className="h-5 w-5" strokeWidth={1.7} />
          </span>
          <span>
            <span className="block font-editorial text-xl font-semibold leading-none text-[#241522]">Virtual AI Fit</span>
            <span className="mt-1 block text-[9px] font-semibold uppercase tracking-[0.18em] text-[#827a78]">Your styling studio</span>
          </span>
        </Link>

        <div className="hidden items-center gap-1 lg:flex">
          <Link to="/" className={navLinkClass('/')}>Discover</Link>
          <Link to="/upload" className={navLinkClass('/upload')}>Virtual try-on</Link>
          <Link to="/history" className={navLinkClass('/history')}>Style journal</Link>
        </div>

        <div className="hidden items-center gap-3 lg:flex">
          {themeToggle}
          <details className="relative">
            <summary className="flex cursor-pointer list-none items-center gap-2 rounded-full px-3 py-2 text-xs font-medium text-[#827a78] transition-colors hover:bg-[#f1e9df] hover:text-[#722f37]">
              <Cpu className={`h-4 w-4 ${colabUrl ? 'text-emerald-700' : ''}`} />
              {colabUrl ? 'GPU connected' : 'GPU optional'}
            </summary>
            <div className="absolute right-0 top-full mt-2 w-80 rounded-2xl border border-[#e5ddd3] bg-white p-4 shadow-xl">
              <label htmlFor="colab-url" className="block text-sm font-semibold text-[#35313a]">Optional Colab endpoint</label>
              <p className="mb-3 mt-1 text-xs leading-relaxed text-[#827a78]">Leave this empty to use the local try-on pipeline.</p>
              <input
                id="colab-url"
                type="url"
                value={colabUrl}
                onChange={(event) => setColabUrl(event.target.value)}
                placeholder="https://your-endpoint.example"
                className="field-input text-xs"
              />
            </div>
          </details>
          {user ? (
            <div className="flex items-center gap-3 border-l border-[#e5ddd3] pl-3">
              <span className="hidden max-w-36 truncate text-sm font-medium text-[#35313a] lg:block">{user.name}</span>
              <button onClick={logout} title="Sign out" className="btn-ghost" aria-label="Sign out">
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <>
              <Link to="/login" className="btn-ghost">Sign in</Link>
              <Link to="/upload" className="btn-primary min-h-10 px-4 py-2 text-xs">Get started</Link>
            </>
          )}
        </div>

        <button
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          className="btn-ghost lg:hidden"
          aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={menuOpen}
        >
          {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {menuOpen && (
        <div className="border-t border-[#e5ddd3] bg-white px-4 py-3 lg:hidden">
          <div className="mx-auto flex max-w-7xl flex-col gap-1">
            {themeToggle}
            <Link onClick={() => setMenuOpen(false)} to="/" className={navLinkClass('/')}>Discover</Link>
            <Link onClick={() => setMenuOpen(false)} to="/upload" className={navLinkClass('/upload')}>Virtual try-on</Link>
            <Link onClick={() => setMenuOpen(false)} to="/history" className={navLinkClass('/history')}>Style journal</Link>
            {user ? (
              <button onClick={() => { logout(); setMenuOpen(false); }} className="btn-ghost justify-start">
                <LogOut className="h-4 w-4" /> Sign out
              </button>
            ) : (
              <div className="flex gap-2 pt-2">
                <Link onClick={() => setMenuOpen(false)} to="/login" className="btn-secondary flex-1">Sign in</Link>
                <Link onClick={() => setMenuOpen(false)} to="/upload" className="btn-primary flex-1">Get started</Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;
