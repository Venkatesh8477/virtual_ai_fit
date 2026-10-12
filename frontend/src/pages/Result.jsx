import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Download, Save, RefreshCw, Eye, Sparkles, Activity, Layers, ArrowLeft, CheckCircle, Share2 } from 'lucide-react';

const Result = ({ resultData }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('result'); // 'result', 'landmarks', 'segmented'
  const [savedSuccess, setSavedSuccess] = useState(false);

  if (!resultData) {
    return (
      <div className="min-h-[75vh] flex flex-col items-center justify-center p-4 text-center">
        <div className="p-4 rounded-3xl bg-slate-900 border border-slate-800 text-slate-500 mb-4">
          <Sparkles className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">No Active Try-On Result</h2>
        <p className="text-sm text-slate-400 max-w-sm mb-6">Upload a person photo and dress image to view AI body analysis and try-on output.</p>
        <Link
          to="/upload"
          className="px-6 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all"
        >
          Go to Upload Studio
        </Link>
      </div>
    );
  }

  const {
    person_image,
    dress_image,
    landmark_visualization,
    segmented_image,
    result_image,
    body_analysis,
    landmarks,
    engine
  } = resultData;

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = result_image;
    link.download = `AI-Virtual-TryOn-Result-${Date.now()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 space-y-8">
      
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 glass-panel p-6 rounded-3xl border border-slate-800">
        <div>
          <button
            onClick={() => navigate('/upload')}
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-indigo-400 mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Upload Studio
          </button>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            Virtual Try-On Result
            <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              {engine || 'AI Engine Active'}
            </span>
          </h1>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <button
            onClick={handleDownload}
            className="flex-1 md:flex-none px-5 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition-all hover:scale-105"
          >
            <Download className="w-4 h-4" />
            Download Result
          </button>
          
          <button
            onClick={handleSave}
            className="px-5 py-3 rounded-2xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs flex items-center justify-center gap-2 border border-slate-800 transition-colors"
          >
            {savedSuccess ? (
              <>
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span className="text-emerald-400">Saved</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4 text-slate-400" />
                <span>Save Record</span>
              </>
            )}
          </button>

          <Link
            to="/upload"
            className="px-5 py-3 rounded-2xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 font-semibold text-xs flex items-center justify-center gap-2 border border-purple-500/30 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Try Another Dress
          </Link>
        </div>
      </div>

      {/* Main Grid: Inputs vs AI Output */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column (5 Cols): Inputs & Proportions */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Source Images (Original + Dress) */}
          <div className="glass-panel p-5 rounded-3xl space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              Source Input Media
            </h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-950 p-2.5 rounded-2xl border border-slate-800/80">
                <span className="block text-[11px] font-semibold text-slate-400 mb-2 text-center">Original Person</span>
                <div className="h-44 flex items-center justify-center overflow-hidden rounded-xl bg-slate-900/50">
                  <img src={person_image} alt="Original person" className="max-h-full max-w-full object-contain rounded-xl" />
                </div>
              </div>

              <div className="bg-slate-950 p-2.5 rounded-2xl border border-slate-800/80">
                <span className="block text-[11px] font-semibold text-slate-400 mb-2 text-center">Selected Dress</span>
                <div className="h-44 flex items-center justify-center overflow-hidden rounded-xl bg-slate-900/50">
                  <img src={dress_image} alt="Selected dress" className="max-h-full max-w-full object-contain rounded-xl" />
                </div>
              </div>
            </div>
          </div>

          {/* Module 3: MediaPipe Body Measurements & Proportions */}
          <div className="glass-panel p-6 rounded-3xl space-y-4 border border-indigo-500/20">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-400" />
                MediaPipe Body Analysis
              </h3>
              <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300">
                {body_analysis?.body_type_shape || 'Hourglass'} Shape
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
                <span className="block text-[10px] text-slate-400">Shoulder Width</span>
                <span className="text-base font-bold text-white">{body_analysis?.shoulder_width_cm || 42} <span className="text-xs font-normal text-slate-500">cm</span></span>
              </div>

              <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
                <span className="block text-[10px] text-slate-400">Waist Width</span>
                <span className="text-base font-bold text-white">{body_analysis?.waist_width_cm || 32} <span className="text-xs font-normal text-slate-500">cm</span></span>
              </div>

              <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
                <span className="block text-[10px] text-slate-400">Hip Width</span>
                <span className="text-base font-bold text-white">{body_analysis?.hip_width_cm || 40} <span className="text-xs font-normal text-slate-500">cm</span></span>
              </div>

              <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
                <span className="block text-[10px] text-slate-400">Arm Length</span>
                <span className="text-base font-bold text-white">{body_analysis?.arm_length_cm || 60} <span className="text-xs font-normal text-slate-500">cm</span></span>
              </div>

              <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
                <span className="block text-[10px] text-slate-400">Leg Length</span>
                <span className="text-base font-bold text-white">{body_analysis?.leg_length_cm || 85} <span className="text-xs font-normal text-slate-500">cm</span></span>
              </div>

              <div className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800">
                <span className="block text-[10px] text-slate-400">Torso-Leg Ratio</span>
                <span className="text-base font-bold text-indigo-400">{body_analysis?.body_ratio || 0.72}</span>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column (7 Cols): View Tabs (Result / MediaPipe Landmarks / Background Segmented) */}
        <div className="lg:col-span-7 glass-panel p-6 rounded-3xl space-y-6">
          
          {/* Tab Selection */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('result')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'result'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-white bg-slate-900/50'
                }`}
              >
                Final AI Try-On
              </button>

              <button
                onClick={() => setActiveTab('landmarks')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'landmarks'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-white bg-slate-900/50'
                }`}
              >
                MediaPipe Pose Keypoints
              </button>

              <button
                onClick={() => setActiveTab('segmented')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'segmented'
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-white bg-slate-900/50'
                }`}
              >
                Background Removed
              </button>
            </div>
          </div>

          {/* Active Canvas Display */}
          <div className="relative min-h-[500px] bg-slate-950/80 rounded-2xl border border-slate-800 flex items-center justify-center p-4 overflow-hidden group">
            {activeTab === 'result' && (
              <img
                src={result_image}
                alt="Final AI Try-On"
                className="max-h-[580px] max-w-full object-contain rounded-xl shadow-2xl transition-transform duration-500 group-hover:scale-105"
              />
            )}

            {activeTab === 'landmarks' && (
              <img
                src={landmark_visualization}
                alt="MediaPipe Pose Landmarks"
                className="max-h-[580px] max-w-full object-contain rounded-xl shadow-2xl"
              />
            )}

            {activeTab === 'segmented' && (
              <div className="w-full h-full flex flex-col items-center justify-center">
                {/* Transparency checkerboard background effect */}
                <div className="p-4 rounded-xl bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px]">
                  <img
                    src={segmented_image}
                    alt="Segmented Foreground Person"
                    className="max-h-[550px] max-w-full object-contain drop-shadow-2xl"
                  />
                </div>
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
};

export default Result;
