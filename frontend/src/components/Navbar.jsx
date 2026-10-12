import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sparkles, History, Upload, User, LogOut, Shirt, Cpu } from 'lucide-react';

const Navbar = ({ colabUrl, setColabUrl }) => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-4 lg:px-8 py-3 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 p-[2px] shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform duration-300">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Shirt className="w-5 h-5 text-indigo-400 group-hover:rotate-12 transition-transform duration-300" />
            </div>
          </div>
          <div>
            <span className="text-xl font-bold font-sans tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
              V-TryOn <span className="text-indigo-400 font-extrabold">AI</span>
            </span>
            <span className="block text-[10px] text-slate-400 tracking-wider font-semibold uppercase">
              Pose & Neural Fitting
            </span>
          </div>
        </Link>

        {/* Center Nav Links */}
        <div className="hidden md:flex items-center gap-1 bg-slate-900/60 p-1.5 rounded-full border border-slate-800/80">
          <Link
            to="/upload"
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
              isActive('/upload') || isActive('/')
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <Upload className="w-4 h-4" />
            Studio Try-On
          </Link>
          
          <Link
            to="/history"
            className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
              isActive('/history')
                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            <History className="w-4 h-4" />
            History Gallery
          </Link>
        </div>

        {/* Right Section: Colab Config & User Auth */}
        <div className="flex items-center gap-3">
          
          {/* Colab URL Input Trigger */}
          <div className="relative group hidden sm:block">
            <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-xl text-xs text-slate-300 hover:border-indigo-500/50 transition-colors">
              <Cpu className={`w-3.5 h-3.5 ${colabUrl ? 'text-emerald-400 animate-pulse' : 'text-slate-400'}`} />
              <span>{colabUrl ? 'Colab GPU Active' : 'Colab GPU (Optional)'}</span>
            </div>
            {/* Popover */}
            <div className="absolute right-0 top-full mt-2 w-72 p-3 glass-panel rounded-2xl shadow-2xl hidden group-hover:block z-50">
              <p className="text-xs font-semibold text-slate-200 mb-1">Google Colab IDM-VTON API</p>
              <p className="text-[11px] text-slate-400 mb-2">Paste your ngrok public URL from Colab to run GPU inference:</p>
              <input
                type="text"
                placeholder="https://xxxx.ngrok-free.app"
                value={colabUrl}
                onChange={(e) => setColabUrl(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {user ? (
            <div className="flex items-center gap-3">
              <div className="hidden lg:flex flex-col text-right">
                <span className="text-xs font-semibold text-white">{user.name}</span>
                <span className="text-[10px] text-slate-400">{user.email}</span>
              </div>
              <button
                onClick={logout}
                title="Logout"
                className="p-2.5 rounded-xl bg-slate-900 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-800 transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-900 rounded-xl transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 text-xs font-semibold bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl shadow-lg shadow-indigo-600/20 transition-all hover:scale-105"
              >
                Register
              </Link>
            </div>
          )}

        </div>

      </div>
    </nav>
  );
};

export default Navbar;
