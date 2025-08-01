'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import React from 'react'

export default function HomePage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)

  // Mock login function
  const handleLogin = (username: string, password: string) => {
    // Simular login exitoso
    setCurrentUser({
      id: 'aa0e8400-e29b-41d4-a716-446655440001',
      username: username,
      display_name: 'Shadow Hunter',
      level: 25,
      rank: 'B',
      hp: 150,
      mp: 75,
      experience: 12500,
      orbs: 5000,
      crystals: 100
    })
    setIsLoggedIn(true)
  }

  if (!isLoggedIn) {
    return <LoginScreen onLogin={handleLogin} />
  }

  return <Dashboard user={currentUser} onLogout={() => setIsLoggedIn(false)} />
}

function LoginScreen({ onLogin }: { onLogin: (username: string, password: string) => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onLogin(username, password)
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="card-game w-full max-w-md"
      >
        <div className="text-center mb-8">
          <h1 className="font-display text-4xl font-bold text-gold-400 mb-2">
            ICFES LEVELING
          </h1>
          <p className="text-mist-purple-300 font-ui">
            Combate enemigos académicos mientras preparas tu ICFES
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-ui text-mist-purple-300 mb-2">
              Usuario
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 bg-bg-tertiary border border-mist-purple-500/30 rounded-lg
                       text-white placeholder-mist-purple-400 focus:outline-none focus:ring-2 
                       focus:ring-mist-purple-500 focus:border-transparent"
              placeholder="shadow_hunter"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-ui text-mist-purple-300 mb-2">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-bg-tertiary border border-mist-purple-500/30 rounded-lg
                       text-white placeholder-mist-purple-400 focus:outline-none focus:ring-2 
                       focus:ring-mist-purple-500 focus:border-transparent"
              placeholder="password123"
              required
            />
          </div>

          <button
            type="submit"
            className="btn-primary w-full"
          >
            Iniciar Sesión
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-mist-purple-400 mb-2">Usuarios de prueba:</p>
          <div className="text-xs text-mist-purple-500 space-y-1">
            <p>shadow_hunter / password123 (Level 25, Rank B)</p>
            <p>math_master / password123 (Level 18, Rank C)</p>
            <p>newbie_student / password123 (Level 1, Rank E)</p>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

function Dashboard({ user, onLogout }: { user: any, onLogout: () => void }) {
  return (
    <div className="min-h-screen p-4">
      {/* Header */}
      <header className="flex justify-between items-center mb-8">
        <div>
          <h1 className="font-display text-3xl font-bold text-gold-400">
            {user.display_name}
          </h1>
          <p className="text-mist-purple-300 font-ui">
            Nivel {user.level} • Rank {user.rank}
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-gold-400 font-ui font-semibold">{user.orbs} Orbes</p>
            <p className="text-mist-purple-400 font-ui font-semibold">{user.crystals} Cristales</p>
          </div>
          <button
            onClick={onLogout}
            className="btn-secondary"
          >
            Salir
          </button>
        </div>
      </header>

      {/* Stats Bars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div className="card-game">
          <div className="flex justify-between items-center mb-2">
            <span className="font-ui font-semibold text-success-400">HP</span>
            <span className="text-sm">{user.hp}/150</span>
          </div>
          <div className="liquid-bar h-3">
            <div 
              className="liquid-bar-fill hp h-full rounded-full"
              style={{ width: `${(user.hp / 150) * 100}%` }}
            ></div>
          </div>
        </div>

        <div className="card-game">
          <div className="flex justify-between items-center mb-2">
            <span className="font-ui font-semibold text-mystic-blue-400">MP</span>
            <span className="text-sm">{user.mp}/75</span>
          </div>
          <div className="liquid-bar h-3">
            <div 
              className="liquid-bar-fill mp h-full rounded-full"
              style={{ width: `${(user.mp / 75) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Game Modes */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="card-game text-center cursor-pointer"
        >
          <div className="w-16 h-16 bg-gradient-danger rounded-full mx-auto mb-4 flex items-center justify-center">
            <span className="text-2xl">⚔️</span>
          </div>
          <h3 className="font-ui font-semibold text-lg mb-2">Mazmorra</h3>
          <p className="text-sm text-mist-purple-300">
            Combate enemigos en mazmorras temáticas
          </p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="card-game text-center cursor-pointer"
        >
          <div className="w-16 h-16 bg-gradient-gold rounded-full mx-auto mb-4 flex items-center justify-center">
            <span className="text-2xl">🏰</span>
          </div>
          <h3 className="font-ui font-semibold text-lg mb-2">Torre Infinita</h3>
          <p className="text-sm text-mist-purple-300">
            Sube pisos infinitos de dificultad creciente
          </p>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="card-game text-center cursor-pointer"
        >
          <div className="w-16 h-16 bg-gradient-success rounded-full mx-auto mb-4 flex items-center justify-center">
            <span className="text-2xl">👥</span>
          </div>
          <h3 className="font-ui font-semibold text-lg mb-2">PvP</h3>
          <p className="text-sm text-mist-purple-300">
            Combate contra otros jugadores
          </p>
        </motion.div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8">
        <h2 className="font-ui font-semibold text-xl mb-4">Actividad Reciente</h2>
        <div className="card-game">
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-success-400">✓ Batalla completada</span>
              <span className="text-sm text-mist-purple-400">+120 EXP</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gold-400">💰 Item obtenido</span>
              <span className="text-sm text-mist-purple-400">Poción de Tiempo</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-mystic-blue-400">📈 Nivel subido</span>
              <span className="text-sm text-mist-purple-400">Nivel 25</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 