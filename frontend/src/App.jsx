import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Upload from './pages/Upload';
import Home from './pages/Home';
import Result from './pages/Result';
import History from './pages/History';

function App() {
  const [colabUrl, setColabUrl] = useState('');
  const [tryonResult, setTryonResult] = useState(null);
  const [isDark, setIsDark] = useState(() => localStorage.getItem('virtual-fit-theme') === 'dark');

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('virtual-fit-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen flex flex-col justify-between">
          <Navbar
            colabUrl={colabUrl}
            setColabUrl={setColabUrl}
            isDark={isDark}
            setIsDark={setIsDark}
          />
          
          <div className="flex-1">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/upload" element={<Upload colabUrl={colabUrl} setTryonResult={setTryonResult} />} />
              <Route path="/result" element={<Result resultData={tryonResult} />} />
              <Route path="/history" element={<History setTryonResult={setTryonResult} />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>

          <footer className="border-t border-[#e5ddd3] bg-[#faf7f2] px-4 py-6 text-center text-xs text-[#827a78]">
            <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 sm:flex-row">
              <div>
                © {new Date().getFullYear()} Virtual AI Fit. A personal styling studio.
              </div>
              <div className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-[#c6a46a]" /> Thoughtful style, one look at a time</div>
            </div>
          </footer>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
