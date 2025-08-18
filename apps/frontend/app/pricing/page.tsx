'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function PricingPage() {
  const router = useRouter();
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  const plans = [
    {
      name: 'Gratis',
      price: { monthly: 0, yearly: 0 },
      description: 'Perfecto para comenzar tu aventura',
      features: [
        '✅ 1 prueba diagnóstica al mes',
        '✅ Acceso a 100 preguntas',
        '✅ Plan de estudio básico',
        '✅ 1 materia disponible',
        '✅ Rango máximo: C',
        '❌ Sin batallas de jefes',
        '❌ Sin personalización IA',
        '❌ Sin análisis detallado'
      ],
      cta: 'Empezar Gratis',
      highlighted: false,
      color: 'gray'
    },
    {
      name: 'Hunter Pro',
      price: { monthly: 29900, yearly: 299000 },
      description: 'El más popular entre los estudiantes',
      features: [
        '✅ Pruebas diagnósticas ilimitadas',
        '✅ +2000 preguntas ICFES',
        '✅ Planes personalizados con IA',
        '✅ Todas las materias',
        '✅ Rango máximo: S',
        '✅ Batallas de jefes épicas',
        '✅ Videos explicativos',
        '✅ Análisis predictivo',
        '✅ Soporte prioritario'
      ],
      cta: 'Elegir Hunter Pro',
      highlighted: true,
      color: 'purple'
    },
    {
      name: 'Guild Master',
      price: { monthly: 49900, yearly: 499000 },
      description: 'Para grupos y colegios',
      features: [
        '✅ Todo de Hunter Pro',
        '✅ Hasta 30 estudiantes',
        '✅ Panel de administración',
        '✅ Reportes detallados',
        '✅ Rango máximo: SSS',
        '✅ Raids multijugador',
        '✅ Competencias privadas',
        '✅ Tutor IA dedicado',
        '✅ Soporte 24/7',
        '✅ Certificados personalizados'
      ],
      cta: 'Contactar Ventas',
      highlighted: false,
      color: 'gold'
    }
  ];

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(price);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <header className="bg-black/20 backdrop-blur-lg border-b border-purple-500/20">
        <div className="container mx-auto px-4 py-4">
          <nav className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <span className="text-2xl font-bold bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
                🎮 ICFES LEVELING
              </span>
            </Link>
            <div className="flex items-center space-x-6">
              <Link href="/landing" className="text-gray-300 hover:text-white transition-colors">
                Inicio
              </Link>
              <Link href="/features" className="text-gray-300 hover:text-white transition-colors">
                Características
              </Link>
              <Link href="/pricing" className="text-white font-semibold">
                Precios
              </Link>
              <Link href="/login" className="px-4 py-2 text-purple-400 border border-purple-400 rounded-lg hover:bg-purple-400/10 transition-all">
                Iniciar Sesión
              </Link>
              <Link href="/signup" className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all">
                Registrarse
              </Link>
            </div>
          </nav>
        </div>
      </header>

      {/* Pricing Content */}
      <div className="container mx-auto px-4 py-16">
        {/* Title Section */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
            Elige tu Camino de Hunter
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            Desbloquea todo tu potencial con el plan perfecto para ti
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center bg-black/30 rounded-lg p-1 border border-purple-500/30">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-6 py-2 rounded-md font-semibold transition-all ${
                billingCycle === 'monthly'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Mensual
            </button>
            <button
              onClick={() => setBillingCycle('yearly')}
              className={`px-6 py-2 rounded-md font-semibold transition-all ${
                billingCycle === 'yearly'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Anual
              <span className="ml-2 text-xs bg-green-500 text-white px-2 py-1 rounded">
                -17%
              </span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative bg-black/40 backdrop-blur-lg rounded-xl p-8 border ${
                plan.highlighted
                  ? 'border-purple-400 scale-105 shadow-2xl shadow-purple-500/20'
                  : 'border-gray-700'
              } hover:border-purple-400/50 transition-all duration-300`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-purple-600 to-blue-600 text-white text-sm font-bold px-4 py-1 rounded-full">
                    MÁS POPULAR
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className={`text-2xl font-bold mb-2 text-${plan.color}-400`}>
                  {plan.name}
                </h3>
                <p className="text-gray-400 text-sm mb-4">{plan.description}</p>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-white">
                    {formatPrice(plan.price[billingCycle])}
                  </span>
                  {plan.price[billingCycle] > 0 && (
                    <span className="text-gray-400 ml-2">
                      /{billingCycle === 'monthly' ? 'mes' : 'año'}
                    </span>
                  )}
                </div>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="text-sm text-gray-300">
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => {
                  if (plan.name === 'Gratis') {
                    router.push('/signup');
                  } else if (plan.name === 'Guild Master') {
                    router.push('/contact');
                  } else {
                    router.push('/signup?plan=pro');
                  }
                }}
                className={`w-full py-3 font-bold rounded-lg transition-all duration-200 ${
                  plan.highlighted
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-600'
                } transform hover:scale-105`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>

        {/* FAQ Section */}
        <div className="mt-20 max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 text-white">
            Preguntas Frecuentes
          </h2>
          <div className="space-y-6">
            <div className="bg-black/30 backdrop-blur-lg rounded-lg p-6 border border-purple-500/20">
              <h3 className="text-xl font-semibold text-purple-400 mb-2">
                ¿Puedo cambiar de plan en cualquier momento?
              </h3>
              <p className="text-gray-300">
                Sí, puedes actualizar o cambiar tu plan en cualquier momento desde tu panel de cuenta.
              </p>
            </div>
            <div className="bg-black/30 backdrop-blur-lg rounded-lg p-6 border border-purple-500/20">
              <h3 className="text-xl font-semibold text-purple-400 mb-2">
                ¿Hay periodo de prueba?
              </h3>
              <p className="text-gray-300">
                Ofrecemos 7 días de prueba gratis en el plan Hunter Pro. No se requiere tarjeta de crédito.
              </p>
            </div>
            <div className="bg-black/30 backdrop-blur-lg rounded-lg p-6 border border-purple-500/20">
              <h3 className="text-xl font-semibold text-purple-400 mb-2">
                ¿Qué métodos de pago aceptan?
              </h3>
              <p className="text-gray-300">
                Aceptamos tarjetas de crédito/débito, PSE, Nequi, Daviplata y transferencias bancarias.
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-20 text-center">
          <div className="bg-gradient-to-r from-purple-600/20 to-blue-600/20 rounded-xl p-12 border border-purple-500/30">
            <h2 className="text-3xl font-bold mb-4 text-white">
              ¿Listo para subir de nivel?
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              Únete a miles de estudiantes que ya están mejorando sus resultados
            </p>
            <div className="flex justify-center space-x-4">
              <Link
                href="/signup"
                className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold rounded-lg hover:from-purple-700 hover:to-blue-700 transform hover:scale-105 transition-all"
              >
                Comenzar Ahora
              </Link>
              <Link
                href="/demo"
                className="px-8 py-3 bg-black/40 text-white font-bold rounded-lg border border-purple-400 hover:bg-purple-400/10 transform hover:scale-105 transition-all"
              >
                Ver Demo
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}