import type { Metadata } from 'next'
import { Inter, Cinzel, Orbitron, Fira_Code } from 'next/font/google'
import './globals.css'
import React from 'react'

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

export const metadata: Metadata = {
  title: 'ICFES LEVELING - Videojuego Educativo',
  description: 'Combate enemigos académicos mientras preparas tu ICFES. RPG educativo inspirado en Solo Leveling.',
  keywords: 'ICFES, educación, videojuego, RPG, matemáticas, ciencias, lenguaje',
  authors: [{ name: 'ICFES LEVELING Team' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#0A0A0A',
  manifest: '/manifest.json',
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
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
        font-body
        bg-bg-primary
        text-white
        antialiased
        min-h-screen
      `}>
        <div className="relative min-h-screen">
          {/* Background Scene */}
          <div className="fixed inset-0 z-0">
            <div className="absolute inset-0 bg-gradient-mystic opacity-90"></div>
            <div className="absolute inset-0 bg-stars-bg opacity-20"></div>
          </div>
          
          {/* Main Content */}
          <div className="relative z-10">
            {children}
          </div>
        </div>
      </body>
    </html>
  )
} 