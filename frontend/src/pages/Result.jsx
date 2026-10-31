import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Activity, ArrowLeft, ArrowRight, Download, Eye, Image as ImageIcon,
  Layers, RefreshCw, Sparkles,
} from 'lucide-react';

const Result = ({ resultData }) => {
  const navigate = useNavigate();
  const [activeView, setActiveView] = useState('result');

  if (!resultData) {
    return (
      <main className="flex min-h-[70vh] items-center justify-center px-4 py-16">
        <section className="app-card max-w-md p-8 text-center">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#f1e9df] text-[#722f37]"><Sparkles className="h-6 w-6" /></span>
          <h1 className="font-editorial mt-5 text-3xl text-[#241522]">Your fitting room is ready</h1>
          <p className="mt-3 text-sm leading-6 text-[#827a78]">Add a photo and a garment in the studio to create a try-on preview.</p>
          <Link to="/upload" className="btn-primary mt-6">Go to the studio <ArrowRight className="h-4 w-4" /></Link>
        </section>
      </main>
    );
  }

  const {
    person_image: personImage,
    dress_image: dressImage,
    landmark_visualization: landmarkImage,
    segmented_image: segmentedImage,
    segmentation_mask: segmentationMask,
    segmentation_method: segmentationMethod,
    segmentation_warning: segmentationWarning,
    result_image: resultImage,
    body_analysis: bodyAnalysis,
    landmarks = [],
    engine,
  } = resultData;

  const unusableLandmarks = landmarks.filter((landmark) => landmark.usable_for_measurement === false);
  const views = [
    { id: 'result', label: 'Your look', icon: Sparkles },
    { id: 'compare', label: 'Before & after', icon: Eye },
    ...(landmarkImage ? [{ id: 'landmarks', label: 'Pose map', icon: Activity }] : []),
    ...(segmentedImage ? [{ id: 'segmented', label: 'Person cutout', icon: ImageIcon }] : []),
    ...(segmentationMask ? [{ id: 'mask', label: 'Mask', icon: Layers }] : []),
  ];

  const formatPixelMetric = (value) => (
    Number.isFinite(value) ? `${value.toFixed(1)} px` : '—'
  );

  const handleDownload = () => {
    if (!resultImage) return;
    const link = document.createElement('a');
    link.href = resultImage;
    link.download = `Virtual-AI-Fit-Look-${Date.now()}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <main className="fade-in mx-auto max-w-7xl px-4 pb-16 pt-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <button onClick={() => navigate('/upload')} className="mb-3 inline-flex items-center gap-2 text-xs font-semibold text-[#827a78] hover:text-[#722f37]">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to the studio
          </button>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#9b725b]">The fitting room</p>
          <h1 className="font-editorial mt-1 text-4xl text-[#241522] sm:text-5xl">Your look is ready.</h1>
          {engine && <p className="mt-2 text-xs text-[#827a78]">Created with {engine}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={handleDownload} disabled={!resultImage} className="btn-secondary flex-1 sm:flex-none disabled:cursor-not-allowed disabled:opacity-50">
            <Download className="h-4 w-4" /> Download
          </button>
          <Link to="/upload" className="btn-primary flex-1 sm:flex-none"><RefreshCw className="h-4 w-4" /> Try another look</Link>
        </div>
      </div>

      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_310px]">
        <section className="app-card min-w-0 overflow-hidden">
          <div className="flex gap-1 overflow-x-auto border-b border-[#eee7df] p-3 sm:p-4">
            {views.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setActiveView(id)}
                aria-pressed={activeView === id}
                className={`inline-flex shrink-0 items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold transition-colors ${activeView === id ? 'bg-[#722f37] text-white' : 'text-[#827a78] hover:bg-[#f1e9df] hover:text-[#722f37]'}`}
              >
                <Icon className="h-3.5 w-3.5" /> {label}
              </button>
            ))}
          </div>
          {activeView === 'compare' ? (
            <div className="grid min-h-[480px] grid-cols-2 gap-px bg-[#e5ddd3] p-px sm:min-h-[600px]">
              {[
                ['Before', personImage],
                ['Your look', resultImage],
              ].map(([label, image]) => (
                <div key={label} className="flex min-w-0 flex-col bg-[#f7f3ef] p-3 sm:p-5">
                  <span className="mb-3 text-xs font-semibold text-[#827a78]">{label}</span>
                  <div className="flex flex-1 items-center justify-center overflow-hidden rounded-xl bg-white p-2 sm:p-4">
                    {image ? <img src={image} alt={label} className="max-h-[560px] max-w-full object-contain" /> : <span className="text-xs text-[#827a78]">Image unavailable</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={`flex min-h-[480px] items-center justify-center p-4 sm:min-h-[600px] sm:p-8 ${activeView === 'segmented' ? 'bg-[linear-gradient(45deg,#f1e9df_25%,transparent_25%,transparent_75%,#f1e9df_75%),linear-gradient(45deg,#f1e9df_25%,#fff_25%,#fff_75%,#f1e9df_75%)] [background-position:0_0,10px_10px] [background-size:20px_20px]' : 'bg-[#f5f0e9]'}`}>
              {activeView === 'result' && (resultImage
                ? <img src={resultImage} alt="Your virtual try-on result" className="max-h-[680px] max-w-full rounded-lg object-contain" />
                : <span className="text-sm text-[#827a78]">Try-on result image unavailable.</span>)}
              {activeView === 'landmarks' && (
                <img src={landmarkImage} alt="Pose landmark visualization" className="max-h-[680px] max-w-full rounded-lg object-contain" />
              )}
              {activeView === 'segmented' && (
                <img src={segmentedImage} alt="Person cutout with background removed" className="max-h-[680px] max-w-full object-contain" />
              )}
              {activeView === 'mask' && (
                <img src={segmentationMask} alt="Grayscale person segmentation mask" className="max-h-[680px] max-w-full object-contain" />
              )}
            </div>
          )}
          {(segmentationMethod || segmentationWarning) && (
            <div className="border-t border-[#eee7df] px-4 py-3 text-xs text-[#827a78] sm:px-5">
              {segmentationMethod && <p>Segmentation method: <span className="font-medium text-[#35313a]">{segmentationMethod}</span></p>}
              {segmentationWarning && <p role="status" className="mt-1 text-amber-800">Segmentation note: {segmentationWarning}</p>}
            </div>
          )}
        </section>

        <aside className="space-y-4">
          <section className="app-card p-4">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-[#35313a]"><Layers className="h-4 w-4 text-[#c6a46a]" /> The pieces</h2>
            <div className="mt-4 grid grid-cols-2 gap-3">
              {[
                ['Your photo', personImage],
                ['Selected garment', dressImage],
              ].map(([label, image]) => (
                <div key={label}>
                  <div className="flex h-36 items-center justify-center overflow-hidden rounded-xl bg-[#f5f0e9] p-2">
                    {image ? <img src={image} alt={label} className="max-h-full max-w-full object-contain" /> : <ImageIcon className="h-5 w-5 text-[#b4a9a2]" />}
                  </div>
                  <p className="mt-2 truncate text-[11px] font-medium text-[#827a78]">{label}</p>
                </div>
              ))}
            </div>
          </section>

          <details className="app-card group">
            <summary className="flex cursor-pointer list-none items-center justify-between p-4">
              <span className="flex items-center gap-2 text-sm font-semibold text-[#35313a]"><Activity className="h-4 w-4 text-[#c6a46a]" /> Fit analysis</span>
              <span className="text-xs text-[#827a78] group-open:rotate-180">⌄</span>
            </summary>
            <div className="border-t border-[#eee7df] px-4 pb-4 pt-3">
              <p className="mb-3 text-xs text-[#827a78]">
                {bodyAnalysis?.body_type_shape ? `${bodyAnalysis.body_type_shape} shape estimate` : 'Body shape estimate unavailable'}
              </p>
              <dl className="grid grid-cols-2 gap-2">
                {[
                  ['Shoulder', bodyAnalysis?.shoulder_width_px],
                  ['Waist', bodyAnalysis?.waist_width_px],
                  ['Hip', bodyAnalysis?.hip_width_px],
                  ['Arm length', bodyAnalysis?.arm_length_px],
                  ['Leg length', bodyAnalysis?.leg_length_px],
                  ['Torso / leg', bodyAnalysis?.body_ratio],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-lg bg-[#faf7f2] p-2.5">
                    <dt className="text-[10px] text-[#827a78]">{label}</dt>
                    <dd className="mt-1 text-xs font-semibold text-[#35313a]">{label === 'Torso / leg' ? value ?? '—' : formatPixelMetric(value)}</dd>
                  </div>
                ))}
              </dl>
              <p className="mt-3 text-[10px] leading-4 text-[#827a78]">Distances are image-space pixels, not calibrated body measurements.</p>
              {unusableLandmarks.length > 0 && (
                <p className="mt-2 text-[10px] leading-4 text-amber-800">
                  {unusableLandmarks.length} landmarks may be unreliable: {unusableLandmarks.map((landmark) => landmark.name).join(', ')}.
                </p>
              )}
            </div>
          </details>

        </aside>
      </div>
    </main>
  );
};

export default Result;
