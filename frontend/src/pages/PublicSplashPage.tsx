import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
    Home, Eye, X, ScanSearch, ArrowRight, CalendarCheck, LogIn,
    AlertTriangle, MapPin, Phone, Mail, Instagram, Layers,
    ShieldCheck, MessageSquare, Menu,
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

/* ─────────────────── Modal Shell ─────────────────── */
function Modal({ open, onClose, children }: { open: boolean; onClose: () => void; children: React.ReactNode }) {
    if (!open) return null
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
            <div
                className="relative w-full max-w-md rounded-2xl p-8 animate-[fadeUp_0.25s_ease-out]"
                style={{ background: 'rgba(18,18,18,0.97)', border: '1px solid rgba(255,255,255,0.08)' }}
            >
                <button onClick={onClose} className="absolute top-4 right-4 p-1 rounded-lg text-gray-500 hover:text-white hover:bg-white/10 transition-colors">
                    <X className="h-5 w-5" />
                </button>
                {children}
            </div>
        </div>
    )
}

/* ─────────────────── Main Page ─────────────────── */
export default function PublicSplashPage() {
    const navigate = useNavigate()
    const { login, isLoading, error, isAuthenticated, user } = useAuth()

    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
    const [showTokenModal, setShowTokenModal] = useState(false)
    const [showLoginModal, setShowLoginModal] = useState(false)
    const [showConsultModal, setShowConsultModal] = useState(false)
    const [tokenValue, setTokenValue] = useState('')
    const [loginForm, setLoginForm] = useState({ username: '', password: '' })
    const [consultForm, setConsultForm] = useState({ carBrand: '', carModel: '', regYear: '', phone: '', email: '' })
    const [consultSubmitted, setConsultSubmitted] = useState(false)
    const tokenRef = useRef<HTMLInputElement>(null)
    const usernameRef = useRef<HTMLInputElement>(null)

    // After successful login, navigate away
    useEffect(() => {
        if (isAuthenticated && user) {
            if (user.is_temporary_password) {
                navigate('/change-password', { replace: true })
            } else {
                navigate('/admin/dashboard', { replace: true })
            }
        }
    }, [isAuthenticated, user, navigate])

    // Auto-focus inputs when modals open
    useEffect(() => { if (showTokenModal) setTimeout(() => tokenRef.current?.focus(), 100) }, [showTokenModal])
    useEffect(() => { if (showLoginModal) setTimeout(() => usernameRef.current?.focus(), 100) }, [showLoginModal])

    const handleTokenSubmit = () => {
        if (tokenValue.length === 6) {
            window.location.href = `/track/${tokenValue}`
        }
    }

    const handleLoginSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        await login(loginForm)
    }

    return (
        <div className="min-h-screen bg-matte-black text-white flex flex-col">

            {/* ═══════════ NAVBAR ═══════════ */}
            <nav className="sticky top-0 z-40 w-full border-b border-white/10 bg-matte-black/90 backdrop-blur-md">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-20">
                    {/* Logo */}
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-deep-charcoal border border-electric-blue/50 rounded-full flex items-center justify-center">
                            <span className="text-electric-blue font-bold text-xl">R</span>
                        </div>
                        <span className="text-white font-bold text-xl tracking-wider">RG AUTO</span>
                    </div>

                    {/* Nav links */}
                    <div className="hidden md:flex items-center gap-7">
                        <a href="#top" className="flex items-center gap-1.5 text-gray-300 hover:text-electric-blue text-base font-medium px-3 py-1.5 rounded-lg hover:bg-electric-blue/10 transition-all">
                            <Home className="w-4 h-4" />
                            Home
                        </a>
                        <button
                            onClick={() => setShowConsultModal(true)}
                            className="flex items-center gap-1.5 text-gray-300 hover:text-electric-blue text-base font-medium px-3 py-1.5 rounded-lg hover:bg-electric-blue/10 transition-all"
                        >
                            <MessageSquare className="w-4 h-4" />
                            BOOK CONSULTATION
                        </button>
                        <a href="#book" className="flex items-center gap-1.5 text-gray-300 hover:text-electric-blue text-base font-medium px-3 py-1.5 rounded-lg hover:bg-electric-blue/10 transition-all">
                            <CalendarCheck className="w-4 h-4" />
                            BOOK SERVICE
                        </a>
                        <button
                            onClick={() => setShowTokenModal(true)}
                            className="flex items-center gap-1.5 text-gray-300 hover:text-electric-blue text-base font-medium px-3 py-1.5 rounded-lg hover:bg-electric-blue/10 transition-all"
                        >
                            <Eye className="w-4 h-4" />
                            LIVE BAY
                        </button>
                        <button
                            onClick={() => setShowLoginModal(true)}
                            className="flex items-center gap-1.5 text-gray-300 hover:text-electric-blue text-base font-medium px-3 py-1.5 rounded-lg hover:bg-electric-blue/10 transition-all"
                        >
                            <LogIn className="w-4 h-4" />
                            LOGIN
                        </button>
                    </div>

                    {/* Mobile hamburger */}
                    <button
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        className="md:hidden p-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
                    >
                        {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                    </button>
                </div>

                {/* Mobile dropdown menu */}
                {mobileMenuOpen && (
                    <div className="md:hidden border-t border-white/10 bg-matte-black/95 backdrop-blur-md px-4 py-3 space-y-1">
                        <a
                            href="#top"
                            onClick={() => setMobileMenuOpen(false)}
                            className="flex items-center gap-2.5 text-gray-300 hover:text-electric-blue text-sm font-medium px-3 py-2.5 rounded-lg hover:bg-electric-blue/10 transition-all"
                        >
                            <Home className="w-4 h-4" />
                            Home
                        </a>
                        <button
                            onClick={() => { setShowConsultModal(true); setMobileMenuOpen(false) }}
                            className="w-full flex items-center gap-2.5 text-gray-300 hover:text-electric-blue text-sm font-medium px-3 py-2.5 rounded-lg hover:bg-electric-blue/10 transition-all"
                        >
                            <MessageSquare className="w-4 h-4" />
                            Book Consultation
                        </button>
                        <a
                            href="#book"
                            onClick={() => setMobileMenuOpen(false)}
                            className="flex items-center gap-2.5 text-gray-300 hover:text-electric-blue text-sm font-medium px-3 py-2.5 rounded-lg hover:bg-electric-blue/10 transition-all"
                        >
                            <CalendarCheck className="w-4 h-4" />
                            Book Service
                        </a>
                        <button
                            onClick={() => { setShowTokenModal(true); setMobileMenuOpen(false) }}
                            className="w-full flex items-center gap-2.5 text-gray-300 hover:text-electric-blue text-sm font-medium px-3 py-2.5 rounded-lg hover:bg-electric-blue/10 transition-all"
                        >
                            <Eye className="w-4 h-4" />
                            Live Bay
                        </button>
                        <button
                            onClick={() => { setShowLoginModal(true); setMobileMenuOpen(false) }}
                            className="w-full flex items-center gap-2.5 text-gray-300 hover:text-electric-blue text-sm font-medium px-3 py-2.5 rounded-lg hover:bg-electric-blue/10 transition-all"
                        >
                            <LogIn className="w-4 h-4" />
                            Login
                        </button>
                    </div>
                )}
            </nav>

            {/* ═══════════ HERO SECTION ═══════════ */}
            <section id="top" className="relative w-full overflow-hidden">
                {/* Subtle ambient glow */}
                <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 50% 40%, rgba(0,240,255,0.08) 0%, transparent 60%)' }} />

                <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-28 text-center">
                    <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight mb-5">
                        Transparency in{' '}
                        <span className="text-electric-blue">Every Micron.</span>
                    </h1>
                    <p className="text-gray-400 text-base md:text-lg max-w-2xl mx-auto font-light leading-relaxed">
                        Experience the future of vehicle detailing. From Paint Protection Film to intricate corrections, watch your vehicle's transformation in real-time through our digital showroom.
                    </p>
                </div>
            </section>

            {/* ═══════════ PREMIUM PROTECTION SECTION ═══════════ */}
            <section className="relative w-full bg-matte-black">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                        {/* Video — left */}
                        <div className="relative rounded-2xl overflow-hidden border border-white/10 bg-black/40 aspect-video">
                            <video
                                className="absolute inset-0 w-full h-full object-cover"
                                autoPlay muted loop playsInline
                            >
                                <source src="/videos/ppf-comparison.mp4" type="video/mp4" />
                            </video>
                        </div>

                        {/* Text — right (matches Section 3 sizing) */}
                        <div>
                            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">
                                Premium{' '}
                                <span className="text-electric-blue">Protection</span>
                            </h2>
                            <p className="text-gray-400 text-base leading-relaxed mb-8 max-w-lg">
                                Our climate-controlled facility ensures flawless PPF application. Every variable — temperature, humidity, airflow — is precision-managed and logged in real time.
                            </p>

                            {/* Comparison rows */}
                            <div className="space-y-5">
                                <div className="flex items-start gap-4">
                                    <div className="mt-0.5 w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center flex-shrink-0">
                                        <AlertTriangle className="w-5 h-5 text-amber-400" />
                                    </div>
                                    <div>
                                        <h4 className="text-amber-400 font-bold text-sm mb-1">Uncontrolled</h4>
                                        <p className="text-gray-500 text-sm">Dust · Humidity · Orange peel · No logging</p>
                                    </div>
                                </div>

                                <div className="flex items-start gap-4">
                                    <div className="mt-0.5 w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center flex-shrink-0">
                                        <ShieldCheck className="w-5 h-5 text-emerald-400" />
                                    </div>
                                    <div>
                                        <h4 className="text-emerald-400 font-bold text-sm mb-1">Controlled</h4>
                                        <p className="text-gray-500 text-sm">HEPA · 24°C · Flawless · Telemetry</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ═══════════ LIVE BAY EXPERIENCE SECTION ═══════════ */}
            <section className="relative w-full bg-deep-charcoal/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                        {/* Text content */}
                        <div>
                            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">
                                The{' '}
                                <span className="text-champagne-gold">Live Bay</span>{' '}
                                Experience
                            </h2>
                            <p className="text-gray-400 text-base leading-relaxed mb-8 max-w-lg">
                                Trust is built on visibility. Access our HD live feeds 24/7 to monitor your vehicle's progress. Witness the precision of our master detailers from anywhere in the world.
                            </p>

                            {/* Features */}
                            <div className="space-y-5">
                                <div className="flex items-start gap-4">
                                    <div className="mt-0.5 w-9 h-9 rounded-lg bg-electric-blue/10 border border-electric-blue/30 flex items-center justify-center flex-shrink-0">
                                        <ShieldCheck className="w-5 h-5 text-electric-blue" />
                                    </div>
                                    <div>
                                        <h4 className="text-white font-bold text-sm mb-1">Uncompromised Protection</h4>
                                        <p className="text-gray-500 text-sm">Industry-leading PPF and ceramic coatings.</p>
                                    </div>
                                </div>

                                <div className="flex items-start gap-4">
                                    <div className="mt-0.5 w-9 h-9 rounded-lg bg-electric-blue/10 border border-electric-blue/30 flex items-center justify-center flex-shrink-0">
                                        <Layers className="w-5 h-5 text-electric-blue" />
                                    </div>
                                    <div>
                                        <h4 className="text-white font-bold text-sm mb-1">Layer-by-Layer Report</h4>
                                        <p className="text-gray-500 text-sm">Detailed logs of every correction and application.</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Video */}
                        <div className="relative rounded-2xl overflow-hidden border border-white/10 bg-black/40 aspect-video group cursor-pointer"
                             onClick={() => setShowTokenModal(true)}
                        >
                            <video
                                className="w-full h-full object-cover"
                                autoPlay muted loop playsInline
                            >
                                <source src="/videos/live-bay-preview.mp4" type="video/mp4" />
                            </video>
                            {/* Hover overlay */}
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                                <div className="flex flex-col items-center gap-3">
                                    <div className="w-16 h-16 rounded-full bg-white/10 border border-white/20 flex items-center justify-center backdrop-blur-sm">
                                        <Eye className="w-7 h-7 text-white" />
                                    </div>
                                    <span className="text-white text-sm font-medium tracking-wider uppercase">Enter Live Bay</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ═══════════ FOOTER ═══════════ */}
            <footer className="w-full bg-matte-black border-t border-white/10 pt-10 pb-6">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                        <div>
                            <h3 className="text-xl font-bold text-white mb-4 tracking-wider">RG <span className="text-electric-blue">AUTO STUDIO</span></h3>
                            <p className="text-gray-400 text-sm leading-relaxed max-w-xs">
                                Redefining automotive perfection through transparency and precision. Experience the pinnacle of detailing and protection.
                            </p>
                        </div>

                        <div>
                            <h4 className="text-lg font-semibold text-white mb-4">Contact</h4>
                            <div className="space-y-3">
                                <div className="flex items-center space-x-3 text-gray-400">
                                    <MapPin className="w-4 h-4 text-champagne-gold flex-shrink-0" />
                                    <span className="text-sm">Okhla Phase III, New Delhi</span>
                                </div>
                                <div className="flex items-center space-x-3 text-gray-400">
                                    <MapPin className="w-4 h-4 text-champagne-gold flex-shrink-0" />
                                    <span className="text-sm">Sector 29, Gurgaon</span>
                                </div>
                                <div className="flex items-center space-x-3 text-gray-400">
                                    <Phone className="w-4 h-4 text-electric-blue flex-shrink-0" />
                                    <span className="text-sm">+91 98765 43210</span>
                                </div>
                                <div className="flex items-center space-x-3 text-gray-400">
                                    <MapPin className="w-4 h-4 text-champagne-gold flex-shrink-0" />
                                    <span className="text-sm">Vikaspuri, New Delhi</span>
                                </div>
                                <div className="flex items-center space-x-3 text-gray-400">
                                    <Mail className="w-4 h-4 text-electric-blue flex-shrink-0" />
                                    <span className="text-sm">rahulgupta@rgautostudio.com</span>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h4 className="text-lg font-semibold text-white mb-4">Connect</h4>
                            <a href="https://instagram.com/rgautostudio" target="_blank" rel="noopener noreferrer" className="inline-flex items-center space-x-2 text-gray-400 hover:text-electric-blue transition-colors">
                                <Instagram className="w-5 h-5" />
                                <span>@rgautostudio</span>
                            </a>
                        </div>
                    </div>

                    <div className="border-t border-white/5 pt-6 flex flex-col md:flex-row justify-between items-center text-xs text-gray-500">
                        <p>&copy; {new Date().getFullYear()} RG Auto Studio. All rights reserved.</p>
                        <div className="flex space-x-4 mt-4 md:mt-0">
                            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
                            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
                        </div>
                    </div>
                </div>
            </footer>

            {/* ═══════════ TOKEN MODAL ═══════════ */}
            <Modal open={showTokenModal} onClose={() => { setShowTokenModal(false); setTokenValue('') }}>
                <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-electric-blue/10 border border-electric-blue/30 mb-4">
                        <ScanSearch className="w-6 h-6 text-electric-blue" />
                    </div>
                    <h2 className="text-xl font-bold text-white">View Live Bay</h2>
                    <p className="text-sm text-gray-500 mt-1">Enter your 6-character tracking code</p>
                </div>

                <div className="space-y-4">
                    <input
                        ref={tokenRef}
                        type="text"
                        maxLength={6}
                        value={tokenValue}
                        onChange={(e) => setTokenValue(e.target.value.toUpperCase())}
                        onKeyDown={(e) => { if (e.key === 'Enter') handleTokenSubmit() }}
                        placeholder="ABC123"
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white text-center font-mono text-2xl tracking-[0.4em] placeholder-gray-600 focus:outline-none focus:border-electric-blue/50 transition-colors"
                    />
                    <button
                        onClick={handleTokenSubmit}
                        disabled={tokenValue.length !== 6}
                        className="w-full flex items-center justify-center gap-2 bg-electric-blue text-black font-bold py-3.5 rounded-xl hover:brightness-110 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                        Enter Live Bay
                        <ArrowRight className="w-5 h-5" />
                    </button>
                </div>
            </Modal>

            {/* ═══════════ LOGIN MODAL ═══════════ */}
            <Modal open={showLoginModal} onClose={() => setShowLoginModal(false)}>
                <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-electric-blue/10 border border-electric-blue/30 mb-4">
                        <span className="text-electric-blue font-bold text-xl">R</span>
                    </div>
                    <h2 className="text-xl font-bold text-white">Staff Login</h2>
                    <p className="text-sm text-gray-500 mt-1">Sign in to your account</p>
                </div>

                <form onSubmit={handleLoginSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Username</label>
                        <input
                            ref={usernameRef}
                            type="text"
                            autoComplete="username"
                            value={loginForm.username}
                            onChange={(e) => setLoginForm(f => ({ ...f, username: e.target.value }))}
                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-electric-blue/50 transition-colors"
                            placeholder="Enter your username"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Password</label>
                        <input
                            type="password"
                            autoComplete="current-password"
                            value={loginForm.password}
                            onChange={(e) => setLoginForm(f => ({ ...f, password: e.target.value }))}
                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-electric-blue/50 transition-colors"
                            placeholder="Enter your password"
                        />
                    </div>

                    {error && (
                        <div className="flex items-start gap-2 p-3 rounded-lg border border-red-500/30 bg-red-500/10">
                            <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                            <p className="text-sm text-red-400">{error}</p>
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isLoading || !loginForm.username || !loginForm.password}
                        className="w-full bg-white text-black font-bold py-3.5 rounded-xl hover:bg-gray-100 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        {isLoading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>
            </Modal>

            {/* ═══════════ CONSULTATION MODAL ═══════════ */}
            <Modal open={showConsultModal} onClose={() => { setShowConsultModal(false); setConsultSubmitted(false); setConsultForm({ carBrand: '', carModel: '', regYear: '', phone: '', email: '' }) }}>
                {consultSubmitted ? (
                    <div className="text-center py-4">
                        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-emerald-500/10 border border-emerald-500/30 mb-4">
                            <ShieldCheck className="w-6 h-6 text-emerald-400" />
                        </div>
                        <h2 className="text-xl font-bold text-white mb-2">Request Submitted!</h2>
                        <p className="text-sm text-gray-400">We'll get back to you shortly.</p>
                    </div>
                ) : (
                    <>
                        <div className="text-center mb-6">
                            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-electric-blue/10 border border-electric-blue/30 mb-4">
                                <MessageSquare className="w-6 h-6 text-electric-blue" />
                            </div>
                            <h2 className="text-xl font-bold text-white">Book Consultation</h2>
                            <p className="text-sm text-gray-500 mt-1">Tell us about your vehicle</p>
                        </div>

                        <form onSubmit={(e) => { e.preventDefault(); setConsultSubmitted(true) }} className="space-y-3">
                            <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Car Brand</label>
                                <input
                                    type="text"
                                    value={consultForm.carBrand}
                                    onChange={(e) => setConsultForm(f => ({ ...f, carBrand: e.target.value }))}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-electric-blue/50 transition-colors"
                                    placeholder="e.g. BMW, Mercedes, Audi"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Car Model</label>
                                <input
                                    type="text"
                                    value={consultForm.carModel}
                                    onChange={(e) => setConsultForm(f => ({ ...f, carModel: e.target.value }))}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-electric-blue/50 transition-colors"
                                    placeholder="e.g. 3 Series, C-Class"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Registration Year</label>
                                <input
                                    type="number"
                                    min="2000"
                                    max={new Date().getFullYear()}
                                    value={consultForm.regYear}
                                    onChange={(e) => setConsultForm(f => ({ ...f, regYear: e.target.value }))}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-electric-blue/50 transition-colors"
                                    placeholder="e.g. 2024"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Phone Number</label>
                                <input
                                    type="tel"
                                    value={consultForm.phone}
                                    onChange={(e) => setConsultForm(f => ({ ...f, phone: e.target.value }))}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-electric-blue/50 transition-colors"
                                    placeholder="+91 98765 43210"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">Email</label>
                                <input
                                    type="email"
                                    value={consultForm.email}
                                    onChange={(e) => setConsultForm(f => ({ ...f, email: e.target.value }))}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-electric-blue/50 transition-colors"
                                    placeholder="your@email.com"
                                    required
                                />
                            </div>
                            <button
                                type="submit"
                                className="w-full bg-electric-blue text-black font-bold py-3.5 rounded-xl hover:brightness-110 transition-all mt-2"
                            >
                                Submit Request
                            </button>
                        </form>
                    </>
                )}
            </Modal>

            {/* ═══════════ ANIMATIONS ═══════════ */}
            <style>{`
                @keyframes fadeUp {
                    from { opacity: 0; transform: translateY(16px); }
                    to   { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    )
}
