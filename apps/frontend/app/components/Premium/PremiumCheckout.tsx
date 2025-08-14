'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Crown, 
  Check, 
  X,
  Zap,
  Trophy,
  Brain,
  Users,
  TrendingUp,
  Shield,
  ChevronRight,
  CreditCard,
  Lock,
  Sparkles
} from 'lucide-react';
import { useAudio } from '../PortalLogin/AudioEngine';
import { paymentService, PREMIUM_PLANS, PremiumPlan } from '@/services/payment.service';
import { useAuthStore } from '@/stores/useAuthStore';
import { trackGameEvent } from '@/lib/analytics';
import { getStripe } from '@/services/payment.service';

interface PremiumCheckoutProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function PremiumCheckout({ isOpen, onClose, onSuccess }: PremiumCheckoutProps) {
  const { playSound } = useAudio();
  const { user } = useAuthStore();
  const [selectedPlan, setSelectedPlan] = useState<PremiumPlan>(PREMIUM_PLANS[0]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  
  const handlePlanSelect = (plan: PremiumPlan) => {
    playSound('typing_click');
    setSelectedPlan(plan);
    trackGameEvent('premium_plan_selected', { plan: plan.id });
  };
  
  const handleCheckout = async () => {
    if (!user) {
      setError('Debes iniciar sesión para comprar Premium');
      return;
    }
    
    setIsProcessing(true);
    setError('');
    playSound('quest_complete');
    
    try {
      trackGameEvent('premium_checkout_started', { 
        plan: selectedPlan.id,
        price: selectedPlan.price 
      });
      
      // Create checkout session
      const { sessionId } = await paymentService.createCheckoutSession(
        selectedPlan.id,
        user.id
      );
      
      // Redirect to Stripe Checkout
      const stripe = await getStripe();
      if (stripe) {
        const { error } = await stripe.redirectToCheckout({
          sessionId
        });
        
        if (error) {
          throw error;
        }
      }
    } catch (err: any) {
      console.error('Checkout error:', err);
      setError(err.message || 'Error al procesar el pago');
      playSound('notification_epic');
      trackGameEvent('premium_checkout_error', { 
        error: err.message,
        plan: selectedPlan.id 
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(price);
  };
  
  const getSavings = () => {
    const monthlyTotal = PREMIUM_PLANS[0].price * 12;
    const yearlyPrice = PREMIUM_PLANS[1].price;
    const savings = monthlyTotal - yearlyPrice;
    const savingsPercent = Math.round((savings / monthlyTotal) * 100);
    
    return { savings, savingsPercent };
  };
  
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            className="fixed inset-0 bg-black/80 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          
          <motion.div
            className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 
              bg-gray-900 rounded-lg max-w-4xl w-full mx-4 z-50 max-h-[90vh] overflow-y-auto"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-900 to-indigo-900 p-6 rounded-t-lg relative overflow-hidden">
              <div className="absolute inset-0 bg-stars-bg opacity-20"></div>
              
              <button
                onClick={onClose}
                className="absolute top-4 right-4 text-white/70 hover:text-white transition-colors z-10"
              >
                <X className="w-6 h-6" />
              </button>
              
              <div className="relative z-10">
                <div className="flex items-center gap-3 mb-4">
                  <Crown className="w-10 h-10 text-yellow-400" />
                  <h2 className="text-3xl font-bold text-white font-cinzel">
                    Hazte Premium
                  </h2>
                </div>
                
                <p className="text-purple-200 text-lg">
                  Desbloquea todo el poder de ICFES Leveling
                </p>
              </div>
            </div>
            
            {/* Plans */}
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {PREMIUM_PLANS.map((plan, index) => {
                  const isSelected = selectedPlan.id === plan.id;
                  const isYearly = plan.interval === 'year';
                  const { savingsPercent } = getSavings();
                  
                  return (
                    <motion.div
                      key={plan.id}
                      className={`
                        relative rounded-lg cursor-pointer transition-all
                        ${isSelected 
                          ? 'ring-2 ring-purple-500 bg-purple-900/20' 
                          : 'bg-gray-800/50 hover:bg-gray-800/70'
                        }
                      `}
                      onClick={() => handlePlanSelect(plan)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      {isYearly && (
                        <div className="absolute -top-3 -right-3 bg-gradient-to-r from-yellow-500 
                          to-yellow-600 text-black font-bold px-4 py-1 rounded-full text-sm
                          transform rotate-12">
                          Ahorra {savingsPercent}%
                        </div>
                      )}
                      
                      <div className="p-6">
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h3 className="text-xl font-bold text-white mb-1">
                              {plan.name}
                            </h3>
                            <p className="text-gray-400 text-sm">
                              {plan.description}
                            </p>
                          </div>
                          
                          {isSelected && (
                            <div className="bg-purple-500 rounded-full p-1">
                              <Check className="w-5 h-5 text-white" />
                            </div>
                          )}
                        </div>
                        
                        <div className="mb-6">
                          <div className="text-3xl font-bold text-white mb-1">
                            {formatPrice(plan.price)}
                          </div>
                          <p className="text-sm text-gray-400">
                            por {plan.interval === 'month' ? 'mes' : 'año'}
                          </p>
                        </div>
                        
                        <div className="space-y-3">
                          {plan.features.slice(0, 5).map((feature, idx) => (
                            <div key={idx} className="flex items-start gap-2">
                              <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                              <span className="text-sm text-gray-300">
                                {feature}
                              </span>
                            </div>
                          ))}
                          
                          {plan.features.length > 5 && (
                            <p className="text-sm text-purple-400 mt-2">
                              +{plan.features.length - 5} más beneficios
                            </p>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
              
              {/* Features Grid */}
              <div className="bg-gray-800/30 rounded-lg p-6 mb-8">
                <h3 className="text-lg font-semibold text-white mb-4">
                  ¿Por qué Premium?
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-start gap-3">
                    <Brain className="w-6 h-6 text-purple-400 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-white mb-1">
                        IA Avanzada
                      </h4>
                      <p className="text-sm text-gray-400">
                        Tips personalizados y análisis predictivo
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <Trophy className="w-6 h-6 text-yellow-400 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-white mb-1">
                        Sin Límites
                      </h4>
                      <p className="text-sm text-gray-400">
                        Practica sin restricciones diarias
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <Users className="w-6 h-6 text-green-400 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-white mb-1">
                        Comunidad VIP
                      </h4>
                      <p className="text-sm text-gray-400">
                        Acceso a raids y eventos exclusivos
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Error Message */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-red-900/30 border border-red-500/50 rounded-lg p-4 mb-6"
                >
                  <p className="text-red-400">{error}</p>
                </motion.div>
              )}
              
              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-4">
                <button
                  onClick={handleCheckout}
                  disabled={isProcessing}
                  className={`
                    flex-1 py-4 px-6 rounded-lg font-bold text-lg
                    transition-all transform hover:scale-105
                    flex items-center justify-center gap-3
                    ${isProcessing
                      ? 'bg-gray-700 cursor-not-allowed'
                      : 'bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800'
                    }
                    text-white
                  `}
                >
                  {isProcessing ? (
                    <>
                      <motion.div
                        className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      />
                      Procesando...
                    </>
                  ) : (
                    <>
                      <CreditCard className="w-5 h-5" />
                      Continuar con {selectedPlan.name}
                      <ChevronRight className="w-5 h-5" />
                    </>
                  )}
                </button>
                
                <button
                  onClick={onClose}
                  disabled={isProcessing}
                  className="px-6 py-4 bg-gray-700 hover:bg-gray-600 text-white 
                    font-semibold rounded-lg transition-all"
                >
                  Cancelar
                </button>
              </div>
              
              {/* Security Notice */}
              <div className="flex items-center justify-center gap-2 mt-6 text-sm text-gray-500">
                <Lock className="w-4 h-4" />
                <span>Pago seguro procesado por Stripe</span>
                <Shield className="w-4 h-4" />
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}