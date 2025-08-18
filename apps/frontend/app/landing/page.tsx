"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Lock,
  Unlock,
  Star,
  Users,
  Trophy,
  Brain,
  PlayCircle,
  Check,
  X,
  ArrowRight,
  Zap,
  Shield,
  Gift,
  TrendingUp,
  Clock,
  Youtube,
  FileText,
  BarChart3,
  Gamepad2,
  Crown,
  Flame
} from "lucide-react";

export default function FreemiumLandingPage() {
  const router = useRouter();
  const [selectedPlan, setSelectedPlan] = useState<"free" | "premium">("free");
  const [showVideo, setShowVideo] = useState(false);

  const features = {
    free: [
      { icon: Check, text: "10 preguntas diarias", available: true },
      { icon: Check, text: "1 diagnóstico mensual", available: true },
      { icon: Check, text: "Plan de estudio básico", available: true },
      { icon: Check, text: "Videos de YouTube", available: true },
      { icon: Check, text: "Sistema de rangos (E-B)", available: true },
      { icon: X, text: "Explicaciones IA ilimitadas", available: false },
      { icon: X, text: "Simulacros completos", available: false },
      { icon: X, text: "Análisis avanzado", available: false },
      { icon: X, text: "Sin anuncios", available: false },
      { icon: X, text: "Soporte prioritario", available: false }
    ],
    premium: [
      { icon: Check, text: "Preguntas ILIMITADAS", available: true },
      { icon: Check, text: "Diagnósticos ILIMITADOS", available: true },
      { icon: Check, text: "Plan personalizado con IA", available: true },
      { icon: Check, text: "Videos premium + YouTube", available: true },
      { icon: Check, text: "Todos los rangos (E-SSS)", available: true },
      { icon: Check, text: "Explicaciones IA ilimitadas", available: true },
      { icon: Check, text: "Simulacros completos ICFES", available: true },
      { icon: Check, text: "Análisis predictivo", available: true },
      { icon: Check, text: "Sin anuncios", available: true },
      { icon: Check, text: "Soporte prioritario 24/7", available: true }
    ]
  };

  const userJourney = [
    {
      step: 1,
      title: "Registro Gratuito",
      description: "Crea tu cuenta en 30 segundos",
      icon: Unlock,
      color: "from-green-500 to-emerald-500"
    },
    {
      step: 2,
      title: "Diagnóstico Inicial",
      description: "Evalúa tu nivel actual",
      icon: Brain,
      color: "from-blue-500 to-cyan-500"
    },
    {
      step: 3,
      title: "Plan Personalizado",
      description: "Recibe tu ruta de estudio",
      icon: FileText,
      color: "from-purple-500 to-pink-500"
    },
    {
      step: 4,
      title: "Practica Diaria",
      description: "10 preguntas gratis al día",
      icon: Gamepad2,
      color: "from-orange-500 to-red-500"
    },
    {
      step: 5,
      title: "Videos y Recursos",
      description: "Aprende con contenido curado",
      icon: Youtube,
      color: "from-red-500 to-pink-500"
    },
    {
      step: 6,
      title: "Sube de Rango",
      description: "Desbloquea logros y recompensas",
      icon: Trophy,
      color: "from-yellow-500 to-amber-500"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-void-black via-deep-purple to-void-black">
      {/* Professional Header Navigation */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-black/20 backdrop-blur-lg border-b border-purple-500/20">
        <nav className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link href="/" className="flex items-center space-x-2">
              <span className="text-2xl font-bold bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
                🎮 ICFES LEVELING
              </span>
            </Link>

            {/* Center Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <Link href="/" className="text-gray-300 hover:text-white transition-colors font-medium">
                Inicio
              </Link>
              <Link href="/features" className="text-gray-300 hover:text-white transition-colors font-medium">
                Características
              </Link>
              <Link href="/pricing" className="text-gray-300 hover:text-white transition-colors font-medium">
                Precios
              </Link>
              <Link href="/demo" className="text-gray-300 hover:text-white transition-colors font-medium">
                Demo
              </Link>
              <Link href="/about" className="text-gray-300 hover:text-white transition-colors font-medium">
                Nosotros
              </Link>
            </div>

            {/* Auth Buttons */}
            <div className="flex items-center space-x-4">
              <Link 
                href="/login" 
                className="px-6 py-2 text-purple-400 font-semibold border border-purple-400 rounded-lg hover:bg-purple-400/10 transition-all duration-200"
              >
                Iniciar Sesión
              </Link>
              <Link 
                href="/signup" 
                className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200 shadow-lg hover:shadow-purple-500/25"
              >
                Registrarse
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="particles" />
        <div className="absolute inset-0 bg-gradient-radial from-neon-purple/10 via-transparent to-transparent" />
      </div>

      {/* Hero Section - Add padding top for fixed header */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <div className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-neon-purple/20 to-neon-blue/20 rounded-full border border-neon-purple/30 mb-8">
              <Gift className="h-5 w-5 text-neon-gold animate-pulse" />
              <span className="text-white font-semibold">
                ¡Empieza GRATIS hoy! Sin tarjeta de crédito
              </span>
            </div>

            <h1 className="text-6xl md:text-8xl font-bold text-white mb-6">
              Conquista el
              <span className="block text-gradient mt-2">ICFES Saber 11</span>
            </h1>

            <p className="text-2xl text-gray-300 mb-12 max-w-3xl mx-auto">
              Sistema gamificado estilo <span className="italic text-neon-purple">Solo Leveling</span>. 
              Sube de rango E hasta SSS mientras dominas cada materia.
            </p>

            <div className="flex flex-col sm:flex-row gap-6 justify-center mb-12">
              <Link
                href="/signup"
                className="px-10 py-5 bg-gradient-to-r from-neon-purple to-neon-blue rounded-2xl text-white font-bold text-xl hover:shadow-2xl hover:shadow-neon-purple/30 transition-all transform hover:scale-105 glow-button"
              >
                Empezar Gratis <ArrowRight className="inline ml-2" />
              </Link>
              
              <button
                onClick={() => setShowVideo(true)}
                className="px-10 py-5 bg-white/10 backdrop-blur border-2 border-white/20 rounded-2xl text-white font-bold text-xl hover:bg-white/20 transition-all flex items-center justify-center gap-3"
              >
                <PlayCircle className="h-6 w-6" /> Ver Demo (2 min)
              </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
              {[
                { value: "50K+", label: "Estudiantes", icon: Users },
                { value: "95%", label: "Aprobación", icon: Trophy },
                { value: "+45", label: "Puntos Promedio", icon: TrendingUp },
                { value: "4.9★", label: "Calificación", icon: Star }
              ].map((stat, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1 }}
                  className="glass-card p-6 rounded-2xl"
                >
                  <stat.icon className="h-8 w-8 text-neon-purple mx-auto mb-2" />
                  <p className="text-3xl font-bold text-white">{stat.value}</p>
                  <p className="text-gray-400">{stat.label}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* User Journey Section */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-5xl font-bold text-center text-white mb-16">
            Tu Viaje hacia el <span className="text-gradient">Éxito</span>
          </h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {userJourney.map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="relative"
              >
                <div className="glass-card p-8 rounded-2xl hover:scale-105 transition-transform">
                  <div className={`h-16 w-16 rounded-2xl bg-gradient-to-br ${item.color} grid place-items-center mb-4`}>
                    <item.icon className="h-8 w-8 text-white" />
                  </div>
                  
                  <div className="text-sm text-gray-400 mb-2">Paso {item.step}</div>
                  <h3 className="text-2xl font-bold text-white mb-2">{item.title}</h3>
                  <p className="text-gray-300">{item.description}</p>
                  
                  {i < userJourney.length - 1 && (
                    <div className="hidden lg:block absolute top-1/2 -right-4 transform -translate-y-1/2">
                      <ArrowRight className="h-8 w-8 text-neon-purple/50" />
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Comparison */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-5xl font-bold text-center text-white mb-16">
            Elige tu <span className="text-gradient">Poder</span>
          </h2>

          <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {/* Free Plan */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              className={`glass-card rounded-3xl p-8 cursor-pointer transition-all ${
                selectedPlan === "free" ? "border-2 border-green-500 scale-105" : "border border-gray-600"
              }`}
              onClick={() => setSelectedPlan("free")}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-3xl font-bold text-white">Plan Gratuito</h3>
                  <p className="text-gray-400">Perfecto para empezar</p>
                </div>
                <Shield className="h-12 w-12 text-green-500" />
              </div>

              <div className="text-5xl font-bold text-white mb-8">
                $0<span className="text-xl text-gray-400">/mes</span>
              </div>

              <ul className="space-y-4 mb-8">
                {features.free.map((feature, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <feature.icon 
                      className={`h-5 w-5 flex-shrink-0 ${
                        feature.available ? "text-green-400" : "text-gray-600"
                      }`} 
                    />
                    <span className={feature.available ? "text-gray-200" : "text-gray-600 line-through"}>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              <Link
                href="/signup"
                className="block w-full py-4 bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl text-white font-bold text-center hover:shadow-xl transition-all"
              >
                Comenzar Gratis
              </Link>
            </motion.div>

            {/* Premium Plan */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className={`glass-card rounded-3xl p-8 cursor-pointer transition-all relative overflow-hidden ${
                selectedPlan === "premium" ? "border-2 border-neon-purple scale-105" : "border border-gray-600"
              }`}
              onClick={() => setSelectedPlan("premium")}
            >
              <div className="absolute top-0 right-0 px-6 py-2 bg-gradient-to-r from-neon-purple to-neon-blue rounded-bl-2xl">
                <span className="text-white font-bold">MÁS POPULAR</span>
              </div>

              <div className="flex items-center justify-between mb-6 mt-4">
                <div>
                  <h3 className="text-3xl font-bold text-white">Premium Hunter</h3>
                  <p className="text-gray-400">Poder ilimitado</p>
                </div>
                <Crown className="h-12 w-12 text-neon-gold" />
              </div>

              <div className="text-5xl font-bold text-white mb-8">
                $29<span className="text-xl text-gray-400">/mes</span>
                <span className="text-sm text-green-400 block">Ahorra 30% anual</span>
              </div>

              <ul className="space-y-4 mb-8">
                {features.premium.map((feature, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <feature.icon className="h-5 w-5 text-neon-purple flex-shrink-0" />
                    <span className="text-gray-200">{feature.text}</span>
                  </li>
                ))}
              </ul>

              <Link
                href="/signup?plan=premium"
                className="block w-full py-4 bg-gradient-to-r from-neon-purple to-neon-blue rounded-2xl text-white font-bold text-center hover:shadow-xl hover:shadow-neon-purple/30 transition-all glow-button"
              >
                Probar 7 Días Gratis
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4">
          <div className="glass-card rounded-3xl p-12 text-center">
            <h2 className="text-4xl font-bold text-white mb-6">
              Experimenta el Poder del Sistema
            </h2>
            <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
              Prueba una pregunta de ejemplo y descubre cómo nuestro sistema gamificado 
              hace que estudiar sea adictivo.
            </p>

            <div className="grid md:grid-cols-3 gap-8 mb-12">
              <div className="p-6 bg-white/5 rounded-2xl">
                <Brain className="h-12 w-12 text-neon-purple mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">Preguntas Adaptativas</h3>
                <p className="text-gray-400">Se ajustan a tu nivel en tiempo real</p>
              </div>

              <div className="p-6 bg-white/5 rounded-2xl">
                <Zap className="h-12 w-12 text-neon-gold mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">Explicaciones IA</h3>
                <p className="text-gray-400">Entiende cada concepto a profundidad</p>
              </div>

              <div className="p-6 bg-white/5 rounded-2xl">
                <Trophy className="h-12 w-12 text-neon-blue mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">Sistema de Rangos</h3>
                <p className="text-gray-400">Sube de nivel como en un RPG</p>
              </div>
            </div>

            <Link
              href="/demo"
              className="inline-flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-neon-purple to-neon-blue rounded-2xl text-white font-bold text-xl hover:shadow-2xl hover:shadow-neon-purple/30 transition-all glow-button"
            >
              <PlayCircle className="h-6 w-6" />
              Probar Demo Interactiva
            </Link>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-5xl font-bold text-center text-white mb-16">
            Historias de <span className="text-gradient">Éxito</span>
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                name: "María González",
                score: "+52 puntos",
                quote: "Pasé de 280 a 332 puntos. El sistema de rangos me motivó a estudiar todos los días.",
                avatar: "MG",
                rank: "A"
              },
              {
                name: "Carlos Rodríguez",
                score: "+67 puntos",
                quote: "La explicación con IA es increíble. Entendí conceptos que nunca había comprendido.",
                avatar: "CR",
                rank: "S"
              },
              {
                name: "Ana Martínez",
                score: "+48 puntos",
                quote: "Los videos personalizados y el plan adaptativo hicieron toda la diferencia.",
                avatar: "AM",
                rank: "SS"
              }
            ].map((testimonial, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.1 }}
                className="glass-card p-8 rounded-2xl"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="h-16 w-16 rounded-full bg-gradient-to-br from-neon-purple to-neon-blue grid place-items-center text-white font-bold text-xl">
                    {testimonial.avatar}
                  </div>
                  <div>
                    <p className="text-white font-bold">{testimonial.name}</p>
                    <p className="text-green-400 font-bold">{testimonial.score}</p>
                  </div>
                  <div className={`ml-auto px-3 py-1 rounded-full bg-gradient-to-r rank-${testimonial.rank.toLowerCase()}`}>
                    <span className="text-white font-bold">Rango {testimonial.rank}</span>
                  </div>
                </div>
                <p className="text-gray-300 italic">"{testimonial.quote}"</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 relative">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="glass-card rounded-3xl p-12 border-2 border-neon-purple"
          >
            <Flame className="h-16 w-16 text-orange-500 mx-auto mb-6 animate-pulse" />
            
            <h2 className="text-5xl font-bold text-white mb-6">
              Tu Aventura Comienza Ahora
            </h2>
            
            <p className="text-xl text-gray-300 mb-8">
              Únete a miles de estudiantes que ya están conquistando el ICFES.
              <br />Sin riesgos. Sin tarjeta de crédito. Solo resultados.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/signup"
                className="px-10 py-5 bg-gradient-to-r from-neon-purple to-neon-blue rounded-2xl text-white font-bold text-xl hover:shadow-2xl hover:shadow-neon-purple/30 transition-all glow-button"
              >
                Crear Cuenta Gratis
              </Link>
              
              <Link
                href="/pricing"
                className="px-10 py-5 bg-white/10 backdrop-blur border-2 border-white/20 rounded-2xl text-white font-bold text-xl hover:bg-white/20 transition-all"
              >
                Ver Todos los Planes
              </Link>
            </div>

            <p className="text-gray-400 mt-8">
              🔥 <span className="text-orange-400">Oferta limitada:</span> Premium con 50% de descuento el primer mes
            </p>
          </motion.div>
        </div>
      </section>

      {/* Video Modal */}
      <AnimatePresence>
        {showVideo && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            onClick={() => setShowVideo(false)}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="relative max-w-4xl w-full aspect-video bg-black rounded-2xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setShowVideo(false)}
                className="absolute top-4 right-4 z-10 p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
              >
                <X className="h-6 w-6 text-white" />
              </button>
              
              <iframe
                width="100%"
                height="100%"
                src="https://www.youtube.com/embed/demo-video-id"
                title="ICFES Leveling Demo"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}