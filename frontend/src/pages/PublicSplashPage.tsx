import { Link } from 'react-router-dom'
import { Car, ScanSearch, ArrowRight } from 'lucide-react'

export default function PublicSplashPage() {
    return (
        <div className="min-h-screen bg-matte-black text-white relative overflow-hidden flex flex-col">
            {/* Background ambient light */}
            <div
                className="absolute inset-0 pointer-events-none"
                style={{
                    background: 'radial-gradient(circle at 50% 30%, rgba(0, 240, 255, 0.15) 0%, transparent 60%)',
                }}
            />

            {/* Grid pattern overlay */}
            <div
                className="absolute inset-0 pointer-events-none opacity-[0.03]"
                style={{
                    backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)',
                    backgroundSize: '40px 40px'
                }}
            />

            {/* Header */}
            <header className="relative z-10 w-full px-6 py-6 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div
                        className="h-10 w-10 rounded-xl flex items-center justify-center backdrop-blur-md"
                        style={{
                            background: 'rgba(0,240,255,0.1)',
                            border: '1px solid rgba(0,240,255,0.3)',
                            boxShadow: '0 0 20px rgba(0,240,255,0.2)',
                        }}
                    >
                        <span className="text-electric-blue font-bold tracking-wider">PPF</span>
                    </div>
                    <span className="font-bold tracking-widest uppercase text-sm text-gray-300">Auto Studio</span>
                </div>

                <Link
                    to="/login"
                    className="text-xs font-medium text-gray-400 hover:text-white transition-colors uppercase tracking-wider px-4 py-2 border border-white/10 rounded-full hover:bg-white/5"
                >
                    Staff Portal
                </Link>
            </header>

            {/* Main Hero Content */}
            <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 text-center pb-20">

                {/* Animated Icon */}
                <div className="relative mb-8 group">
                    <div className="absolute inset-0 bg-electric-blue/20 blur-2xl rounded-full scale-150 animate-pulse-slow" />
                    <div className="relative h-24 w-24 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-xl flex items-center justify-center transform transition-transform duration-500 ease-out hover:scale-105 hover:bg-white/10 origin-center overflow-hidden">
                        {/* Scanning line animation */}
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-electric-blue to-transparent filter drop-shadow-[0_0_8px_rgba(0,240,255,0.8)] animate-[scan_3s_ease-in-out_infinite]" />
                        <Car className="h-10 w-10 text-electric-blue opacity-90" />
                    </div>
                </div>

                <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6">
                    Premium <span className="text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-500">Protection</span>
                </h1>

                <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-12 font-light leading-relaxed">
                    Track your vehicle's paint protection journey in real-time. Uncompromising quality monitoring, direct to your device.
                </p>

                {/* Enter Token CTA */}
                <div className="w-full max-w-md mx-auto space-y-6">
                    <div className="relative group/input">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-electric-blue to-purple-600 rounded-2xl blur opacity-20 group-hover/input:opacity-50 transition duration-1000 group-hover/input:duration-200" />
                        <div className="relative bg-black/50 backdrop-blur-xl border border-white/10 rounded-2xl flex items-center p-2 focus-within:border-electric-blue/50 transition-colors">
                            <div className="pl-4 pr-3 py-3">
                                <ScanSearch className="h-5 w-5 text-gray-400" />
                            </div>
                            <input
                                id="token-input"
                                type="text"
                                placeholder="Enter your 6-character tracking token"
                                className="w-full bg-transparent border-none text-white placeholder-gray-500 focus:ring-0 focus:outline-none placeholder:font-light font-mono tracking-widest text-lg"
                                onChange={(e) => {
                                    const val = e.target.value.toUpperCase();
                                    e.target.value = val;
                                }}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        const val = (e.target as HTMLInputElement).value;
                                        if (val.length === 6) window.location.href = `/track/${val}`;
                                    }
                                }}
                            />
                        </div>
                    </div>

                    <button
                        onClick={() => {
                            const val = (document.getElementById('token-input') as HTMLInputElement).value;
                            if (val) window.location.href = `/track/${val}`;
                        }}
                        className="group relative w-full inline-flex items-center justify-center gap-3 bg-white text-black font-semibold py-4 px-8 rounded-xl overflow-hidden transition-all hover:scale-[1.02] active:scale-[0.98]"
                    >
                        <span className="relative z-10 text-base">View Live Bay Feed</span>
                        <ArrowRight className="relative z-10 w-5 h-5 transition-transform group-hover:translate-x-1" />
                        <div className="absolute inset-0 bg-gradient-to-r from-gray-200 to-white opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                </div>
            </main>

            {/* Footer */}
            <footer className="relative z-10 py-8 text-center border-t border-white/5 bg-black/20 backdrop-blur-sm">
                <p className="text-xs text-gray-500 font-mono">
                    Powered by PPF Workshop System <span className="mx-2 text-gray-700">|</span> Real-time Climate telemetry
                </p>
            </footer>

            <style>{`
        @keyframes scan {
          0%, 100% {
            transform: translateY(-200%);
            opacity: 0;
          }
          10%, 90% {
            opacity: 1;
          }
          50% {
            transform: translateY(120px);
          }
        }
      `}</style>
        </div>
    )
}
