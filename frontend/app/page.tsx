import Link from "next/link";
import { SessionDisplay } from "@/components/auth/session-display";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a0f] text-[#ededed]">
      {/* ===== NAVBAR ===== */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/[0.06] bg-[#0a0a0f]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold gradient-text tracking-tight">
            Vyra
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-gray-400 hover:text-white transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="text-sm text-gray-400 hover:text-white transition-colors">
              How It Works
            </a>
            <a href="#pricing" className="text-sm text-gray-400 hover:text-white transition-colors">
              Pricing
            </a>
          </div>

          <div className="flex items-center gap-3">
            <SessionDisplay />
          </div>
        </div>
      </nav>

      {/* ===== HERO SECTION ===== */}
      <section className="relative pt-32 pb-20 md:pt-44 md:pb-32 overflow-hidden">
        {/* Background decorative orbs */}
        <div className="glow-orb w-[500px] h-[500px] bg-purple-600 -top-40 -left-40" />
        <div className="glow-orb w-[400px] h-[400px] bg-pink-500 top-20 -right-32" />
        <div className="glow-orb w-[300px] h-[300px] bg-violet-500 bottom-0 left-1/3" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Copy */}
            <div className="animate-fade-in-up">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-purple-500/20 bg-purple-500/5 text-purple-400 text-xs font-medium mb-6">
                <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
                AI-Powered Content Engine
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
                Create Stunning{" "}
                <span className="gradient-text">Instagram Content</span>{" "}
                With AI
              </h1>

              <p className="text-lg text-gray-400 mb-8 max-w-lg leading-relaxed">
                Automate your brand growth without losing your identity. Vyra uses
                advanced AI to maintain face consistency across all your posts,
                reels, and stories.
              </p>

              <div className="flex flex-wrap gap-4 mb-10">
                <Link href="/auth/signup" className="btn-gradient">
                  Start Creating Free
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </Link>
                <Link href="#how-it-works" className="btn-ghost">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Watch Demo
                </Link>
              </div>

              {/* Stats Row */}
              <div className="flex gap-8">
                <div>
                  <div className="text-2xl font-bold gradient-text">99.8%</div>
                  <div className="text-xs text-gray-500 mt-1">Identity Accuracy</div>
                </div>
                <div className="w-px bg-white/10" />
                <div>
                  <div className="text-2xl font-bold gradient-text">4K</div>
                  <div className="text-xs text-gray-500 mt-1">Ultra-HD Output</div>
                </div>
                <div className="w-px bg-white/10" />
                <div>
                  <div className="text-2xl font-bold gradient-text">3s</div>
                  <div className="text-xs text-gray-500 mt-1">Avg Generation</div>
                </div>
              </div>
            </div>

            {/* Right: Phone Mockup */}
            <div className="flex justify-center lg:justify-end animate-float">
              <div className="relative">
                {/* Glow behind phone */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 to-pink-500/20 blur-3xl rounded-full scale-110" />

                {/* Phone frame */}
                <div className="relative w-[280px] h-[560px] rounded-[2.5rem] border-2 border-white/10 bg-[#111118] p-3 shadow-2xl">
                  {/* Notch */}
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-28 h-6 bg-[#0a0a0f] rounded-b-2xl" />

                  {/* Screen content */}
                  <div className="w-full h-full rounded-[2rem] overflow-hidden bg-gradient-to-b from-purple-900/40 to-pink-900/30 flex flex-col">
                    {/* Mock IG Header */}
                    <div className="p-4 flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500" />
                      <div>
                        <div className="text-[10px] font-semibold text-white">vyra_creator</div>
                        <div className="text-[8px] text-gray-400">Sponsored</div>
                      </div>
                    </div>

                    {/* Mock Image Area */}
                    <div className="flex-1 mx-3 rounded-xl bg-gradient-to-br from-purple-600/30 via-pink-500/20 to-violet-500/30 flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-4xl mb-2">✨</div>
                        <div className="text-[10px] text-white/70 px-4">AI-Generated Content</div>
                      </div>
                    </div>

                    {/* Mock Actions */}
                    <div className="p-4 flex gap-4">
                      <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                      </svg>
                      <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                      </svg>
                    </div>

                    {/* Mock Caption */}
                    <div className="px-4 pb-4">
                      <div className="text-[9px] text-white/50">
                        <span className="font-semibold text-white/70">vyra_creator</span>{" "}
                        Living my best life ✨ #ai #content
                      </div>
                    </div>
                  </div>
                </div>

                {/* Floating badge */}
                <div className="absolute -right-4 top-16 glass-card px-3 py-2 animate-pulse-glow">
                  <div className="text-[10px] text-purple-400 font-medium">🔒 Identity Locked</div>
                  <div className="text-[9px] text-gray-500">Consistency: 99.8%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== SOCIAL PROOF ===== */}
      <div className="section-divider" />
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500 mb-8">
            Trusted by <span className="text-white font-medium">10,000+</span> top-tier creators
          </p>
          <div className="flex justify-center items-center gap-10 flex-wrap opacity-30">
            {["Instagram", "TikTok", "YouTube", "Meta", "Shopify"].map((brand) => (
              <span key={brand} className="text-lg font-bold tracking-wider text-gray-400 uppercase">
                {brand}
              </span>
            ))}
          </div>
        </div>
      </section>
      <div className="section-divider" />

      {/* ===== FEATURES SECTION ===== */}
      <section id="features" className="py-20 md:py-28 relative">
        <div className="glow-orb w-[400px] h-[400px] bg-purple-600 top-0 right-0 opacity-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Designed for the{" "}
              <span className="gradient-text">Next Generation</span>
            </h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              Stop wasting hours on manual editing. Vyra handles the heavy lifting
              so you can focus on strategy.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="glass-card p-8">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-600/20 to-pink-500/20 flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-3">Face Identity</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Our proprietary AI ensures your digital twin looks consistent across
                every single post, reel, and story. ≥0.95 identity strength guaranteed.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="glass-card p-8">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-600/20 to-pink-500/20 flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-3">Smart Presets</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Choose from Luxury, Lifestyle, and Beauty presets specifically
                trained for high-engagement Instagram aesthetics.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="glass-card p-8">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-600/20 to-pink-500/20 flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-3">4K Export</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Don&apos;t settle for blurry uploads. Get ultra-sharp 4K exports in
                9:16 Reels, 4:5 Feed, and 1:1 Square — optimized for the algorithm.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== HOW IT WORKS ===== */}
      <section id="how-it-works" className="py-20 md:py-28 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Three Steps to{" "}
              <span className="gradient-text">Viral Content</span>
            </h2>
          </div>

          <div className="relative">
            {/* Connector Line */}
            <div className="hidden md:block step-connector top-20" />

            <div className="grid md:grid-cols-3 gap-8 relative z-10">
              {[
                {
                  step: "01",
                  title: "Upload Assets",
                  desc: "Upload a single photo of yourself or your brand's core elements.",
                  icon: (
                    <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  ),
                },
                {
                  step: "02",
                  title: "Choose Style",
                  desc: "Select from AI-driven presets and content formats that match your brand.",
                  icon: (
                    <svg className="w-6 h-6 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                    </svg>
                  ),
                },
                {
                  step: "03",
                  title: "Launch Content",
                  desc: "Export high-resolution files with captions, hashtags, and location tags.",
                  icon: (
                    <svg className="w-6 h-6 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  ),
                },
              ].map((item) => (
                <div key={item.step} className="glass-card p-8 text-center">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-600/20 to-pink-500/20 flex items-center justify-center mx-auto mb-5">
                    {item.icon}
                  </div>
                  <div className="text-xs font-bold text-purple-400 tracking-widest mb-2">
                    STEP {item.step}
                  </div>
                  <h3 className="text-lg font-semibold mb-3">{item.title}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ===== PRICING ===== */}
      <section id="pricing" className="py-20 md:py-28 relative">
        <div className="glow-orb w-[500px] h-[500px] bg-pink-600 bottom-0 left-1/4 opacity-10" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Simple,{" "}
              <span className="gradient-text">Transparent</span> Pricing
            </h2>
            <p className="text-gray-400 max-w-md mx-auto">
              Choose the plan that fits your growth ambitions.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
            {/* Free Plan */}
            <div className="glass-card p-8 flex flex-col">
              <h3 className="text-xl font-semibold mb-1">Free</h3>
              <p className="text-sm text-gray-500 mb-6">Perfect for exploring the AI</p>

              <div className="mb-8">
                <span className="text-4xl font-bold">$0</span>
                <span className="text-gray-500 text-sm ml-1">/month</span>
              </div>

              <ul className="space-y-4 mb-8 flex-1">
                {[
                  { text: "5 AI Generations / mo", included: true },
                  { text: "Standard Resolution", included: true },
                  { text: "Basic Templates", included: true },
                  { text: "Face Consistency", included: false },
                ].map((item) => (
                  <li key={item.text} className="flex items-center gap-3 text-sm">
                    {item.included ? (
                      <svg className="w-5 h-5 text-green-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-gray-600 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    )}
                    <span className={item.included ? "text-gray-300" : "text-gray-600"}>
                      {item.text}
                    </span>
                  </li>
                ))}
              </ul>

              <Link href="/auth/signup" className="btn-ghost text-center justify-center">
                Get Started
              </Link>
            </div>

            {/* Pro Plan */}
            <div className="gradient-border-card p-8 flex flex-col relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-purple-600 to-pink-500 text-xs font-bold text-white">
                MOST POPULAR
              </div>

              <h3 className="text-xl font-semibold mb-1">Pro</h3>
              <p className="text-sm text-gray-500 mb-6">For serious creators & brands</p>

              <div className="mb-8">
                <span className="text-4xl font-bold gradient-text">$19</span>
                <span className="text-gray-500 text-sm ml-1">/month</span>
              </div>

              <ul className="space-y-4 mb-8 flex-1">
                {[
                  "Unlimited Generations",
                  "4K Ultra-HD Export",
                  "Face Identity Consistency",
                  "Priority GPU Rendering",
                  "No Watermark",
                ].map((text) => (
                  <li key={text} className="flex items-center gap-3 text-sm">
                    <svg className="w-5 h-5 text-purple-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-300">{text}</span>
                  </li>
                ))}
              </ul>

              <Link href="/auth/signup" className="btn-gradient text-center justify-center">
                Upgrade to Pro
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FINAL CTA ===== */}
      <section className="py-20 md:py-28 relative overflow-hidden">
        <div className="glow-orb w-[600px] h-[600px] bg-purple-600 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-15" />

        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Ready to{" "}
            <span className="gradient-text">Transform</span> Your Content?
          </h2>
          <p className="text-gray-400 mb-8 max-w-lg mx-auto">
            Join 10,000+ creators who use Vyra to automate their Instagram
            content while maintaining perfect brand identity.
          </p>
          <div className="flex justify-center gap-4">
            <Link href="/auth/signup" className="btn-gradient text-lg px-10 py-4">
              Get Started Free
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <div className="section-divider" />
      <footer className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-10 mb-12">
            {/* Brand */}
            <div>
              <Link href="/" className="text-2xl font-bold gradient-text tracking-tight">
                Vyra
              </Link>
              <p className="text-sm text-gray-500 mt-3 leading-relaxed">
                Empowering the next generation of digital creators with
                cutting-edge AI automation.
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-4">Product</h4>
              <ul className="space-y-2.5">
                {["Features", "Templates", "AI Models", "Releases"].map((item) => (
                  <li key={item}>
                    <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-4">Resources</h4>
              <ul className="space-y-2.5">
                {["Documentation", "Help Center", "Blog", "Tutorials"].map((item) => (
                  <li key={item}>
                    <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Company */}
            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-4">Company</h4>
              <ul className="space-y-2.5">
                {["About Us", "Contact", "Privacy Policy", "Terms of Service"].map((item) => (
                  <li key={item}>
                    <a href="#" className="text-sm text-gray-500 hover:text-white transition-colors">
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="border-t border-white/5 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-600">
              &copy; 2026 Vyra. All rights reserved.
            </p>
            <div className="flex gap-5">
              {/* Twitter/X */}
              <a href="#" className="text-gray-600 hover:text-white transition-colors" aria-label="Twitter">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
              {/* Instagram */}
              <a href="#" className="text-gray-600 hover:text-white transition-colors" aria-label="Instagram">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
                </svg>
              </a>
              {/* GitHub */}
              <a href="#" className="text-gray-600 hover:text-white transition-colors" aria-label="GitHub">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
