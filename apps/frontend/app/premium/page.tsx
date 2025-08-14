'use client';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Crown, Zap, Users, BarChart3, CheckCircle, XCircle, Star, Calendar, Clock } from 'lucide-react';

interface PremiumStatus {
  is_premium: boolean;
  premium_expires_at?: string;
  premium_plan?: string;
  ai_requests_remaining: number;
  simulacros_remaining: number;
}

interface Mentor {
  id: string;
  name: string;
  subject: string;
  bio?: string;
  avatar_url?: string;
  rating: number;
  hourly_rate: number;
}

interface PredictiveAnalytics {
  predicted_score: number;
  confidence: number;
  improvement_potential: number;
  recommended_areas: Record<string, boolean>;
}

export default function PremiumPage() {
  const [premiumStatus, setPremiumStatus] = useState<PremiumStatus | null>(null);
  const [mentors, setMentors] = useState<Mentor[]>([]);
  const [analytics, setAnalytics] = useState<PredictiveAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<'monthly' | 'yearly'>('monthly');

  useEffect(() => {
    fetchPremiumData();
  }, []);

  const fetchPremiumData = async () => {
    try {
      // Fetch premium status
      const statusResponse = await fetch('/api/v1/premium/status/user-123');
      const status = await statusResponse.json();
      setPremiumStatus(status);

      // Fetch mentors
      const mentorsResponse = await fetch('/api/v1/premium/mentors');
      const mentorsData = await mentorsResponse.json();
      setMentors(mentorsData);

      // Fetch predictive analytics if premium
      if (status.is_premium) {
        const analyticsResponse = await fetch('/api/v1/premium/analytics/predictive?user_id=user-123');
        const analyticsData = await analyticsResponse.json();
        setAnalytics(analyticsData);
      }
    } catch (error) {
      console.error('Error fetching premium data:', error);
    } finally {
      setLoading(false);
    }
  };

  const upgradeToPremium = async () => {
    try {
      const response = await fetch('/api/v1/premium/upgrade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'user-123',
          plan: selectedPlan,
          duration_days: selectedPlan === 'monthly' ? 30 : 365
        })
      });
      
      if (response.ok) {
        await fetchPremiumData(); // Refresh data
      }
    } catch (error) {
      console.error('Error upgrading to premium:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold text-white mb-4">
            <Crown className="inline-block mr-3 text-yellow-400" />
            Sistema Premium
          </h1>
          <p className="text-xl text-gray-300">
            Acelera tu preparación con beneficios exclusivos
          </p>
        </motion.div>

        {/* Premium Status */}
        {premiumStatus && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-8"
          >
            <h2 className="text-2xl font-bold text-white mb-4">Estado Premium</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center space-x-3">
                {premiumStatus.is_premium ? (
                  <CheckCircle className="text-green-400" />
                ) : (
                  <XCircle className="text-red-400" />
                )}
                <span className="text-white">
                  {premiumStatus.is_premium ? 'Premium Activo' : 'Plan Gratuito'}
                </span>
              </div>
              <div className="text-white">
                <span className="text-gray-300">Requests IA restantes: </span>
                <span className="font-bold">{premiumStatus.ai_requests_remaining}</span>
              </div>
              <div className="text-white">
                <span className="text-gray-300">Simulacros restantes: </span>
                <span className="font-bold">{premiumStatus.simulacros_remaining}</span>
              </div>
              {premiumStatus.premium_expires_at && (
                <div className="text-white">
                  <span className="text-gray-300">Expira: </span>
                  <span className="font-bold">
                    {new Date(premiumStatus.premium_expires_at).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Upgrade Plans */}
        {!premiumStatus?.is_premium && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8"
          >
            {/* Monthly Plan */}
            <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg p-6 text-white">
              <h3 className="text-2xl font-bold mb-4">Plan Mensual</h3>
              <div className="text-3xl font-bold mb-4">$29.99/mes</div>
              <ul className="space-y-2 mb-6">
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  Tutores IA ilimitados
                </li>
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  10 simulacros completos
                </li>
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  Análisis predictivo avanzado
                </li>
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  Acceso a mentores reales
                </li>
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  Sin publicidad
                </li>
              </ul>
              <button
                onClick={() => {
                  setSelectedPlan('monthly');
                  upgradeToPremium();
                }}
                className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold py-3 px-6 rounded-lg transition-colors"
              >
                Actualizar a Premium
              </button>
            </div>

            {/* Yearly Plan */}
            <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg p-6 text-white relative">
              <div className="absolute -top-4 -right-4 bg-yellow-500 text-black px-3 py-1 rounded-full text-sm font-bold">
                MEJOR VALOR
              </div>
              <h3 className="text-2xl font-bold mb-4">Plan Anual</h3>
              <div className="text-3xl font-bold mb-4">$299.99/año</div>
              <div className="text-sm text-gray-300 mb-4">Ahorra $59.89</div>
              <ul className="space-y-2 mb-6">
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  Tutores IA ilimitados
                </li>
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  20 simulacros completos
                </li>
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  Análisis predictivo avanzado
                </li>
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  Acceso prioritario a mentores
                </li>
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  Sin publicidad
                </li>
                <li className="flex items-center">
                  <CheckCircle className="mr-2 text-green-400" />
                  Certificados de dominio
                </li>
              </ul>
              <button
                onClick={() => {
                  setSelectedPlan('yearly');
                  upgradeToPremium();
                }}
                className="w-full bg-yellow-500 hover:bg-yellow-600 text-black font-bold py-3 px-6 rounded-lg transition-colors"
              >
                Actualizar a Premium
              </button>
            </div>
          </motion.div>
        )}

        {/* Mentors Section */}
        {premiumStatus?.is_premium && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <h2 className="text-2xl font-bold text-white mb-6">
              <Users className="inline-block mr-3" />
              Mentores Reales Disponibles
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {mentors.map((mentor) => (
                <div key={mentor.id} className="bg-white/10 backdrop-blur-sm rounded-lg p-4">
                  <div className="flex items-center mb-3">
                    {mentor.avatar_url ? (
                      <img
                        src={mentor.avatar_url}
                        alt={mentor.name}
                        className="w-12 h-12 rounded-full mr-3"
                      />
                    ) : (
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full mr-3 flex items-center justify-center">
                        <Users className="text-white" />
                      </div>
                    )}
                    <div>
                      <h3 className="text-white font-bold">{mentor.name}</h3>
                      <p className="text-gray-300 text-sm">{mentor.subject}</p>
                    </div>
                  </div>
                  <div className="flex items-center mb-2">
                    <Star className="text-yellow-400 mr-1" />
                    <span className="text-white">{mentor.rating}/5.0</span>
                  </div>
                  <p className="text-gray-300 text-sm mb-3">{mentor.bio}</p>
                  <div className="flex justify-between items-center">
                    <span className="text-white font-bold">
                      ${mentor.hourly_rate}/hora
                    </span>
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                      Agendar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Predictive Analytics */}
        {analytics && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white/10 backdrop-blur-sm rounded-lg p-6"
          >
            <h2 className="text-2xl font-bold text-white mb-6">
              <BarChart3 className="inline-block mr-3" />
              Análisis Predictivo Avanzado
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-400 mb-2">
                  {analytics.predicted_score}
                </div>
                <div className="text-white">Puntaje ICFES Proyectado</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-400 mb-2">
                  {Math.round(analytics.confidence * 100)}%
                </div>
                <div className="text-white">Nivel de Confianza</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-400 mb-2">
                  +{analytics.improvement_potential}
                </div>
                <div className="text-white">Potencial de Mejora</div>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="text-white font-bold mb-3">Áreas de Enfoque Recomendadas:</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {Object.entries(analytics.recommended_areas).map(([area, needsFocus]) => (
                  <div key={area} className="flex items-center space-x-2">
                    {needsFocus ? (
                      <CheckCircle className="text-red-400" />
                    ) : (
                      <CheckCircle className="text-green-400" />
                    )}
                    <span className="text-white capitalize">{area}</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
} 