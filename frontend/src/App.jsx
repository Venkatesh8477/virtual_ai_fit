import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import Upload from './pages/Upload';
import Result from './pages/Result';
import History from './pages/History';

function App() {
  const [colabUrl, setColabUrl] = useState('');
  const [tryonResult, setTryonResult] = useState(null);

  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen flex flex-col justify-between">
          <Navbar colabUrl={colabUrl} setColabUrl={setColabUrl} />
          
          <main className="flex-1 pb-16">
            <Routes>
              <Route path="/" element={<Upload colabUrl={colabUrl} setTryonResult={setTryonResult} />} />
              <Route path="/upload" element={<Upload colabUrl={colabUrl} setTryonResult={setTryonResult} />} />
              <Route path="/result" element={<Result resultData={tryonResult} />} />
              <Route path="/history" element={<History setTryonResult={setTryonResult} />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          <footer className="glass-panel border-t border-slate-800/80 py-6 px-4 text-center text-xs text-slate-500">
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
              <div>
                © {new Date().getFullYear()} AI Virtual Try-On Studio. Powered by MediaPipe & IDM-VTON.
              </div>
              <div className="flex items-center gap-4 text-slate-400">
                <span>FastAPI Backend</span>
                <span>•</span>
                <span>React Frontend</span>
                <span>•</span>
                <span>MongoDB History</span>
              </div>
            </div>
          </footer>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
