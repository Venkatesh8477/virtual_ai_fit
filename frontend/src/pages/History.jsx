import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { historyAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { AlertCircle, ArrowRight, CalendarDays, History as HistoryIcon, RotateCw, Shirt, Trash2 } from 'lucide-react';

const History = ({ setTryonResult }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [historyList, setHistoryList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError('');
    setHistoryList([]);
    try {
      const response = await historyAPI.getHistory();
      setHistoryList(response.data.history || []);
    } catch (err) {
      console.error(err);
      setError('Your style journal could not be loaded. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) fetchHistory();
    else {
      setHistoryList([]);
      setLoading(false);
    }
  }, [user, fetchHistory]);

  const handleDelete = async (itemId, event) => {
    event.stopPropagation();
    setDeletingId(itemId);
    setError('');
    try {
      await historyAPI.deleteHistoryItem(itemId);
      setHistoryList((items) => items.filter((item) => item.id !== itemId));
    } catch (err) {
      console.error(err);
      setError('This saved look could not be removed. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleInspect = (item) => {
    setTryonResult({
      person_image: item.personImage,
      dress_image: item.dressImage,
      result_image: item.resultImage,
      landmark_visualization: item.landmarkVisualization,
      segmented_image: item.segmentedImage,
      body_analysis: item.bodyAnalysis || {},
    });
    navigate('/result');
  };

  if (!user) {
    return (
      <main className="flex min-h-[70vh] items-center justify-center px-4 py-16">
        <section className="app-card max-w-md p-8 text-center">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#f1e9df] text-[#722f37]"><HistoryIcon className="h-6 w-6" /></span>
          <h1 className="font-editorial mt-5 text-3xl text-[#241522]">Your style journal</h1>
          <p className="mt-3 text-sm leading-6 text-[#827a78]">Sign in to revisit the try-on looks saved to your account.</p>
          <Link to="/login" className="btn-primary mt-6">Sign in to continue <ArrowRight className="h-4 w-4" /></Link>
        </section>
      </main>
    );
  }

  return (
    <main className="fade-in mx-auto max-w-7xl px-4 pb-16 pt-10 sm:px-6 lg:px-8">
      <div className="flex flex-col justify-between gap-4 border-b border-[#e5ddd3] pb-6 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#9b725b]">Saved for another day</p>
          <h1 className="font-editorial mt-2 text-4xl text-[#241522]">Your style journal</h1>
          <p className="mt-2 text-sm text-[#827a78]">Looks you have created in your Virtual AI Fit studio.</p>
        </div>
        {!loading && !error && <span className="w-fit rounded-full border border-[#e5ddd3] bg-white px-3 py-1.5 text-xs font-medium text-[#827a78]">{historyList.length} {historyList.length === 1 ? 'look' : 'looks'}</span>}
      </div>

      {error && (
        <div role="alert" className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          <span className="flex items-center gap-2"><AlertCircle className="h-4 w-4 shrink-0" />{error}</span>
          <button onClick={fetchHistory} className="btn-secondary min-h-9 px-3 py-1 text-xs"><RotateCw className="h-3.5 w-3.5" /> Retry</button>
        </div>
      )}

      {loading ? (
        <div role="status" className="py-24 text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-[#e5ddd3] border-t-[#722f37]" />
          <p className="mt-4 text-sm text-[#827a78]">Gathering your saved looks…</p>
        </div>
      ) : historyList.length === 0 && !error ? (
        <section className="mx-auto mt-12 max-w-lg rounded-2xl border border-dashed border-[#d8c8c0] bg-white/70 px-6 py-14 text-center">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#f1e9df] text-[#722f37]"><Shirt className="h-6 w-6" /></span>
          <h2 className="font-editorial mt-5 text-2xl text-[#241522]">A fresh page</h2>
          <p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-[#827a78]">Your saved try-on looks will appear here. Head to the studio to create your first one.</p>
          <Link to="/upload" className="btn-primary mt-6">Visit the studio <ArrowRight className="h-4 w-4" /></Link>
        </section>
      ) : historyList.length > 0 && (
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {historyList.map((item) => (
            <article key={item.id} className="group app-card overflow-hidden">
              <button type="button" onClick={() => handleInspect(item)} className="block w-full text-left" aria-label={`Revisit look from ${new Date(item.createdAt).toLocaleDateString()}`}>
                <div className="relative flex h-72 items-center justify-center overflow-hidden bg-[#f2ece5] p-4">
                  {item.resultImage ? (
                    <img src={item.resultImage} alt="Saved virtual try-on look" loading="lazy" className="h-full w-full rounded-lg object-contain transition-transform duration-300 group-hover:scale-[1.02]" />
                  ) : (
                    <span className="flex h-12 w-12 items-center justify-center rounded-full bg-white text-[#827a78]"><Shirt className="h-5 w-5" /></span>
                  )}
                  <span className="absolute bottom-3 right-3 rounded-full bg-white/90 px-3 py-1.5 text-[11px] font-semibold text-[#722f37] shadow-sm">View look</span>
                </div>
              </button>
              <div className="p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="flex items-center gap-1.5 text-xs text-[#827a78]"><CalendarDays className="h-3.5 w-3.5 text-[#c6a46a]" />{new Date(item.createdAt).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</span>
                  {item.bodyAnalysis?.body_type_shape && <span className="max-w-32 truncate rounded-full bg-[#f1e9df] px-2.5 py-1 text-[10px] font-medium text-[#722f37]">{item.bodyAnalysis.body_type_shape}</span>}
                </div>
                <div className="mt-4 flex items-center justify-between border-t border-[#eee7df] pt-3">
                  <button type="button" onClick={() => handleInspect(item)} className="text-sm font-semibold text-[#722f37] hover:text-[#4a1f2d]">Revisit look <ArrowRight className="ml-1 inline h-3.5 w-3.5" /></button>
                  <button
                    type="button"
                    onClick={(event) => handleDelete(item.id, event)}
                    disabled={deletingId === item.id}
                    className="btn-ghost min-h-9 px-2 text-xs text-[#827a78] hover:text-rose-700 disabled:opacity-50"
                    aria-label="Delete saved look"
                    title="Delete saved look"
                  >
                    <Trash2 className="h-3.5 w-3.5" /> {deletingId === item.id ? 'Removing…' : 'Remove'}
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
};

export default History;
