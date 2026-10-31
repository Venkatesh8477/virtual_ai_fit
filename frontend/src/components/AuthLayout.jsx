import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';

const authImage = 'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1200&q=85';

const AuthLayout = ({ title, subtitle, error, children, footer }) => (
  <main className="mx-auto grid min-h-[calc(100vh-145px)] max-w-7xl items-center gap-8 px-4 py-8 sm:px-6 lg:grid-cols-2 lg:gap-16 lg:px-8">
    <section className="relative hidden min-h-[620px] overflow-hidden rounded-[28px] bg-[#241522] lg:block">
      <img src={authImage} alt="Friends exploring fashion together" className="absolute inset-0 h-full w-full object-cover opacity-80" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#241522]/90 via-[#241522]/15 to-[#241522]/20" />
      <div className="absolute left-9 top-9">
        <Link to="/" className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-4 py-2 text-xs font-semibold text-white backdrop-blur">
          <Sparkles className="h-3.5 w-3.5 text-[#e5c891]" /> Virtual AI Fit
        </Link>
      </div>
      <div className="absolute bottom-10 left-10 right-10 text-white">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#e5c891]">Your style, your story</p>
        <h2 className="font-editorial mt-3 max-w-lg text-4xl leading-tight">A fitting room that feels like it was made for you.</h2>
        <p className="mt-4 max-w-md text-sm leading-6 text-white/75">Take a moment to explore new looks and find the pieces that feel like you.</p>
      </div>
    </section>

    <section className="mx-auto w-full max-w-md">
      <Link to="/" className="mb-7 inline-flex items-center gap-2 text-xs font-medium text-[#827a78] hover:text-[#722f37] lg:hidden">
        ← <span>Back to Virtual AI Fit</span>
      </Link>
      <div className="app-card p-6 sm:p-9">
        <div className="mb-7">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#9b725b]">Welcome to the studio</p>
          <h1 className="font-editorial mt-2 text-3xl text-[#241522]">{title}</h1>
          <p className="mt-2 text-sm leading-6 text-[#827a78]">{subtitle}</p>
        </div>
        {error && <div role="alert" className="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-3 text-sm text-rose-800">{error}</div>}
        {children}
        <p className="mt-6 border-t border-[#eee7df] pt-5 text-center text-xs text-[#827a78]">{footer}</p>
      </div>
      <p className="mt-5 text-center text-[10px] text-[#9a918e]">Your account lets you keep your saved style journal in one place.</p>
    </section>
  </main>
);

export default AuthLayout;
