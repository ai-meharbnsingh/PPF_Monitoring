/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect } from 'react';
import { GoogleGenAI } from "@google/genai";
import { motion, AnimatePresence } from "motion/react";
import { 
  ShieldCheck, 
  AlertTriangle, 
  Play, 
  Loader2, 
  CheckCircle2, 
  Thermometer, 
  Droplets, 
  Wind,
  ExternalLink,
  Key
} from 'lucide-react';

// Extend window for AI Studio API Key selection
declare global {
  interface Window {
    aistudio: {
      hasSelectedApiKey: () => Promise<boolean>;
      openSelectKey: () => Promise<void>;
    };
  }
}

const DEFAULT_PROMPT = `Cinematic split-screen comparison of a black Toyota Fortuner in a PPF workshop.

LEFT SIDE labeled "Uncontrolled Environment": dusty garage with harsh fluorescent lighting, visible dust particles floating in air, humidity condensation on surfaces, a technician struggling to apply PPF film that keeps trapping dust bubbles under the clear film, orange peel texture forming, edges lifting and peeling. The car paint looks dull with trapped contaminants under the PPF.

RIGHT SIDE labeled "Controlled Environment": a clean, climate-controlled professional PPF bay with soft diffused LED lighting, air looks crystal clear with no floating particles, digital monitoring displays showing temperature 24°C humidity 45% air quality excellent on a wall-mounted screen, technician smoothly applying PPF film that bonds perfectly with zero bubbles, the black paint gleams like a mirror under the clear PPF with a perfect wet-glass finish.

Shot transitions from wide establishing to close-up on the film surface showing the dramatic quality difference. Slow motion. 4K cinematic look, shallow depth of field, dramatic lighting contrast between the two sides.`;

export default function App() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState("");
  const [hasKey, setHasKey] = useState(false);

  const loadingMessages = [
    "Initializing cinematic engine...",
    "Simulating dust particles for uncontrolled environment...",
    "Calibrating soft LED lighting for professional bay...",
    "Applying virtual PPF film with precision...",
    "Rendering 4K wet-glass finish...",
    "Finalizing split-screen comparison...",
    "Polishing the black Toyota Fortuner's reflection..."
  ];

  useEffect(() => {
    const checkKey = async () => {
      if (window.aistudio) {
        const selected = await window.aistudio.hasSelectedApiKey();
        setHasKey(selected);
      }
    };
    checkKey();
  }, []);

  useEffect(() => {
    if (isGenerating) {
      let i = 0;
      const interval = setInterval(() => {
        setLoadingMessage(loadingMessages[i % loadingMessages.length]);
        i++;
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [isGenerating]);

  const handleSelectKey = async () => {
    if (window.aistudio) {
      await window.aistudio.openSelectKey();
      setHasKey(true);
    }
  };

  const generateVideo = async () => {
    setIsGenerating(true);
    setError(null);
    setVideoUrl(null);
    setLoadingMessage(loadingMessages[0]);

    try {
      const apiKey = (process.env as any).GEMINI_API_KEY;
      const ai = new GoogleGenAI({ apiKey });

      let operation = await ai.models.generateVideos({
        model: 'veo-3.1-fast-generate-preview',
        prompt: DEFAULT_PROMPT,
        config: {
          numberOfVideos: 1,
          resolution: '1080p',
          aspectRatio: '16:9'
        }
      });

      // Poll for completion
      while (!operation.done) {
        await new Promise(resolve => setTimeout(resolve, 10000));
        operation = await ai.operations.getVideosOperation({ operation: operation });
      }

      const downloadLink = operation.response?.generatedVideos?.[0]?.video?.uri;
      
      if (downloadLink) {
        const response = await fetch(downloadLink, {
          method: 'GET',
          headers: {
            'x-goog-api-key': apiKey,
          },
        });
        const blob = await response.blob();
        setVideoUrl(URL.createObjectURL(blob));
      } else {
        throw new Error("Video generation failed - no download link received.");
      }
    } catch (err: any) {
      console.error(err);
      if (err.message?.includes("Requested entity was not found")) {
        setError("API Key session expired. Please re-select your key.");
        setHasKey(false);
      } else {
        setError(err.message || "An unexpected error occurred during generation.");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans selection:bg-emerald-500/30">
      {/* Background Atmosphere */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-900/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-900/10 blur-[120px] rounded-full" />
      </div>

      <main className="relative z-10 max-w-7xl mx-auto px-6 py-12 lg:py-24">
        {/* Header Section */}
        <header className="mb-16 lg:mb-24">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 mb-6"
          >
            <div className="px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-bold tracking-widest uppercase">
              Professional Grade
            </div>
            <div className="h-px flex-1 bg-white/10" />
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-6xl lg:text-8xl font-black tracking-tighter leading-[0.9] uppercase mb-8"
          >
            Controlled <br />
            <span className="text-emerald-500">vs</span> Uncontrolled
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="max-w-2xl text-xl text-zinc-400 leading-relaxed"
          >
            Visualize the critical difference environment makes in PPF application. 
            From dusty garages to climate-controlled clean rooms—witness the 
            impact on your vehicle's finish.
          </motion.p>
        </header>

        {/* Action Section */}
        <section className="grid lg:grid-cols-2 gap-12 items-start">
          <div className="space-y-8">
            {!hasKey ? (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="p-8 rounded-3xl bg-zinc-900/50 border border-white/10 backdrop-blur-xl"
              >
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-2xl bg-amber-500/20 flex items-center justify-center text-amber-500">
                    <Key size={24} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold">API Key Required</h3>
                    <p className="text-zinc-400 text-sm">Veo video generation requires a paid API key.</p>
                  </div>
                </div>
                <p className="text-zinc-400 mb-8 text-sm leading-relaxed">
                  To generate this cinematic comparison, you must select a Google Cloud project with billing enabled. 
                  Visit <a href="https://ai.google.dev/gemini-api/docs/billing" target="_blank" className="text-emerald-400 underline">billing documentation</a> for more info.
                </p>
                <button 
                  onClick={handleSelectKey}
                  className="w-full py-4 rounded-2xl bg-white text-black font-bold hover:bg-emerald-500 transition-colors flex items-center justify-center gap-2"
                >
                  Select API Key
                </button>
              </motion.div>
            ) : (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-6 rounded-3xl bg-zinc-900/50 border border-white/10">
                    <AlertTriangle className="text-amber-500 mb-4" size={24} />
                    <h4 className="font-bold mb-2">Uncontrolled</h4>
                    <ul className="text-xs text-zinc-500 space-y-2">
                      <li>• Floating dust particles</li>
                      <li>• Fluorescent flicker</li>
                      <li>• Humidity bubbles</li>
                      <li>• Orange peel texture</li>
                    </ul>
                  </div>
                  <div className="p-6 rounded-3xl bg-emerald-500/10 border border-emerald-500/20">
                    <ShieldCheck className="text-emerald-500 mb-4" size={24} />
                    <h4 className="font-bold mb-2">Controlled</h4>
                    <ul className="text-xs text-zinc-400 space-y-2">
                      <li>• HEPA filtered air</li>
                      <li>• Diffused LED lighting</li>
                      <li>• 24°C / 45% Humidity</li>
                      <li>• Mirror-glass finish</li>
                    </ul>
                  </div>
                </div>

                <button 
                  onClick={generateVideo}
                  disabled={isGenerating}
                  className={`w-full py-6 rounded-3xl font-black text-xl uppercase tracking-widest flex items-center justify-center gap-3 transition-all ${
                    isGenerating 
                    ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' 
                    : 'bg-emerald-500 text-black hover:bg-emerald-400 hover:scale-[1.02] active:scale-[0.98]'
                  }`}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Play fill="currentColor" />
                      Generate Cinematic Comparison
                    </>
                  )}
                </button>

                {error && (
                  <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3">
                    <AlertTriangle size={18} />
                    {error}
                  </div>
                )}
              </div>
            )}

            {/* Technical Specs */}
            <div className="flex flex-wrap gap-6 pt-8 border-t border-white/10">
              <div className="flex items-center gap-2 text-zinc-500">
                <Thermometer size={16} />
                <span className="text-xs font-mono uppercase tracking-wider">24°C Optimized</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-500">
                <Droplets size={16} />
                <span className="text-xs font-mono uppercase tracking-wider">45% Humidity</span>
              </div>
              <div className="flex items-center gap-2 text-zinc-500">
                <Wind size={16} />
                <span className="text-xs font-mono uppercase tracking-wider">HEPA Grade</span>
              </div>
            </div>
          </div>

          {/* Video Preview Area */}
          <div className="relative aspect-video rounded-[2rem] overflow-hidden bg-zinc-900 border border-white/10 shadow-2xl group">
            <AnimatePresence mode="wait">
              {isGenerating ? (
                <motion.div 
                  key="loading"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 flex flex-col items-center justify-center p-12 text-center"
                >
                  <div className="w-24 h-24 mb-8 relative">
                    <div className="absolute inset-0 border-4 border-emerald-500/20 rounded-full" />
                    <div className="absolute inset-0 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                  <h3 className="text-2xl font-bold mb-2">Creating Vision</h3>
                  <p className="text-emerald-400 font-mono text-sm animate-pulse">{loadingMessage}</p>
                </motion.div>
              ) : videoUrl ? (
                <motion.div 
                  key="video"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="absolute inset-0"
                >
                  <video 
                    src={videoUrl} 
                    controls 
                    autoPlay 
                    loop 
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-6 right-6 flex gap-2">
                    <div className="px-3 py-1 rounded-lg bg-black/60 backdrop-blur-md border border-white/10 text-[10px] font-bold uppercase tracking-widest">
                      1080p Veo 3.1
                    </div>
                  </div>
                </motion.div>
              ) : (
                <motion.div 
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="absolute inset-0 flex flex-col items-center justify-center p-12 text-center bg-gradient-to-br from-zinc-900 to-black"
                >
                  <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Play className="text-zinc-600" size={32} />
                  </div>
                  <h3 className="text-xl font-bold text-zinc-500 mb-2">Ready to Visualize</h3>
                  <p className="text-zinc-600 text-sm max-w-xs">
                    Click generate to create the cinematic split-screen comparison.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </section>

        {/* Footer */}
        <footer className="mt-24 pt-12 border-t border-white/10 flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-4">
            <ShieldCheck className="text-emerald-500" />
            <span className="text-sm font-bold tracking-widest uppercase">PPF Master Quality Assurance</span>
          </div>
          <div className="flex gap-8">
            <a href="#" className="text-zinc-500 hover:text-white text-xs uppercase tracking-widest transition-colors">Case Studies</a>
            <a href="#" className="text-zinc-500 hover:text-white text-xs uppercase tracking-widest transition-colors">Equipment Specs</a>
            <a href="#" className="text-zinc-500 hover:text-white text-xs uppercase tracking-widest transition-colors flex items-center gap-2">
              Documentation <ExternalLink size={12} />
            </a>
          </div>
        </footer>
      </main>
    </div>
  );
}
