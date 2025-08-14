import { loadStripe, Stripe } from '@stripe/stripe-js';
import { axiosInstance } from '../lib/axios';

// Initialize Stripe
let stripePromise: Promise<Stripe | null>;

export const getStripe = () => {
  if (!stripePromise) {
    stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '');
  }
  return stripePromise;
};

export interface PremiumPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  interval: 'month' | 'year';
  features: string[];
  stripePriceId?: string;
}

export interface PaymentIntent {
  clientSecret: string;
  amount: number;
  currency: string;
}

export const PREMIUM_PLANS: PremiumPlan[] = [
  {
    id: 'monthly',
    name: 'Premium Mensual',
    description: 'Acceso completo por 1 mes',
    price: 19900, // $19,900 COP
    currency: 'COP',
    interval: 'month',
    features: [
      'Acceso ilimitado a todas las preguntas',
      'Simulacros ICFES ilimitados',
      'Análisis detallado con IA',
      'Sin publicidad',
      'Soporte prioritario',
      'Raids exclusivos',
      'Doble experiencia'
    ],
    stripePriceId: process.env.NEXT_PUBLIC_STRIPE_MONTHLY_PRICE_ID
  },
  {
    id: 'yearly',
    name: 'Premium Anual',
    description: 'Acceso completo por 1 año',
    price: 199900, // $199,900 COP (ahorro de 2 meses)
    currency: 'COP',
    interval: 'year',
    features: [
      'Todo lo del plan mensual',
      'Ahorro de 2 meses',
      'Badge exclusivo "Fundador"',
      'Acceso beta a nuevas funciones',
      'Mentoría IA personalizada',
      'Análisis predictivo ICFES',
      'Certificado de completación'
    ],
    stripePriceId: process.env.NEXT_PUBLIC_STRIPE_YEARLY_PRICE_ID
  }
];

class PaymentService {
  async createCheckoutSession(planId: string, userId: string) {
    try {
      const plan = PREMIUM_PLANS.find(p => p.id === planId);
      if (!plan) throw new Error('Plan no encontrado');
      
      const response = await axiosInstance.post('/premium/create-checkout-session', {
        planId,
        priceId: plan.stripePriceId,
        userId
      });
      
      return response.data;
    } catch (error) {
      console.error('Error creating checkout session:', error);
      throw error;
    }
  }
  
  async createPaymentIntent(amount: number, currency: string = 'COP'): Promise<PaymentIntent> {
    try {
      const response = await axiosInstance.post('/premium/create-payment-intent', {
        amount,
        currency
      });
      
      return response.data;
    } catch (error) {
      console.error('Error creating payment intent:', error);
      throw error;
    }
  }
  
  async confirmPayment(paymentIntentId: string) {
    try {
      const response = await axiosInstance.post('/premium/confirm-payment', {
        paymentIntentId
      });
      
      return response.data;
    } catch (error) {
      console.error('Error confirming payment:', error);
      throw error;
    }
  }
  
  async getUserSubscription(userId: string) {
    try {
      const response = await axiosInstance.get(`/premium/subscription/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching subscription:', error);
      throw error;
    }
  }
  
  async cancelSubscription(subscriptionId: string) {
    try {
      const response = await axiosInstance.post('/premium/cancel-subscription', {
        subscriptionId
      });
      
      return response.data;
    } catch (error) {
      console.error('Error canceling subscription:', error);
      throw error;
    }
  }
  
  async getPaymentHistory(userId: string) {
    try {
      const response = await axiosInstance.get(`/premium/payment-history/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching payment history:', error);
      throw error;
    }
  }
}

export const paymentService = new PaymentService();