import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { tryonAPI } from '../api/client';
import {
  AlertCircle, ArrowRight, Check, Image as ImageIcon, RefreshCw, Sparkles,
  Trash2, Upload as UploadIcon, User, Shirt,
} from 'lucide-react';

const acceptedTypes = ['image/jpeg', 'image/png', 'image/webp'];

const ImageCard = ({ kind, title, description, file, preview, onFile, onRemove }) => {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);
  const isPerson = kind === 'person';

  const receiveFile = (candidate) => {
    if (!candidate) return;
    if (!acceptedTypes.includes(candidate.type)) {
      onFile(null, 'Please choose a JPG, PNG, or WebP image.');
      return;
    }
    onFile(candidate, '');
  };

  return (
    <section className="app-card p-4 sm:p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#f1e9df] text-[#722f37]">
            {isPerson ? <User className="h-4 w-4" /> : <Shirt className="h-4 w-4" />}
          </span>
          <div>
            <h2 className="text-sm font-semibold text-[#35313a]">{title}</h2>
            <p className="mt-0.5 text-xs text-[#827a78]">{description}</p>
          </div>
        </div>
        {file && <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-700"><Check className="h-3.5 w-3.5" /> Added</span>}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="sr-only"
        aria-label={`Choose ${title.toLowerCase()}`}
        onChange={(event) => {
          receiveFile(event.target.files?.[0]);
          event.target.value = '';
        }}
      />
      <div
        onDragEnter={(event) => { event.preventDefault(); setDragging(true); }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) setDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          receiveFile(event.dataTransfer.files?.[0]);
        }}
        className={`upload-zone relative flex min-h-[300px] flex-col items-center justify-center overflow-hidden rounded-2xl p-4 sm:min-h-[350px] ${dragging ? 'is-dragging' : ''}`}
      >
        {preview ? (
          <>
            <img src={preview} alt={isPerson ? 'Selected person photo preview' : 'Selected garment preview'} className="max-h-[300px] max-w-full rounded-xl object-contain sm:max-h-[340px]" />
            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between rounded-xl bg-white/95 px-3 py-2 shadow-sm">
              <span className="max-w-[65%] truncate text-xs font-medium text-[#35313a]">{file?.name}</span>
              <div className="flex gap-1">
                <button type="button" className="btn-ghost min-h-8 px-2 text-xs" onClick={() => inputRef.current?.click()}>Replace</button>
                <button type="button" className="btn-ghost min-h-8 px-2 text-xs text-rose-700" onClick={onRemove} aria-label={`Remove ${title.toLowerCase()}`}><Trash2 className="h-3.5 w-3.5" /> Remove</button>
              </div>
            </div>
          </>
        ) : (
          <button type="button" onClick={() => inputRef.current?.click()} className="flex w-full flex-col items-center py-12 text-center">
            <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#f1e9df] text-[#722f37]"><UploadIcon className="h-6 w-6" /></span>
            <span className="text-sm font-semibold text-[#35313a]">Drop an image here or <span className="text-[#722f37] underline underline-offset-2">browse files</span></span>
            <span className="mt-2 max-w-xs text-xs leading-5 text-[#827a78]">{description}</span>
            <span className="mt-4 rounded-full bg-[#f1e9df] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.1em] text-[#827a78]">JPG · PNG · WebP</span>
          </button>
        )}
      </div>
      <p className="mt-3 flex items-center gap-1.5 text-[11px] leading-5 text-[#827a78]">
        <ImageIcon className="h-3.5 w-3.5 shrink-0 text-[#c6a46a]" />
        {isPerson ? 'A clear, well-lit full-body photo works best.' : 'One clothing item on a simple background works best.'}
      </p>
    </section>
  );
};

const Upload = ({ colabUrl, setTryonResult }) => {
  const [person, setPerson] = useState({ file: null, preview: '' });
  const [garment, setGarment] = useState({ file: null, preview: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const objectUrls = useRef(new Set());

  useEffect(() => () => {
    objectUrls.current.forEach((url) => URL.revokeObjectURL(url));
    objectUrls.current.clear();
  }, []);

  const setImage = (setter, previous, file, validationError) => {
    if (validationError) {
      setError(validationError);
      return;
    }
    setError('');
    if (previous.preview) {
      URL.revokeObjectURL(previous.preview);
      objectUrls.current.delete(previous.preview);
    }
    const preview = file ? URL.createObjectURL(file) : '';
    if (preview) objectUrls.current.add(preview);
    setter({ file, preview });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!person.file || !garment.file) {
      setError('Add both a person photo and a garment image to continue.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const response = await tryonAPI.generateTryOn(person.file, garment.file, colabUrl);
      setTryonResult(response.data);
      navigate('/result');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Try-on generation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="fade-in mx-auto max-w-7xl px-4 pb-16 pt-9 sm:px-6 sm:pt-12 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <p className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.17em] text-[#9b725b]"><Sparkles className="h-3.5 w-3.5 text-[#c6a46a]" /> The styling studio</p>
        <h1 className="font-editorial mt-3 text-4xl font-medium tracking-[-0.03em] text-[#241522] sm:text-5xl">Let’s find your <span className="italic text-[#722f37]">next look.</span></h1>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-[#827a78] sm:text-base">Add your photo and a garment to create a personal try-on preview. Clear, well-lit images help the studio do its best work.</p>
      </div>

      <ol aria-label="Try-on steps" className="mx-auto my-8 flex max-w-3xl items-center justify-center">
        {[
          ['01', 'Your photo', Boolean(person.file)],
          ['02', 'Your garment', Boolean(garment.file)],
          ['03', 'Your look', false],
        ].map(([number, label, complete], index) => (
          <li key={number} className="flex flex-1 items-center last:flex-none">
            <div className="flex min-w-0 items-center gap-2 sm:gap-3">
              <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-[11px] font-semibold ${complete ? 'border-[#722f37] bg-[#722f37] text-white' : 'border-[#d8c8c0] bg-white text-[#827a78]'}`}>{complete ? <Check className="h-4 w-4" /> : number}</span>
              <span className={`hidden text-xs font-medium sm:block ${complete ? 'text-[#722f37]' : 'text-[#827a78]'}`}>{label}</span>
            </div>
            {index < 2 && <span aria-hidden="true" className={`mx-3 h-px flex-1 sm:mx-5 ${complete ? 'bg-[#722f37]' : 'bg-[#e5ddd3]'}`} />}
          </li>
        ))}
      </ol>

      {error && (
        <div role="alert" className="mx-auto mb-5 flex max-w-3xl items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid gap-5 md:grid-cols-2">
          <ImageCard
            kind="person"
            title="Your photo"
            description="Choose a full-body photo with your arms slightly away from your sides."
            file={person.file}
            preview={person.preview}
            onFile={(file, validationError) => setImage(setPerson, person, file, validationError)}
            onRemove={() => setImage(setPerson, person, null, '')}
          />
          <ImageCard
            kind="garment"
            title="Your garment"
            description="Choose a single top, dress, or clothing item to try on."
            file={garment.file}
            preview={garment.preview}
            onFile={(file, validationError) => setImage(setGarment, garment, file, validationError)}
            onRemove={() => setImage(setGarment, garment, null, '')}
          />
        </div>

        <div className="app-card flex flex-col items-start justify-between gap-4 p-4 sm:flex-row sm:items-center sm:p-5">
          <div>
            <p className="text-sm font-semibold text-[#35313a]">Ready when you are</p>
            <p className="mt-1 text-xs text-[#827a78]">{colabUrl ? 'Using the configured remote endpoint.' : 'Your photos will be processed by the configured local service.'}</p>
          </div>
          <button type="submit" disabled={loading || !person.file || !garment.file} className="btn-primary w-full sm:w-auto">
            {loading ? <><RefreshCw className="h-4 w-4 animate-spin" /> Creating your preview…</> : <>Create my look <ArrowRight className="h-4 w-4" /></>}
          </button>
        </div>
      </form>

      {loading && (
        <div role="status" aria-live="polite" className="fixed inset-0 z-50 flex items-center justify-center bg-[#241522]/45 p-4 backdrop-blur-sm">
          <div className="app-card w-full max-w-sm p-8 text-center">
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#f1e9df] text-[#722f37]"><Sparkles className="h-6 w-6" /></div>
            <h2 className="font-editorial text-2xl text-[#241522]">Creating your look</h2>
            <p className="mt-2 text-sm text-[#827a78]">Your photos are being prepared. This can take a little moment.</p>
            <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-[#f1e9df]"><div className="h-full w-1/2 animate-pulse rounded-full bg-[#722f37]" /></div>
          </div>
        </div>
      )}
    </main>
  );
};

export default Upload;
