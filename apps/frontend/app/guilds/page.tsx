'use client';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Users, Trophy, MessageSquare, Target, TrendingUp, Crown, 
  Calendar, MapPin, Star, Award, MessageCircle, Search,
  Plus, ArrowRight, ChevronRight, School, Building
} from 'lucide-react';

interface Guild {
  guild_id: string;
  guild_name: string;
  school_name: string;
  school_city: string;
  role: string;
  total_members: number;
  total_score: number;
  average_level: number;
  guild_level: number;
  joined_at: string;
}

interface GuildMember {
  id: string;
  user_id: string;
  role: string;
  joined_at: string;
  contribution_score: number;
  last_activity: string;
  user_display_name: string;
  user_level: number;
  user_avatar_url: string;
}

interface Tournament {
  id: string;
  name: string;
  description: string;
  tournament_type: string;
  start_date: string;
  end_date: string;
  status: string;
  max_participants: number;
  current_participants: number;
  prize_pool: any;
}

interface SchoolRanking {
  id: string;
  school_name: string;
  school_city: string;
  total_students: number;
  average_score: number;
  total_battles_won: number;
  total_experience: number;
  rank_position: number;
  ranking_period: string;
}

interface GuildChatMessage {
  id: string;
  user_id: string;
  message: string;
  message_type: string;
  created_at: string;
  user_display_name: string;
  user_avatar_url: string;
}

interface GuildStatistics {
  total_members: number;
  total_score: number;
  average_level: number;
  guild_level: number;
  guild_experience: number;
  battles_won: number;
  battles_lost: number;
  tournaments_participated: number;
  tournaments_won: number;
}

export default function GuildsPage() {
  const [userGuild, setUserGuild] = useState<Guild | null>(null);
  const [guildMembers, setGuildMembers] = useState<GuildMember[]>([]);
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [schoolRankings, setSchoolRankings] = useState<SchoolRanking[]>([]);
  const [chatMessages, setChatMessages] = useState<GuildChatMessage[]>([]);
  const [guildStatistics, setGuildStatistics] = useState<GuildStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('guild');
  const [newMessage, setNewMessage] = useState('');
  const [schoolName, setSchoolName] = useState('');
  const [schoolCity, setSchoolCity] = useState('');

  const userId = 'user-123'; // Mock user ID

  useEffect(() => {
    fetchGuildData();
  }, []);

  const fetchGuildData = async () => {
    try {
      setLoading(true);
      
      // Fetch user's guild
      const guildResponse = await fetch(`/api/v1/guilds/user-guild/${userId}`);
      if (guildResponse.ok) {
        const guildData = await guildResponse.json();
        setUserGuild(guildData);
        
        // Fetch guild members
        const membersResponse = await fetch(`/api/v1/guilds/${guildData.guild_id}/members`);
        if (membersResponse.ok) {
          const membersData = await membersResponse.json();
          setGuildMembers(membersData);
        }
        
        // Fetch guild statistics
        const statsResponse = await fetch(`/api/v1/guilds/${guildData.guild_id}/statistics`);
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          setGuildStatistics(statsData);
        }
        
        // Fetch guild chat
        const chatResponse = await fetch(`/api/v1/guilds/${guildData.guild_id}/chat`);
        if (chatResponse.ok) {
          const chatData = await chatResponse.json();
          setChatMessages(chatData);
        }
      } else {
        // User not in guild, show school detection
        setUserGuild(null);
      }
      
      // Fetch tournaments
      const tournamentsResponse = await fetch('/api/v1/guilds/tournaments/available');
      if (tournamentsResponse.ok) {
        const tournamentsData = await tournamentsResponse.json();
        setTournaments(tournamentsData);
      }
      
      // Fetch school rankings
      const rankingsResponse = await fetch('/api/v1/guilds/school-rankings');
      if (rankingsResponse.ok) {
        const rankingsData = await rankingsResponse.json();
        setSchoolRankings(rankingsData);
      }
      
    } catch (error) {
      console.error('Error fetching guild data:', error);
      setError('Error al cargar datos del gremio');
    } finally {
      setLoading(false);
    }
  };

  const joinSchool = async () => {
    try {
      const response = await fetch('/api/v1/guilds/auto-detect-school', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          school_name: schoolName,
          school_city: schoolCity
        })
      });
      
      if (response.ok) {
        await fetchGuildData();
      }
    } catch (error) {
      console.error('Error joining school:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !userGuild) return;
    
    try {
      const response = await fetch(`/api/v1/guilds/${userGuild.guild_id}/chat/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          guild_id: userGuild.guild_id,
          user_id: userId,
          message: newMessage,
          message_type: 'text'
        })
      });
      
      if (response.ok) {
        setNewMessage('');
        await fetchGuildData(); // Refresh chat
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const joinTournament = async (tournamentId: string) => {
    if (!userGuild) return;
    
    try {
      const response = await fetch(`/api/v1/guilds/tournaments/${tournamentId}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tournament_id: tournamentId,
          guild_id: userGuild.guild_id,
          user_id: userId
        })
      });
      
      if (response.ok) {
        await fetchGuildData();
      }
    } catch (error) {
      console.error('Error joining tournament:', error);
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'leader': return <Crown className="text-yellow-400" />;
      case 'officer': return <Star className="text-blue-400" />;
      default: return <Users className="text-gray-400" />;
    }
  };

  const getRoleText = (role: string) => {
    switch (role) {
      case 'leader': return 'Líder';
      case 'officer': return 'Oficial';
      default: return 'Miembro';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-xl">Cargando gremios...</div>
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
            <Users className="inline-block mr-3 text-blue-400" />
            Gremios por Colegio
          </h1>
          <p className="text-xl text-gray-300">
            Compite con tu colegio y demuestra tu dominio
          </p>
        </motion.div>

        {/* School Detection (if not in guild) */}
        {!userGuild && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white/10 backdrop-blur-sm rounded-lg p-6 mb-8"
          >
            <h2 className="text-2xl font-bold text-white mb-4">
              <School className="inline-block mr-3" />
              Únete a tu Colegio
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-white mb-2">Nombre del Colegio</label>
                <input
                  type="text"
                  value={schoolName}
                  onChange={(e) => setSchoolName(e.target.value)}
                  className="w-full p-3 rounded-lg bg-white/20 text-white border border-white/30 focus:border-blue-400"
                  placeholder="Ej: Colegio San José"
                />
              </div>
              <div>
                <label className="block text-white mb-2">Ciudad</label>
                <input
                  type="text"
                  value={schoolCity}
                  onChange={(e) => setSchoolCity(e.target.value)}
                  className="w-full p-3 rounded-lg bg-white/20 text-white border border-white/30 focus:border-blue-400"
                  placeholder="Ej: Bogotá"
                />
              </div>
            </div>
            <button
              onClick={joinSchool}
              disabled={!schoolName.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              <Plus className="inline-block mr-2" />
              Unirse al Colegio
            </button>
          </motion.div>
        )}

        {/* Tabs */}
        {userGuild && (
          <div className="flex space-x-1 mb-8 bg-white/10 rounded-lg p-1">
            {[
              { id: 'guild', label: 'Mi Gremio', icon: Users },
              { id: 'rankings', label: 'Rankings', icon: Trophy },
              { id: 'tournaments', label: 'Torneos', icon: Target },
              { id: 'chat', label: 'Chat', icon: MessageSquare }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-md transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        )}

        {/* Tab Content */}
        {userGuild && (
          <div className="space-y-8">
            {/* Guild Tab */}
            {activeTab === 'guild' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Guild Info */}
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-bold text-white">{userGuild.guild_name}</h2>
                    <div className="flex items-center space-x-2">
                      {getRoleIcon(userGuild.role)}
                      <span className="text-white">{getRoleText(userGuild.role)}</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-400">{userGuild.total_members}</div>
                      <div className="text-white">Miembros</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-400">{userGuild.total_score}</div>
                      <div className="text-white">Puntaje Total</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-yellow-400">{userGuild.average_level}</div>
                      <div className="text-white">Nivel Promedio</div>
                    </div>
                  </div>
                  <div className="text-gray-300">
                    <MapPin className="inline-block mr-2" />
                    {userGuild.school_name} - {userGuild.school_city}
                  </div>
                </div>

                {/* Guild Statistics */}
                {guildStatistics && (
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
                    <h3 className="text-xl font-bold text-white mb-4">Estadísticas del Gremio</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-400">{guildStatistics.battles_won}</div>
                        <div className="text-white text-sm">Batallas Ganadas</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-red-400">{guildStatistics.battles_lost}</div>
                        <div className="text-white text-sm">Batallas Perdidas</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-400">{guildStatistics.tournaments_participated}</div>
                        <div className="text-white text-sm">Torneos Participados</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-yellow-400">{guildStatistics.tournaments_won}</div>
                        <div className="text-white text-sm">Torneos Ganados</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Guild Members */}
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
                  <h3 className="text-xl font-bold text-white mb-4">Miembros del Gremio</h3>
                  <div className="space-y-3">
                    {guildMembers.map((member) => (
                      <div key={member.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                        <div className="flex items-center space-x-3">
                          {member.user_avatar_url ? (
                            <img
                              src={member.user_avatar_url}
                              alt={member.user_display_name}
                              className="w-10 h-10 rounded-full"
                            />
                          ) : (
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                              <Users className="text-white" />
                            </div>
                          )}
                          <div>
                            <div className="text-white font-semibold">{member.user_display_name}</div>
                            <div className="text-gray-300 text-sm">Nivel {member.user_level}</div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {getRoleIcon(member.role)}
                          <span className="text-white text-sm">{getRoleText(member.role)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Rankings Tab */}
            {activeTab === 'rankings' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
                  <h2 className="text-2xl font-bold text-white mb-6">
                    <Trophy className="inline-block mr-3" />
                    Rankings por Colegio
                  </h2>
                  <div className="space-y-4">
                    {schoolRankings.map((ranking, index) => (
                      <div key={ranking.id} className="flex items-center justify-between p-4 bg-white/5 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <div className="text-2xl font-bold text-yellow-400">#{ranking.rank_position}</div>
                          <div>
                            <div className="text-white font-semibold">{ranking.school_name}</div>
                            <div className="text-gray-300 text-sm">{ranking.school_city}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-white font-semibold">{ranking.average_score} pts</div>
                          <div className="text-gray-300 text-sm">{ranking.total_students} estudiantes</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Tournaments Tab */}
            {activeTab === 'tournaments' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
                  <h2 className="text-2xl font-bold text-white mb-6">
                    <Target className="inline-block mr-3" />
                    Torneos Disponibles
                  </h2>
                  <div className="space-y-4">
                    {tournaments.map((tournament) => (
                      <div key={tournament.id} className="p-4 bg-white/5 rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="text-white font-semibold">{tournament.name}</h3>
                          <span className={`px-3 py-1 rounded-full text-sm ${
                            tournament.status === 'active' ? 'bg-green-600' : 'bg-yellow-600'
                          } text-white`}>
                            {tournament.status === 'active' ? 'Activo' : 'Próximo'}
                          </span>
                        </div>
                        <p className="text-gray-300 mb-3">{tournament.description}</p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                          <div>
                            <div className="text-white font-semibold">{tournament.current_participants}/{tournament.max_participants}</div>
                            <div className="text-gray-300 text-sm">Participantes</div>
                          </div>
                          <div>
                            <div className="text-white font-semibold">{tournament.tournament_type}</div>
                            <div className="text-gray-300 text-sm">Tipo</div>
                          </div>
                          <div>
                            <div className="text-white font-semibold">{new Date(tournament.start_date).toLocaleDateString()}</div>
                            <div className="text-gray-300 text-sm">Inicio</div>
                          </div>
                          <div>
                            <div className="text-white font-semibold">{new Date(tournament.end_date).toLocaleDateString()}</div>
                            <div className="text-gray-300 text-sm">Fin</div>
                          </div>
                        </div>
                        <button
                          onClick={() => joinTournament(tournament.id)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
                        >
                          Unirse al Torneo
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Chat Tab */}
            {activeTab === 'chat' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-6">
                  <h2 className="text-2xl font-bold text-white mb-6">
                    <MessageSquare className="inline-block mr-3" />
                    Chat del Gremio
                  </h2>
                  
                  {/* Chat Messages */}
                  <div className="h-96 overflow-y-auto mb-4 space-y-3">
                    {chatMessages.map((message) => (
                      <div key={message.id} className="flex items-start space-x-3">
                        {message.user_avatar_url ? (
                          <img
                            src={message.user_avatar_url}
                            alt={message.user_display_name}
                            className="w-8 h-8 rounded-full"
                          />
                        ) : (
                          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                            <Users className="text-white text-sm" />
                          </div>
                        )}
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-white font-semibold">{message.user_display_name}</span>
                            <span className="text-gray-400 text-sm">
                              {new Date(message.created_at).toLocaleTimeString()}
                            </span>
                          </div>
                          <div className="text-white">{message.message}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {/* Send Message */}
                  <div className="flex space-x-3">
                    <input
                      type="text"
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                      placeholder="Escribe un mensaje..."
                      className="flex-1 p-3 rounded-lg bg-white/20 text-white border border-white/30 focus:border-blue-400"
                    />
                    <button
                      onClick={sendMessage}
                      disabled={!newMessage.trim()}
                      className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
                    >
                      <MessageCircle className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 