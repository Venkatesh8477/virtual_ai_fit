import React, { useState, useEffect } from 'react';
import { historyAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { History as HistoryIcon, Calendar, Trash2, ExternalLink, Sparkles, AlertCircle, Shirt } from 'lucide-react';
import { Link } from 'react-router-dom';

const History = ({ setTryonResult }) => {
  const { user } = useAuth();
  const [historyList, setHistoryList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, [user]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      if (user) {
        const res = await historyAPI.getHistory();
        setHistoryList(res.data.history || []);
      }
    } catch (err) {
      console.error(err);
      setError('Could not fetch history items.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (itemId, e) => {
    e.stopPropagation();
    try {
      await historyAPI.deleteHistoryItem(itemId);
      setHistoryList(prev => prev.filter(item => item.id !== itemId));
    } catch (err) {
      console.error(err);
    }
  };

  const handleInspect = (item) => {
    setTryonResult({
      person_image: item.personImage,
      dress_image: item.dressImage,
      result_image: item.resultImage,
      landmark_visualization: item.personImage,
      segmented_image: item.segmentedImage || item.personImage,
      body_analysis: item.bodyAnalysis || {},
      engine: 'Saved History Session'
    });
  };

  if (!user) {
    return (
      <div className="min-h-[75vh] flex flex-col items-center justify-center p-4 text-center">
        <div className="p-4 rounded-3xl bg-slate-900 border border-slate-800 text-indigo-400 mb-4">
          <HistoryIcon className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Sign In to View Try-On History</h2>
        <p className="text-sm text-slate-400 max-w-sm mb-6">Create an account or login to automatically save and revisit your previous virtual try-on sessions.</p>
        <Link
          to="/login"
          className="px-6 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all"
        >
          Sign In Now
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 space-y-8">
      
      {/* Header */}
      <div className="flex items-center justify-between glass-panel p-6 rounded-3xl">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
            <HistoryIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Try-On History Gallery</h1>
            <p className="text-xs text-slate-400 mt-0.5">Revisit and download your past AI virtual try-on renders</p>
          </div>
        </div>
        <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-slate-900 text-indigo-300 border border-slate-800">
          {historyList.length} Renders Saved
        </span>
      </div>

      {loading ? (
        <div className="py-20 text-center space-y-3">
          <div className="w-8 h-8 mx-auto border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400">Loading history records...</p>
        </div>
      ) : historyList.length === 0 ? (
        <div className="glass-panel p-12 rounded-3xl text-center space-y-4 max-w-md mx-auto">
          <Shirt className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-white">No Saved Try-Ons Yet</h3>
          <p className="text-xs text-slate-400">Your AI try-on renders will appear here once generated.</p>
          <Link
            to="/upload"
            className="inline-block px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold text-xs shadow-lg shadow-indigo-600/30"
          >
            Create Your First Try-On
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {historyList.map((item) => (
            <div
              key={item.id}
              onClick={() => handleInspect(item)}
              className="glass-panel rounded-3xl overflow-hidden glass-panel-hover group cursor-pointer border border-slate-800"
            >
              {/* Image Preview Container */}
              <div className="relative h-64 bg-slate-950 flex items-center justify-center p-3 overflow-hidden">
                <img
                  src={item.resultImage}
                  alt="Try-on render"
                  className="max-h-full max-w-full object-contain rounded-xl transition-transform duration-500 group-hover:scale-105"
                />

                <button
                  onClick={(e) => handleDelete(item.id, e)}
                  title="Delete record"
                  className="absolute top-3 right-3 p-2 rounded-xl bg-slate-900/80 hover:bg-rose-600 text-slate-400 hover:text-white transition-colors border border-slate-800"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Card Footer Info */}
              <div className="p-5 space-y-3 bg-slate-900/50 border-t border-slate-800/80">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{new Date(item.createdAt).toLocaleDateString()}</span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 font-medium">
                    {item.bodyAnalysis?.body_type_shape || 'Pose Analyzed'}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                  <span className="text-xs font-bold text-white group-hover:text-indigo-400 transition-colors">
                    Revisit Details
                  </span>
                  <ExternalLink className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
};

export default History;
