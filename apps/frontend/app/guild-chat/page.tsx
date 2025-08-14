'use client';

import React, { useState } from 'react';
import GuildChat from '@/components/GuildChat/GuildChat';
import { AudioProvider } from '@/components/PortalLogin/AudioEngine';
import { motion } from 'framer-motion';
import { Shield, Crown, Sword, Users, MessageSquare } from 'lucide-react';

export default function GuildChatPage() {
  const [selectedGuild, setSelectedGuild] = useState<string | null>(null);
  
  // Mock guilds for demonstration
  const mockGuilds = [
    {
      id: 'guild-001',
      name: 'Shadow Hunters',
      description: 'Elite hunters unidos para dominar las mazmorras',
      memberCount: 42,
      icon: <Sword className="w-8 h-8" />,
      color: 'from-purple-500 to-purple-700'
    },
    {
      id: 'guild-002',
      name: 'Math Warriors',
      description: 'Especialistas en problemas matemáticos complejos',
      memberCount: 28,
      icon: <Crown className="w-8 h-8" />,
      color: 'from-yellow-500 to-yellow-700'
    },
    {
      id: 'guild-003',
      name: 'Knowledge Seekers',
      description: 'Exploradores del conocimiento infinito',
      memberCount: 35,
      icon: <Shield className="w-8 h-8" />,
      color: 'from-blue-500 to-blue-700'
    }
  ];
  
  return (
    <AudioProvider>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 p-8">
        <div className="max-w-7xl mx-auto">
          <motion.h1 
            className="text-4xl font-bold text-white text-center mb-8 font-cinzel"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            Sistema de Chat de Gremios
          </motion.h1>
          
          {!selectedGuild ? (
            <div>
              <p className="text-center text-gray-300 mb-8">
                Selecciona un gremio para unirte al chat
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {mockGuilds.map((guild, index) => (
                  <motion.div
                    key={guild.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="bg-gray-800/50 rounded-lg p-6 hover:bg-gray-800/70 
                      transition-all cursor-pointer border-2 border-transparent 
                      hover:border-purple-500"
                    onClick={() => setSelectedGuild(guild.id)}
                  >
                    <div className={`w-20 h-20 rounded-full bg-gradient-to-br ${guild.color} 
                      flex items-center justify-center mx-auto mb-4 text-white`}>
                      {guild.icon}
                    </div>
                    
                    <h3 className="text-xl font-bold text-white text-center mb-2">
                      {guild.name}
                    </h3>
                    
                    <p className="text-gray-400 text-center text-sm mb-4">
                      {guild.description}
                    </p>
                    
                    <div className="flex items-center justify-center gap-2 text-gray-300">
                      <Users className="w-4 h-4" />
                      <span className="text-sm">{guild.memberCount} miembros</span>
                    </div>
                  </motion.div>
                ))}
              </div>
              
              <div className="mt-12 bg-gray-800/30 rounded-lg p-8">
                <h2 className="text-2xl font-semibold text-white mb-6 text-center">
                  Características del Chat de Gremio
                </h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-start gap-4">
                    <MessageSquare className="w-8 h-8 text-purple-400 flex-shrink-0" />
                    <div>
                      <h3 className="font-semibold text-white mb-2">
                        Chat en Tiempo Real
                      </h3>
                      <p className="text-gray-400 text-sm">
                        Comunicación instantánea con miembros del gremio usando WebSocket
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <Crown className="w-8 h-8 text-yellow-400 flex-shrink-0" />
                    <div>
                      <h3 className="font-semibold text-white mb-2">
                        Sistema de Roles
                      </h3>
                      <p className="text-gray-400 text-sm">
                        Líder, oficiales y miembros con permisos diferenciados
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <Sword className="w-8 h-8 text-red-400 flex-shrink-0" />
                    <div>
                      <h3 className="font-semibold text-white mb-2">
                        Notificaciones de Eventos
                      </h3>
                      <p className="text-gray-400 text-sm">
                        Alertas de raids, logros y actividades del gremio
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-4">
                    <Shield className="w-8 h-8 text-blue-400 flex-shrink-0" />
                    <div>
                      <h3 className="font-semibold text-white mb-2">
                        IA Moderadora
                      </h3>
                      <p className="text-gray-400 text-sm">
                        Sugerencias inteligentes y moderación automática
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-4"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-semibold text-white">
                  Chat de {mockGuilds.find(g => g.id === selectedGuild)?.name}
                </h2>
                
                <button
                  onClick={() => setSelectedGuild(null)}
                  className="bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 
                    rounded-lg transition-colors"
                >
                  Cambiar Gremio
                </button>
              </div>
              
              <GuildChat
                guildId={selectedGuild}
                guildName={mockGuilds.find(g => g.id === selectedGuild)?.name || 'Gremio'}
                maxHeight="700px"
              />
              
              <div className="bg-gray-800/50 rounded-lg p-4 mt-4">
                <p className="text-sm text-gray-400 text-center">
                  💡 Tip: Usa @nombre para mencionar a otros miembros • 
                  Los emojis están permitidos • 
                  Mantén un ambiente respetuoso
                </p>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </AudioProvider>
  );
}