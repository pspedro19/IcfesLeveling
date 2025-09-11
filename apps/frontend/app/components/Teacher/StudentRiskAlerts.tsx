'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  AlertCircle,
  Clock,
  TrendingDown,
  User,
  Mail,
  Phone,
  Calendar,
  Target,
  BookOpen,
  CheckCircle,
  XCircle,
  Eye,
  MessageCircle,
  Bell,
  Filter,
  Search,
  ArrowRight,
  Zap,
  Heart,
  Brain
} from 'lucide-react';

interface RiskAlert {
  id: string;
  studentId: string;
  studentName: string;
  studentAvatar?: string;
  classId: string;
  className: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  alertType: 'academic' | 'engagement' | 'attendance' | 'behavioral';
  title: string;
  description: string;
  riskFactors: {
    lowMastery: boolean;
    noRecentActivity: boolean;
    poorAttendance: boolean;
    longAbsence: boolean;
    decreasingPerformance: boolean;
    socialIssues: boolean;
  };
  suggestedActions: string[];
  priority: number;
  isResolved: boolean;
  resolvedAt?: Date;
  resolutionNotes?: string;
  createdAt: Date;
  updatedAt: Date;
  lastContactAttempt?: Date;
  contactMethods: ('email' | 'phone' | 'meeting' | 'message')[];
  progress: {
    interventionsPlanned: number;
    interventionsCompleted: number;
    improvementSeen: boolean;
    followUpRequired: boolean;
  };
}

interface StudentRiskAlertsProps {
  classId?: string;
  teacherId: string;
  onCreateIntervention?: (studentId: string, alertId: string) => void;
}

export default function StudentRiskAlerts({
  classId,
  teacherId,
  onCreateIntervention
}: StudentRiskAlertsProps) {
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<RiskAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<RiskAlert | null>(null);
  const [filters, setFilters] = useState({
    riskLevel: 'all',
    alertType: 'all',
    resolved: 'pending',
    search: ''
  });
  const [sortBy, setSortBy] = useState<'priority' | 'date' | 'riskLevel'>('priority');

  // Risk level colors and icons
  const getRiskConfig = (level: RiskAlert['riskLevel']) => {
    const configs = {
      low: {
        color: 'text-green-400 bg-green-500/20 border-green-500/30',
        icon: AlertCircle,
        label: 'Bajo Riesgo',
        priority: 1
      },
      medium: {
        color: 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30',
        icon: AlertTriangle,
        label: 'Riesgo Medio',
        priority: 2
      },
      high: {
        color: 'text-orange-400 bg-orange-500/20 border-orange-500/30',
        icon: AlertTriangle,
        label: 'Alto Riesgo',
        priority: 3
      },
      critical: {
        color: 'text-red-400 bg-red-500/20 border-red-500/30',
        icon: AlertTriangle,
        label: 'Riesgo Crítico',
        priority: 4
      }
    };
    return configs[level];
  };

  const getAlertTypeConfig = (type: RiskAlert['alertType']) => {
    const configs = {
      academic: {
        color: 'text-blue-400 bg-blue-500/20',
        icon: BookOpen,
        label: 'Académico'
      },
      engagement: {
        color: 'text-purple-400 bg-purple-500/20',
        icon: Heart,
        label: 'Participación'
      },
      attendance: {
        color: 'text-orange-400 bg-orange-500/20',
        icon: Clock,
        label: 'Asistencia'
      },
      behavioral: {
        color: 'text-pink-400 bg-pink-500/20',
        icon: Brain,
        label: 'Comportamental'
      }
    };
    return configs[type];
  };

  // Load alerts
  useEffect(() => {
    const loadAlerts = async () => {
      setLoading(true);
      try {
        // Mock data - replace with API call
        const mockAlerts: RiskAlert[] = [
          {
            id: 'alert-1',
            studentId: 'student-1',
            studentName: 'Carlos Rodríguez',
            classId: 'class-1',
            className: 'Matemáticas 11°A',
            riskLevel: 'critical',
            alertType: 'academic',
            title: 'Bajo rendimiento académico crítico',
            description: 'El estudiante muestra un declive significativo en su performance con mastery de 34% y sin actividad en los últimos 10 días.',
            riskFactors: {
              lowMastery: true,
              noRecentActivity: true,
              poorAttendance: false,
              longAbsence: true,
              decreasingPerformance: true,
              socialIssues: false
            },
            suggestedActions: [
              'Contactar inmediatamente al estudiante y padres',
              'Programar reunión individual urgente',
              'Evaluar necesidad de plan de recuperación',
              'Considerar tutoría personalizada'
            ],
            priority: 10,
            isResolved: false,
            createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
            updatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
            contactMethods: ['email', 'phone', 'meeting'],
            progress: {
              interventionsPlanned: 2,
              interventionsCompleted: 0,
              improvementSeen: false,
              followUpRequired: true
            }
          },
          {
            id: 'alert-2',
            studentId: 'student-2',
            studentName: 'Ana María López',
            classId: 'class-1',
            className: 'Matemáticas 11°A',
            riskLevel: 'high',
            alertType: 'engagement',
            title: 'Baja participación en clase',
            description: 'Reducción notable en la participación y compromiso con las actividades de aprendizaje.',
            riskFactors: {
              lowMastery: false,
              noRecentActivity: true,
              poorAttendance: false,
              longAbsence: false,
              decreasingPerformance: false,
              socialIssues: true
            },
            suggestedActions: [
              'Conversación personal con la estudiante',
              'Revisar dinámicas grupales',
              'Implementar actividades más interactivas',
              'Seguimiento semanal'
            ],
            priority: 7,
            isResolved: false,
            createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
            updatedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
            contactMethods: ['message', 'meeting'],
            progress: {
              interventionsPlanned: 1,
              interventionsCompleted: 1,
              improvementSeen: true,
              followUpRequired: true
            }
          },
          {
            id: 'alert-3',
            studentId: 'student-3',
            studentName: 'Diego Martínez',
            classId: 'class-1',
            className: 'Matemáticas 11°A',
            riskLevel: 'medium',
            alertType: 'attendance',
            title: 'Asistencia irregular',
            description: 'Patrón de inasistencias que puede afectar el rendimiento académico.',
            riskFactors: {
              lowMastery: false,
              noRecentActivity: false,
              poorAttendance: true,
              longAbsence: false,
              decreasingPerformance: false,
              socialIssues: false
            },
            suggestedActions: [
              'Contactar a padres de familia',
              'Investigar causas de las ausencias',
              'Proporcionar material de recuperación',
              'Establecer plan de seguimiento'
            ],
            priority: 5,
            isResolved: false,
            createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
            updatedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
            contactMethods: ['email', 'phone'],
            progress: {
              interventionsPlanned: 1,
              interventionsCompleted: 0,
              improvementSeen: false,
              followUpRequired: true
            }
          }
        ];

        setAlerts(mockAlerts);
      } catch (error) {
        console.error('Error loading alerts:', error);
      } finally {
        setLoading(false);
      }
    };

    loadAlerts();
  }, [classId, teacherId]);

  // Filter and sort alerts
  useEffect(() => {
    let filtered = alerts;

    // Apply filters
    if (filters.riskLevel !== 'all') {
      filtered = filtered.filter(alert => alert.riskLevel === filters.riskLevel);
    }

    if (filters.alertType !== 'all') {
      filtered = filtered.filter(alert => alert.alertType === filters.alertType);
    }

    if (filters.resolved === 'pending') {
      filtered = filtered.filter(alert => !alert.isResolved);
    } else if (filters.resolved === 'resolved') {
      filtered = filtered.filter(alert => alert.isResolved);
    }

    if (filters.search) {
      filtered = filtered.filter(alert =>
        alert.studentName.toLowerCase().includes(filters.search.toLowerCase()) ||
        alert.title.toLowerCase().includes(filters.search.toLowerCase()) ||
        alert.description.toLowerCase().includes(filters.search.toLowerCase())
      );
    }

    // Sort alerts
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'priority':
          return b.priority - a.priority;
        case 'date':
          return b.createdAt.getTime() - a.createdAt.getTime();
        case 'riskLevel':
          return getRiskConfig(b.riskLevel).priority - getRiskConfig(a.riskLevel).priority;
        default:
          return 0;
      }
    });

    setFilteredAlerts(filtered);
  }, [alerts, filters, sortBy]);

  const resolveAlert = async (alertId: string, notes: string) => {
    try {
      setAlerts(prev => prev.map(alert =>
        alert.id === alertId
          ? {
              ...alert,
              isResolved: true,
              resolvedAt: new Date(),
              resolutionNotes: notes,
              updatedAt: new Date()
            }
          : alert
      ));
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const contactStudent = async (alert: RiskAlert, method: string) => {
    try {
      // Update last contact attempt
      setAlerts(prev => prev.map(a =>
        a.id === alert.id
          ? { ...a, lastContactAttempt: new Date(), updatedAt: new Date() }
          : a
      ));

      // Simulate different contact methods
      switch (method) {
        case 'email':
          // Open email client
          window.location.href = `mailto:${alert.studentName.toLowerCase().replace(' ', '.')}@colegio.edu?subject=Seguimiento Académico&body=Estimado/a ${alert.studentName},%0D%0A%0D%0AMe gustaría hablar contigo sobre tu progreso en la clase.%0D%0A%0D%0ASaludos cordiales.`;
          break;
        case 'message':
          // Open messaging interface (would integrate with school's messaging system)
          alert('Función de mensajería integrada próximamente');
          break;
        case 'meeting':
          // Open calendar to schedule meeting
          alert('Integrando con calendario para programar reunión');
          break;
        default:
          break;
      }
    } catch (error) {
      console.error('Error contacting student:', error);
    }
  };

  const renderAlertCard = (alert: RiskAlert) => {
    const riskConfig = getRiskConfig(alert.riskLevel);
    const typeConfig = getAlertTypeConfig(alert.alertType);
    const RiskIcon = riskConfig.icon;
    const TypeIcon = typeConfig.icon;

    return (
      <motion.div
        key={alert.id}
        className={`bg-gray-900/80 rounded-lg border p-6 cursor-pointer hover:border-gray-600 transition-all ${riskConfig.color.split(' ')[2]}`}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        onClick={() => setSelectedAlert(alert)}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${riskConfig.color}`}>
              <RiskIcon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-white font-semibold">{alert.studentName}</h3>
              <p className="text-gray-400 text-sm">{alert.className}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <div className={`px-2 py-1 rounded text-xs font-semibold ${typeConfig.color}`}>
              <TypeIcon className="w-3 h-3 inline mr-1" />
              {typeConfig.label}
            </div>
            <div className={`px-2 py-1 rounded text-xs font-semibold ${riskConfig.color}`}>
              {riskConfig.label}
            </div>
          </div>
        </div>

        <div className="mb-4">
          <h4 className="text-white font-medium mb-1">{alert.title}</h4>
          <p className="text-gray-400 text-sm line-clamp-2">{alert.description}</p>
        </div>

        {/* Risk Factors */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {Object.entries(alert.riskFactors).map(([factor, isActive]) => {
              if (!isActive) return null;
              
              const factorLabels = {
                lowMastery: 'Bajo Mastery',
                noRecentActivity: 'Sin Actividad',
                poorAttendance: 'Mala Asistencia',
                longAbsence: 'Ausencia Prolongada',
                decreasingPerformance: 'Rendimiento Descendente',
                socialIssues: 'Issues Sociales'
              };
              
              return (
                <span
                  key={factor}
                  className="px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded-full"
                >
                  {factorLabels[factor as keyof typeof factorLabels]}
                </span>
              );
            })}
          </div>
        </div>

        {/* Progress */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-4">
            <span className="text-gray-400">
              {alert.progress.interventionsCompleted}/{alert.progress.interventionsPlanned} intervenciones
            </span>
            {alert.progress.improvementSeen && (
              <span className="text-green-400 flex items-center gap-1">
                <TrendingDown className="w-3 h-3 rotate-180" />
                Mejora vista
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-xs">
              {alert.createdAt.toLocaleDateString()}
            </span>
            {alert.lastContactAttempt && (
              <span className="text-blue-400 text-xs">
                Contactado
              </span>
            )}
          </div>
        </div>
      </motion.div>
    );
  };

  const renderAlertDetail = () => {
    if (!selectedAlert) return null;

    const riskConfig = getRiskConfig(selectedAlert.riskLevel);
    const typeConfig = getAlertTypeConfig(selectedAlert.alertType);

    return (
      <motion.div
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        onClick={() => setSelectedAlert(null)}
      >
        <motion.div
          className="bg-gray-900 rounded-lg border border-gray-700 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold text-xl">
                    {selectedAlert.studentName.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">{selectedAlert.studentName}</h2>
                  <p className="text-gray-400">{selectedAlert.className}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className={`px-2 py-1 rounded text-xs font-semibold ${riskConfig.color}`}>
                      {riskConfig.label}
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-semibold ${typeConfig.color}`}>
                      {typeConfig.label}
                    </div>
                  </div>
                </div>
              </div>
              
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {/* Alert Details */}
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-2">{selectedAlert.title}</h3>
              <p className="text-gray-300 text-sm">{selectedAlert.description}</p>
            </div>

            {/* Risk Factors */}
            <div>
              <h3 className="text-white font-semibold mb-3">Factores de Riesgo Identificados</h3>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(selectedAlert.riskFactors).map(([factor, isActive]) => {
                  const factorInfo = {
                    lowMastery: { label: 'Bajo Mastery', icon: TrendingDown },
                    noRecentActivity: { label: 'Sin Actividad Reciente', icon: Clock },
                    poorAttendance: { label: 'Mala Asistencia', icon: Calendar },
                    longAbsence: { label: 'Ausencia Prolongada', icon: AlertCircle },
                    decreasingPerformance: { label: 'Performance Descendente', icon: TrendingDown },
                    socialIssues: { label: 'Issues Sociales', icon: User }
                  };
                  
                  const info = factorInfo[factor as keyof typeof factorInfo];
                  const Icon = info.icon;
                  
                  return (
                    <div
                      key={factor}
                      className={`flex items-center gap-3 p-3 rounded-lg ${
                        isActive 
                          ? 'bg-red-500/20 border border-red-500/30' 
                          : 'bg-gray-800/30 border border-gray-700'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${isActive ? 'text-red-400' : 'text-gray-500'}`} />
                      <span className={`text-sm ${isActive ? 'text-red-300' : 'text-gray-400'}`}>
                        {info.label}
                      </span>
                      {isActive && <CheckCircle className="w-4 h-4 text-red-400 ml-auto" />}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Suggested Actions */}
            <div>
              <h3 className="text-white font-semibold mb-3">Acciones Sugeridas</h3>
              <div className="space-y-2">
                {selectedAlert.suggestedActions.map((action, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                    <ArrowRight className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                    <span className="text-blue-300 text-sm">{action}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Contact Options */}
            <div>
              <h3 className="text-white font-semibold mb-3">Opciones de Contacto</h3>
              <div className="flex flex-wrap gap-2">
                {selectedAlert.contactMethods.map((method) => {
                  const methodConfig = {
                    email: { label: 'Email', icon: Mail, color: 'bg-blue-600' },
                    phone: { label: 'Teléfono', icon: Phone, color: 'bg-green-600' },
                    message: { label: 'Mensaje', icon: MessageCircle, color: 'bg-purple-600' },
                    meeting: { label: 'Reunión', icon: Calendar, color: 'bg-orange-600' }
                  };
                  
                  const config = methodConfig[method];
                  const Icon = config.icon;
                  
                  return (
                    <button
                      key={method}
                      onClick={() => contactStudent(selectedAlert, method)}
                      className={`flex items-center gap-2 px-4 py-2 ${config.color} hover:opacity-80 text-white rounded-lg text-sm`}
                    >
                      <Icon className="w-4 h-4" />
                      {config.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-700">
              <div className="flex items-center gap-2">
                {onCreateIntervention && (
                  <button
                    onClick={() => onCreateIntervention(selectedAlert.studentId, selectedAlert.id)}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm"
                  >
                    Crear Intervención
                  </button>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                {!selectedAlert.isResolved && (
                  <button
                    onClick={() => {
                      const notes = prompt('Notas de resolución:');
                      if (notes) {
                        resolveAlert(selectedAlert.id, notes);
                        setSelectedAlert(null);
                      }
                    }}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm"
                  >
                    Marcar como Resuelto
                  </button>
                )}
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Alertas de Estudiantes en Riesgo</h2>
          <p className="text-gray-400">
            {filteredAlerts.length} alerta{filteredAlerts.length !== 1 ? 's' : ''} 
            {filters.resolved === 'pending' ? ' pendientes' : filters.resolved === 'resolved' ? ' resueltas' : ''}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-900/80 rounded-lg border border-gray-700/50 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Buscar</label>
            <div className="relative">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Nombre del estudiante..."
                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400"
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Nivel de Riesgo</label>
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
              value={filters.riskLevel}
              onChange={(e) => setFilters({ ...filters, riskLevel: e.target.value })}
            >
              <option value="all">Todos los niveles</option>
              <option value="critical">Crítico</option>
              <option value="high">Alto</option>
              <option value="medium">Medio</option>
              <option value="low">Bajo</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Tipo de Alerta</label>
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
              value={filters.alertType}
              onChange={(e) => setFilters({ ...filters, alertType: e.target.value })}
            >
              <option value="all">Todos los tipos</option>
              <option value="academic">Académico</option>
              <option value="engagement">Participación</option>
              <option value="attendance">Asistencia</option>
              <option value="behavioral">Comportamental</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Estado</label>
            <select
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
              value={filters.resolved}
              onChange={(e) => setFilters({ ...filters, resolved: e.target.value })}
            >
              <option value="all">Todas</option>
              <option value="pending">Pendientes</option>
              <option value="resolved">Resueltas</option>
            </select>
          </div>
        </div>
      </div>

      {/* Sort Options */}
      <div className="flex items-center gap-4">
        <span className="text-gray-400 text-sm">Ordenar por:</span>
        <div className="flex gap-2">
          {[
            { value: 'priority', label: 'Prioridad' },
            { value: 'date', label: 'Fecha' },
            { value: 'riskLevel', label: 'Nivel de Riesgo' }
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => setSortBy(option.value as any)}
              className={`px-3 py-1 rounded text-sm transition-all ${
                sortBy === option.value
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AnimatePresence>
          {filteredAlerts.map(renderAlertCard)}
        </AnimatePresence>
      </div>

      {filteredAlerts.length === 0 && (
        <div className="text-center py-12">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-400">No se encontraron alertas con los filtros aplicados</p>
        </div>
      )}

      {/* Alert Detail Modal */}
      <AnimatePresence>
        {selectedAlert && renderAlertDetail()}
      </AnimatePresence>
    </div>
  );
}