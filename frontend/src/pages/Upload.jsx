import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { tryonAPI } from '../api/client';
import { Upload as UploadIcon, User, Shirt, Sparkles, ArrowRight, Image as ImageIcon, Cpu, CheckCircle2, RefreshCw } from 'lucide-react';

const Upload = ({ colabUrl, setTryonResult }) => {
  const [personFile, setPersonFile] = useState(null);
  const [personPreview, setPersonPreview] = useState('');
  const [dressFile, setDressFile] = useState(null);
  const [dressPreview, setDressPreview] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState('');

  const navigate = useNavigate();

  const handlePersonChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPersonFile(file);
      setPersonPreview(URL.createObjectURL(file));
    }
  };

  const handleDressChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setDressFile(file);
      setDressPreview(URL.createObjectURL(file));
    }
  };

  // Pre-load demo sample images for quick 1-click testing
  const loadSample = (type, sampleUrl) => {
    fetch(sampleUrl)
      .then(res => res.blob())
      .then(blob => {
        const file = new File([blob], `${type}_sample.jpg`, { type: 'image/jpeg' });
        if (type === 'person') {
          setPersonFile(file);
          setPersonPreview(sampleUrl);
        } else {
          setDressFile(file);
          setDressPreview(sampleUrl);
        }
      });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!personFile || !dressFile) {
      setError('Please select both a person photo and a dress image to proceed.');
      return;
    }

    setError('');
    setLoading(true);
    setStatusMessage('Running MediaPipe Pose Estimation & Body Metrics...');

    try {
      setTimeout(() => setStatusMessage('Executing MediaPipe Background Segmentation...'), 1200);
      setTimeout(() => setStatusMessage(colabUrl ? 'Running IDM-VTON Neural Try-On (Google Colab)...' : 'Synthesizing Pose-Aligned Virtual Try-On...'), 2500);

      const res = await tryonAPI.generateTryOn(personFile, dressFile, colabUrl);
      setTryonResult(res.data);
      navigate('/result');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Try-On generation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold mb-3">
          <Sparkles className="w-3.5 h-3.5" />
          AI Neural Fitting Studio
        </div>
        <h1 className="text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
          Virtual Try-On & Body Analysis
        </h1>
        <p className="text-slate-400 text-sm max-w-xl mx-auto mt-2">
          Upload a full-body photo and dress image. MediaPipe will extract body landmarks, estimate proportions, and render your AI try-on result.
        </p>
      </div>

      {error && (
        <div className="max-w-2xl mx-auto mb-6 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm text-center">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Box 1: Person Image */}
          <div className="glass-panel p-6 rounded-3xl relative">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-sm font-bold text-white">
                <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
                  <User className="w-4 h-4" />
                </div>
                1. Full-Body Person Photo
              </div>
              <span className="text-[11px] text-slate-400 font-medium">JPEG / PNG</span>
            </div>

            <div className="relative border-2 border-dashed border-slate-700 hover:border-indigo-500/60 rounded-2xl p-4 transition-colors min-h-[320px] flex flex-col items-center justify-center bg-slate-950/40 group">
              {personPreview ? (
                <div className="relative w-full h-72 flex items-center justify-center">
                  <img
                    src={personPreview}
                    alt="Person preview"
                    className="max-h-full max-w-full object-contain rounded-xl shadow-lg"
                  />
                  <label className="absolute bottom-3 right-3 bg-slate-900/90 text-white px-3 py-1.5 rounded-xl text-xs font-semibold cursor-pointer hover:bg-indigo-600 transition-colors border border-slate-700 shadow-lg">
                    Change
                    <input type="file" accept="image/*" onChange={handlePersonChange} className="hidden" />
                  </label>
                </div>
              ) : (
                <label className="w-full h-full flex flex-col items-center justify-center cursor-pointer py-10">
                  <div className="w-16 h-16 rounded-2xl bg-slate-900 flex items-center justify-center text-slate-400 group-hover:text-indigo-400 group-hover:scale-110 transition-all border border-slate-800 mb-3 shadow-inner">
                    <UploadIcon className="w-7 h-7" />
                  </div>
                  <span className="text-sm font-semibold text-slate-200">Click to upload person photo</span>
                  <span className="text-xs text-slate-500 mt-1">Full-body front facing recommended</span>
                  <input type="file" accept="image/*" onChange={handlePersonChange} className="hidden" />
                </label>
              )}
            </div>

            {/* Quick Demo Preset */}
            <div className="mt-4 flex items-center justify-between text-xs text-slate-400 pt-3 border-t border-slate-800">
              <span>Quick Test Sample:</span>
              <button
                type="button"
                onClick={() => loadSample('person', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80')}
                className="text-indigo-400 hover:text-indigo-300 font-semibold hover:underline"
              >
                Use Model Sample
              </button>
            </div>
          </div>

          {/* Box 2: Dress Image */}
          <div className="glass-panel p-6 rounded-3xl relative">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-sm font-bold text-white">
                <div className="p-2 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30">
                  <Shirt className="w-4 h-4" />
                </div>
                2. Dress / Garment Image
              </div>
              <span className="text-[11px] text-slate-400 font-medium">JPEG / PNG</span>
            </div>

            <div className="relative border-2 border-dashed border-slate-700 hover:border-purple-500/60 rounded-2xl p-4 transition-colors min-h-[320px] flex flex-col items-center justify-center bg-slate-950/40 group">
              {dressPreview ? (
                <div className="relative w-full h-72 flex items-center justify-center">
                  <img
                    src={dressPreview}
                    alt="Dress preview"
                    className="max-h-full max-w-full object-contain rounded-xl shadow-lg"
                  />
                  <label className="absolute bottom-3 right-3 bg-slate-900/90 text-white px-3 py-1.5 rounded-xl text-xs font-semibold cursor-pointer hover:bg-purple-600 transition-colors border border-slate-700 shadow-lg">
                    Change
                    <input type="file" accept="image/*" onChange={handleDressChange} className="hidden" />
                  </label>
                </div>
              ) : (
                <label className="w-full h-full flex flex-col items-center justify-center cursor-pointer py-10">
                  <div className="w-16 h-16 rounded-2xl bg-slate-900 flex items-center justify-center text-slate-400 group-hover:text-purple-400 group-hover:scale-110 transition-all border border-slate-800 mb-3 shadow-inner">
                    <ImageIcon className="w-7 h-7" />
                  </div>
                  <span className="text-sm font-semibold text-slate-200">Click to upload dress image</span>
                  <span className="text-xs text-slate-500 mt-1">Single clothing item on plain background</span>
                  <input type="file" accept="image/*" onChange={handleDressChange} className="hidden" />
                </label>
              )}
            </div>

            {/* Quick Demo Preset */}
            <div className="mt-4 flex items-center justify-between text-xs text-slate-400 pt-3 border-t border-slate-800">
              <span>Quick Test Sample:</span>
              <button
                type="button"
                onClick={() => loadSample('dress', 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&auto=format&fit=crop&q=80')}
                className="text-purple-400 hover:text-purple-300 font-semibold hover:underline"
              >
                Use Dress Sample
              </button>
            </div>
          </div>

        </div>

        {/* Submit Action Bar */}
        <div className="glass-panel p-6 rounded-3xl flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-slate-900 border border-slate-800 text-indigo-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-200">AI Pipeline Engine Mode</div>
              <div className="text-[11px] text-slate-400">
                {colabUrl ? `IDM-VTON Connected (${colabUrl})` : 'MediaPipe + Local Neural Composite Engine'}
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !personFile || !dressFile}
            className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-bold text-base shadow-xl shadow-indigo-600/30 transition-all hover:scale-[1.03] disabled:opacity-40 disabled:hover:scale-100 flex items-center justify-center gap-3"
          >
            {loading ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin text-white" />
                <span>Processing AI Try-On...</span>
              </>
            ) : (
              <>
                <span>Generate Virtual Try-On</span>
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Loading Modal Overlay */}
      {loading && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel max-w-sm w-full p-8 rounded-3xl text-center space-y-4 border border-indigo-500/30 shadow-2xl">
            <div className="relative w-20 h-20 mx-auto flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping" />
              <div className="absolute inset-0 rounded-full border-4 border-t-indigo-500 border-r-purple-500 border-b-pink-500 border-l-transparent animate-spin" />
              <Sparkles className="w-8 h-8 text-indigo-400" />
            </div>
            <h3 className="text-lg font-bold text-white">Analyzing Pose & Fitting</h3>
            <p className="text-xs text-indigo-300 font-medium animate-pulse">{statusMessage}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Upload;
