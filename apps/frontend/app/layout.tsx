import type { Metadata } from 'next'
import { Inter, Cinzel, Orbitron, Fira_Code, Bebas_Neue, Rubik } from 'next/font/google'
import './globals.css'
import React from 'react'
import { QueryProvider } from './providers/QueryProvider'
import { ErrorBoundary } from './components/ErrorBoundary'
import AnalyticsProvider from './providers/AnalyticsProvider'
import dynamic from 'next/dynamic'

const ParticleBackground = dynamic(() => import('./components/gamified/ParticleBackground'), { ssr: false })
const MainNavigation = dynamic(() => import('./components/Navigation/MainNavigation'), { ssr: false })

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-inter'
})

const cinzel = Cinzel({ 
  subsets: ['latin'],
  variable: '--font-cinzel'
})

const orbitron = Orbitron({ 
  subsets: ['latin'],
  variable: '--font-orbitron'
})

const firaCode = Fira_Code({ 
  subsets: ['latin'],
  variable: '--font-fira-code'
})

const bebasNeue = Bebas_Neue({ 
  weight: '400',
  subsets: ['latin'],
  variable: '--font-bebas',
  display: 'swap'
})

const rubik = Rubik({ 
  subsets: ['latin'],
  variable: '--font-rubik',
  display: 'swap'
})

export const metadata: Metadata = {
  title: 'ICFES LEVELING - Videojuego Educativo',
  description: 'Combate enemigos académicos mientras preparas tu ICFES. RPG educativo inspirado en Solo Leveling.',
  keywords: 'ICFES, educación, videojuego, RPG, matemáticas, ciencias, lenguaje',
  authors: [{ name: 'ICFES LEVELING Team' }],
  manifest: '/manifest.json',
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#0A0A0A',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" className="dark">
      <body className={`
        ${inter.variable} 
        ${cinzel.variable} 
        ${orbitron.variable} 
        ${firaCode.variable}
        ${bebasNeue.variable}
        ${rubik.variable}
        font-body
        bg-game-void
        text-white
        antialiased
        min-h-screen
      `}>
        <ErrorBoundary>
          <QueryProvider>
            <AnalyticsProvider>
              {/* <ServiceWorkerRegistration /> */}
              <div className="relative min-h-screen">
                {/* Background Scene */}
                <div className="fixed inset-0 z-0">
                  <div className="absolute inset-0 bg-gradient-to-br from-game-abyss via-game-shadow to-game-void opacity-90 breathing-bg"></div>
                  <div className="absolute inset-0 bg-game-radial opacity-20 time-gradient"></div>
                  <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-game-neonPurple/10 rounded-full blur-3xl animate-float-slow"></div>
                  <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-game-neonBlue/10 rounded-full blur-3xl animate-float-slow" style={{ animationDelay: '2s' }}></div>
                  <div className="absolute top-3/4 right-1/3 w-64 h-64 bg-game-neonGold/5 rounded-full blur-2xl animate-float-slow" style={{ animationDelay: '4s' }}></div>
                  <ParticleBackground />
                </div>
                
                {/* Navigation - Temporarily disabled */}
                {/* <MainNavigation /> */}
                
                {/* Main Content */}
                <div className="relative z-10">
                  {children}
                </div>
              </div>
            </AnalyticsProvider>
          </QueryProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
} 