'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useRouter } from 'next/navigation'
import SoundManager from '../components/SoundManager'
import HeroAnimations from '../components/HeroAnimations'

interface PersonalityQuestion {
  id: string
  question_text: string
  question_type: string
  options: Record<string, string>
  order_index: number
}

interface HeroClass {
  id: string
  name: string
  description: string
  avatar_url: string
  special_ability: string
  element: string
  color_theme: string
  class_type: string
}

interface CutsceneData {
  title: string
  subtitle: string
  animation: string
  particles: string[]
  sound_effect: string
}

interface PersonalityTestResponse {
  hero_class: HeroClass
  personality_answers: Record<string, string>
  cutscene_data: CutsceneData
  stats_boost: Record<string, number>
}

// Hook para manejar autenticación
function useAuth() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Verificar si hay un token en localStorage
    const token = localStorage.getItem('access_token') || localStorage.getItem('token')
    if (token) {
      // Verificar token con el backend
      fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(res => res.json())
      .then(data => {
        if (data.id) {
          setUser(data)
        } else {
          localStorage.removeItem('access_token')
          localStorage.removeItem('token')
        }
      })
      .catch(() => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('token')
      })
      .finally(() => {
        setLoading(false)
      })
    } else {
      setLoading(false)
    }
  }, [])

  return { user, loading }
}

export default function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [questions, setQuestions] = useState<PersonalityQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [testResult, setTestResult] = useState<PersonalityTestResponse | null>(null)
  const [showCutscene, setShowCutscene] = useState(false)
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()

  useEffect(() => {
    if (!authLoading && !user) {
      // Redirigir al login si no hay usuario
      router.push('/login')
      return
    }
    
    if (user) {
      loadQuestions()
    }
  }, [user, authLoading, router])

  const loadQuestions = async () => {
    try {
      const response = await fetch('/api/v1/personality/questions')
      if (response.ok) {
        const data = await response.json()
        setQuestions(data)
      }
    } catch (error) {
      console.error('Error loading questions:', error)
    }
  }

  const handleAnswer = (questionType: string, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionType]: answer
    }))
  }

  const handleNext = () => {
    if (currentStep < questions.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      submitTest()
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1)
    }
  }

  const submitTest = async () => {
    if (!user) return
    
    setIsLoading(true)
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token')
      const response = await fetch('/api/v1/personality/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          user_id: user.id,
          answers: answers
        })
      })

      if (response.ok) {
        const result = await response.json()
        setTestResult(result)
        setShowCutscene(true)
      } else {
        console.error('Error submitting test:', response.statusText)
      }
    } catch (error) {
      console.error('Error submitting test:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCompleteOnboarding = () => {
    // Guardar resultado en localStorage
    if (testResult) {
      localStorage.setItem('heroClass', JSON.stringify(testResult.hero_class))
      localStorage.setItem('onboardingCompleted', 'true')
    }
    router.push('/')
  }

  // Mostrar loading mientras se verifica autenticación
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <p className="text-mist-purple-300">Verificando autenticación...</p>
        </div>
      </div>
    )
  }

  // Redirigir si no hay usuario
  if (!user) {
    return null
  }

  if (showCutscene && testResult) {
    return <HeroCutscene data={testResult} onComplete={handleCompleteOnboarding} />
  }

  if (questions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <p className="text-mist-purple-300">Cargando test épico...</p>
        </div>
      </div>
    )
  }

  const currentQuestion = questions[currentStep]

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-tertiary p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="font-display text-5xl font-bold text-gold-400 mb-4">
            🌟 Test de Personalidad Épica
          </h1>
          <p className="text-xl text-mist-purple-300">
            Descubre tu arquetipo de héroe y desbloquea poderes únicos
          </p>
          {user && (
            <p className="text-mist-purple-400 mt-2">
              Bienvenido, {user.display_name || user.username}!
            </p>
          )}
        </motion.div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-mist-purple-300 font-ui">
              Pregunta {currentStep + 1} de {questions.length}
            </span>
            <span className="text-gold-400 font-ui font-semibold">
              {Math.round(((currentStep + 1) / questions.length) * 100)}%
            </span>
          </div>
          <div className="w-full bg-bg-tertiary rounded-full h-3">
            <motion.div
              className="bg-gradient-to-r from-gold-400 to-gold-600 h-3 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${((currentStep + 1) / questions.length) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Question */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
            className="card-game mb-8"
          >
            <div className="text-center mb-8">
              <h2 className="font-ui text-2xl font-bold text-white mb-4">
                {currentQuestion.question_text}
              </h2>
            </div>

            <div className="space-y-4">
              {Object.entries(currentQuestion.options).map(([key, value]) => (
                <motion.button
                  key={key}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleAnswer(currentQuestion.question_type, key)}
                  className={`w-full p-4 text-left rounded-lg border-2 transition-all duration-200 ${
                    answers[currentQuestion.question_type] === key
                      ? 'border-gold-400 bg-gold-400/10 text-gold-400'
                      : 'border-mist-purple-500/30 bg-bg-tertiary text-mist-purple-300 hover:border-mist-purple-400'
                  }`}
                >
                  <div className="flex items-center">
                    <div className={`w-6 h-6 rounded-full border-2 mr-4 flex items-center justify-center ${
                      answers[currentQuestion.question_type] === key
                        ? 'border-gold-400 bg-gold-400'
                        : 'border-mist-purple-500'
                    }`}>
                      {answers[currentQuestion.question_type] === key && (
                        <div className="w-2 h-2 bg-white rounded-full"></div>
                      )}
                    </div>
                    <span className="font-ui">{value}</span>
                  </div>
                </motion.button>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex justify-between">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className={`btn-secondary ${currentStep === 0 ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            ← Anterior
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleNext}
            disabled={!answers[currentQuestion.question_type] || isLoading}
            className={`btn-primary ${(!answers[currentQuestion.question_type] || isLoading) ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isLoading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Analizando...
              </div>
            ) : currentStep === questions.length - 1 ? (
              '🎯 Descubrir Mi Clase'
            ) : (
              'Siguiente →'
            )}
          </motion.button>
        </div>
      </div>
    </div>
  )
}

function HeroCutscene({ data, onComplete }: { data: PersonalityTestResponse, onComplete: () => void }) {
  const [currentPhase, setCurrentPhase] = useState(0)
  const [isSoundPlaying, setIsSoundPlaying] = useState(false)
  const { hero_class, cutscene_data } = data

  useEffect(() => {
    const timer = setTimeout(() => {
      if (currentPhase < 3) {
        setCurrentPhase(prev => prev + 1)
      }
    }, 2000)

    return () => clearTimeout(timer)
  }, [currentPhase])

  // Reproducir sonido cuando se revela el héroe
  useEffect(() => {
    if (currentPhase === 1 && cutscene_data.sound_effect) {
      setIsSoundPlaying(true)
    }
  }, [currentPhase, cutscene_data.sound_effect])

  const phases = [
    {
      title: "🌟 Descubriendo tu destino...",
      subtitle: "Las estrellas se alinean para revelar tu verdadera naturaleza",
      animation: "fadeIn"
    },
    {
      title: cutscene_data.title,
      subtitle: cutscene_data.subtitle,
      animation: "heroReveal"
    },
    {
      title: `¡${hero_class.name}!`,
      subtitle: hero_class.description,
      animation: "finalReveal"
    }
  ]

  const currentPhaseData = phases[currentPhase] || phases[phases.length - 1]

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-tertiary flex items-center justify-center p-4">
      {/* Sound Manager */}
      <SoundManager 
        soundEffect={cutscene_data.sound_effect}
        isPlaying={isSoundPlaying}
        onSoundEnd={() => setIsSoundPlaying(false)}
      />
      
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1 }}
        className="text-center max-w-4xl relative"
      >
        {/* Animaciones específicas por clase */}
        <HeroAnimations
          classType={hero_class.class_type}
          element={hero_class.element}
          isActive={currentPhase === 1}
          onAnimationComplete={() => {
            // Continuar con la siguiente fase después de las animaciones
            setTimeout(() => setCurrentPhase(prev => prev + 1), 1000)
          }}
        />
        {/* Hero Avatar */}
        <motion.div
          initial={{ scale: 0, rotateY: 180 }}
          animate={{ 
            scale: currentPhase >= 1 ? 1 : 0,
            rotateY: currentPhase >= 1 ? 0 : 180
          }}
          transition={{ duration: 1, delay: 0.5 }}
          className="mb-8"
        >
          <div 
            className="w-48 h-48 mx-auto rounded-full border-4"
            style={{ borderColor: hero_class.color_theme }}
          >
            <div className="w-full h-full rounded-full bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
              <span className="text-6xl">
                {hero_class.class_type === 'mage' && '🧙‍♂️'}
                {hero_class.class_type === 'warrior' && '⚔️'}
                {hero_class.class_type === 'archer' && '🏹'}
                {hero_class.class_type === 'priest' && '🙏'}
                {hero_class.class_type === 'assassin' && '🗡️'}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="font-display text-6xl font-bold mb-4"
          style={{ color: hero_class.color_theme }}
        >
          {currentPhaseData.title}
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="text-xl text-mist-purple-300 mb-8"
        >
          {currentPhaseData.subtitle}
        </motion.p>

        {/* Special Ability */}
        {currentPhase >= 2 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="mb-8"
          >
            <div className="card-game inline-block">
              <h3 className="font-ui font-semibold text-lg mb-2 text-gold-400">
                🎯 Habilidad Especial
              </h3>
              <p className="text-mist-purple-300">
                {hero_class.special_ability}
              </p>
            </div>
          </motion.div>
        )}

        {/* Complete Button */}
        {currentPhase >= 2 && (
          <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 1 }}
            onClick={onComplete}
            className="btn-primary text-lg px-8 py-4"
          >
            🚀 ¡Comenzar Aventura!
          </motion.button>
        )}
      </motion.div>
    </div>
  )
} 