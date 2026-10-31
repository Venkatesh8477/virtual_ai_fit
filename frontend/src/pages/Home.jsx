import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowDown, ArrowRight, Sparkles, WandSparkles } from 'lucide-react';

const heroImage = 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=1200&q=85';

const Home = () => (
  <main className="fade-in">
    <section className="mx-auto grid max-w-7xl items-center gap-12 px-4 pb-20 pt-12 sm:px-6 md:grid-cols-[0.92fr_1.08fr] md:py-20 lg:gap-20 lg:px-8">
      <div className="relative z-10">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#e5ddd3] bg-white/75 px-3.5 py-2 text-xs font-semibold uppercase tracking-[0.11em] text-[#722f37]">
          <Sparkles className="h-3.5 w-3.5 text-[#c6a46a]" /> A new way to get dressed
        </div>
        <h1 className="font-editorial max-w-xl text-5xl font-medium leading-[1.06] tracking-[-0.04em] text-[#241522] sm:text-6xl lg:text-[4.5rem]">
          Your style,<br />
          <span className="italic text-[#722f37]">beautifully</span> reimagined.
        </h1>
        <p className="mt-6 max-w-lg text-base leading-7 text-[#746a6c] sm:text-lg sm:leading-8">
          Meet your personal fitting room. See how a look feels on you, explore the possibilities, and make getting dressed a little more delightful.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link to="/upload" className="btn-primary">
            Step into the studio <ArrowRight className="h-4 w-4" />
          </Link>
          <a href="#how-it-works" className="btn-secondary">
            How it works <ArrowDown className="h-4 w-4" />
          </a>
        </div>
        <div className="mt-10 flex items-center gap-3 border-t border-[#e5ddd3] pt-6">
          <div className="flex -space-x-2" aria-hidden="true">
            <span className="h-8 w-8 rounded-full border-2 border-[#faf7f2] bg-[#e5c5ae]" />
            <span className="h-8 w-8 rounded-full border-2 border-[#faf7f2] bg-[#aa7773]" />
            <span className="h-8 w-8 rounded-full border-2 border-[#faf7f2] bg-[#d7b979]" />
          </div>
          <p className="text-xs leading-5 text-[#827a78]">A thoughtful space to explore<br />your next favourite look.</p>
        </div>
      </div>

      <div className="relative mx-auto w-full max-w-[590px]">
        <div className="absolute -right-4 -top-5 h-28 w-28 rounded-full border border-[#d7c3a2] sm:-right-4 sm:-top-8 sm:h-40 sm:w-40 lg:-right-8" />
        <div className="relative h-[440px] overflow-hidden rounded-[42%_42%_18px_18px] bg-[#e9dbcf] sm:h-[570px]">
          <img src={heroImage} alt="Fashion editorial portrait in a warm, natural setting" className="h-full w-full object-cover object-center" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#241522]/45 via-transparent to-[#241522]/5" />
          <div className="absolute bottom-6 left-6 right-6 flex items-end justify-between text-white sm:bottom-8 sm:left-8 sm:right-8">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/75">The everyday edit</p>
              <p className="mt-1 font-editorial text-2xl sm:text-3xl">Made for your moment</p>
            </div>
            <span className="mb-1 rounded-full border border-white/35 bg-white/15 p-3 backdrop-blur">
              <WandSparkles className="h-5 w-5" />
            </span>
          </div>
        </div>
      </div>
    </section>

    <section id="how-it-works" className="border-y border-[#e9e0d6] bg-[#f4eee6]">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-20 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#9b725b]">A little style, a few steps</p>
          <h2 className="font-editorial mt-3 text-3xl text-[#241522] sm:text-4xl">Your fitting room, reimagined</h2>
          <p className="mt-4 text-sm leading-6 text-[#827a78]">No complicated setup. Just bring a photo and a piece you would love to try.</p>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            ['01', 'Add your photo', 'Choose a clear, full-length photo to get started.'],
            ['02', 'Pick a piece', 'Upload the garment you are curious to see on you.'],
            ['03', 'See the look', 'Let the studio create a preview you can explore.'],
          ].map(([number, title, text]) => (
            <article key={number} className="rounded-2xl border border-[#e5ddd3] bg-white p-6 sm:p-7">
              <span className="font-editorial text-3xl italic text-[#c6a46a]">{number}</span>
              <h3 className="mt-5 text-base font-semibold text-[#35313a]">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-[#827a78]">{text}</p>
            </article>
          ))}
        </div>
        <div className="mt-9 text-center">
          <Link to="/upload" className="btn-primary">Open the styling studio <ArrowRight className="h-4 w-4" /></Link>
        </div>
      </div>
    </section>
  </main>
);

export default Home;
