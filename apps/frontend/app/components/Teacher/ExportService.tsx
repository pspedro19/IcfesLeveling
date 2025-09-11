'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Download,
  FileText,
  Image,
  Table,
  Calendar,
  Filter,
  Settings,
  CheckCircle,
  AlertCircle,
  Loader,
  X
} from 'lucide-react';

interface ExportOptions {
  format: 'pdf' | 'excel' | 'csv' | 'png' | 'json';
  dateRange: {
    start: string;
    end: string;
  };
  includeCharts: boolean;
  includeStudentDetails: boolean;
  includeRecommendations: boolean;
  classIds: string[];
  subjects: string[];
  dataTypes: ('analytics' | 'heatmap' | 'distractors' | 'alerts')[];
}

interface ExportJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  format: string;
  progress: number;
  downloadUrl?: string;
  error?: string;
  createdAt: Date;
  estimatedCompletion?: Date;
}

interface ExportServiceProps {
  isOpen: boolean;
  onClose: () => void;
  classId?: string;
  className?: string;
  currentView?: 'analytics' | 'heatmap' | 'distractors' | 'overview';
}

export default function ExportService({
  isOpen,
  onClose,
  classId,
  className,
  currentView = 'analytics'
}: ExportServiceProps) {
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'pdf',
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      end: new Date().toISOString().split('T')[0]
    },
    includeCharts: true,
    includeStudentDetails: false,
    includeRecommendations: true,
    classIds: classId ? [classId] : [],
    subjects: [],
    dataTypes: [currentView]
  });

  const [exportJobs, setExportJobs] = useState<ExportJob[]>([]);
  const [isExporting, setIsExporting] = useState(false);

  const formatOptions = [
    {
      format: 'pdf',
      label: 'PDF Report',
      icon: FileText,
      description: 'Reporte completo con gráficos y análisis',
      recommended: true
    },
    {
      format: 'excel',
      label: 'Excel Spreadsheet',
      icon: Table,
      description: 'Datos estructurados para análisis posterior',
      recommended: false
    },
    {
      format: 'csv',
      label: 'CSV Data',
      icon: Table,
      description: 'Datos en formato plano para importación',
      recommended: false
    },
    {
      format: 'png',
      label: 'Image Export',
      icon: Image,
      description: 'Capturas de alta resolución de visualizaciones',
      recommended: false
    },
    {
      format: 'json',
      label: 'JSON Data',
      icon: Settings,
      description: 'Datos en formato estructurado para API',
      recommended: false
    }
  ];

  const dataTypeOptions = [
    { value: 'analytics', label: 'Analytics de Clase', description: 'KPIs, métricas de rendimiento' },
    { value: 'heatmap', label: 'Mapa de Debilidades', description: 'Performance por estudiante y tema' },
    { value: 'distractors', label: 'Análisis de Distractores', description: 'Patrones de error comunes' },
    { value: 'alerts', label: 'Alertas y Riesgos', description: 'Estudiantes que requieren atención' }
  ];

  const handleExport = async () => {
    setIsExporting(true);
    
    try {
      // Crear nuevo job de exportación
      const newJob: ExportJob = {
        id: Date.now().toString(),
        status: 'pending',
        format: exportOptions.format,
        progress: 0,
        createdAt: new Date(),
        estimatedCompletion: new Date(Date.now() + 60000) // 1 minute
      };
      
      setExportJobs(prev => [newJob, ...prev]);
      
      // Simular proceso de exportación
      const jobId = newJob.id;
      
      // Update to processing
      setTimeout(() => {
        setExportJobs(prev => prev.map(job => 
          job.id === jobId ? { ...job, status: 'processing', progress: 20 } : job
        ));
      }, 1000);
      
      // Progress updates
      setTimeout(() => {
        setExportJobs(prev => prev.map(job => 
          job.id === jobId ? { ...job, progress: 50 } : job
        ));
      }, 2000);
      
      setTimeout(() => {
        setExportJobs(prev => prev.map(job => 
          job.id === jobId ? { ...job, progress: 80 } : job
        ));
      }, 3000);
      
      // Complete
      setTimeout(() => {
        setExportJobs(prev => prev.map(job => 
          job.id === jobId ? { 
            ...job, 
            status: 'completed', 
            progress: 100,
            downloadUrl: `/api/exports/${jobId}/download`
          } : job
        ));
        setIsExporting(false);
      }, 4000);
      
    } catch (error) {
      console.error('Export failed:', error);
      setIsExporting(false);
    }
  };

  const downloadFile = (job: ExportJob) => {
    if (job.downloadUrl) {
      // In a real implementation, this would trigger the actual download
      const link = document.createElement('a');
      link.href = job.downloadUrl;
      link.download = `${className || 'class-data'}-${job.format}-${new Date().toISOString().split('T')[0]}.${job.format}`;
      link.click();
    }
  };

  const getJobStatusIcon = (status: ExportJob['status']) => {
    switch (status) {
      case 'pending':
      case 'processing':
        return <Loader className="w-4 h-4 text-blue-400 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="bg-gray-900 rounded-lg border border-gray-700 w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto"
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.8, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-white">Exportar Datos</h2>
            <p className="text-gray-400 text-sm">
              {className ? `Clase: ${className}` : 'Selecciona los datos a exportar'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Format Selection */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Formato de Exportación</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {formatOptions.map((option) => (
                <div
                  key={option.format}
                  className={`relative p-4 rounded-lg border cursor-pointer transition-all ${
                    exportOptions.format === option.format
                      ? 'border-purple-500 bg-purple-500/10'
                      : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                  }`}
                  onClick={() => setExportOptions({ ...exportOptions, format: option.format as any })}
                >
                  {option.recommended && (
                    <div className="absolute -top-2 -right-2 bg-purple-600 text-white text-xs px-2 py-1 rounded-full">
                      Recomendado
                    </div>
                  )}
                  <div className="flex items-center gap-3 mb-2">
                    <option.icon className="w-5 h-5 text-purple-400" />
                    <span className="text-white font-medium">{option.label}</span>
                  </div>
                  <p className="text-gray-400 text-sm">{option.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Data Types */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Tipos de Datos</h3>
            <div className="space-y-3">
              {dataTypeOptions.map((option) => (
                <label
                  key={option.value}
                  className="flex items-start gap-3 p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    className="mt-1 w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                    checked={exportOptions.dataTypes.includes(option.value as any)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setExportOptions({
                          ...exportOptions,
                          dataTypes: [...exportOptions.dataTypes, option.value as any]
                        });
                      } else {
                        setExportOptions({
                          ...exportOptions,
                          dataTypes: exportOptions.dataTypes.filter(t => t !== option.value)
                        });
                      }
                    }}
                  />
                  <div>
                    <span className="text-white font-medium">{option.label}</span>
                    <p className="text-gray-400 text-sm">{option.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Date Range */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Rango de Fechas</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Fecha inicio</label>
                  <input
                    type="date"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
                    value={exportOptions.dateRange.start}
                    onChange={(e) => setExportOptions({
                      ...exportOptions,
                      dateRange: { ...exportOptions.dateRange, start: e.target.value }
                    })}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Fecha fin</label>
                  <input
                    type="date"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white"
                    value={exportOptions.dateRange.end}
                    onChange={(e) => setExportOptions({
                      ...exportOptions,
                      dateRange: { ...exportOptions.dateRange, end: e.target.value }
                    })}
                  />
                </div>
              </div>
            </div>

            {/* Additional Options */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Opciones Adicionales</h3>
              <div className="space-y-3">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                    checked={exportOptions.includeCharts}
                    onChange={(e) => setExportOptions({
                      ...exportOptions,
                      includeCharts: e.target.checked
                    })}
                  />
                  <span className="text-white">Incluir gráficos y visualizaciones</span>
                </label>

                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                    checked={exportOptions.includeStudentDetails}
                    onChange={(e) => setExportOptions({
                      ...exportOptions,
                      includeStudentDetails: e.target.checked
                    })}
                  />
                  <span className="text-white">Incluir detalles por estudiante</span>
                </label>

                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
                    checked={exportOptions.includeRecommendations}
                    onChange={(e) => setExportOptions({
                      ...exportOptions,
                      includeRecommendations: e.target.checked
                    })}
                  />
                  <span className="text-white">Incluir recomendaciones pedagógicas</span>
                </label>
              </div>
            </div>
          </div>

          {/* Export Jobs */}
          {exportJobs.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Historial de Exportaciones</h3>
              <div className="space-y-3 max-h-48 overflow-y-auto">
                {exportJobs.map((job) => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {getJobStatusIcon(job.status)}
                      <div>
                        <span className="text-white font-medium">
                          Export {job.format.toUpperCase()}
                        </span>
                        <p className="text-gray-400 text-sm">
                          {job.createdAt.toLocaleString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {job.status === 'processing' && (
                        <div className="w-24 bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-purple-600 h-2 rounded-full transition-all"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      )}

                      {job.status === 'completed' && (
                        <button
                          onClick={() => downloadFile(job)}
                          className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm"
                        >
                          Descargar
                        </button>
                      )}

                      {job.status === 'failed' && (
                        <span className="text-red-400 text-sm">Error</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-4 p-6 border-t border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white"
          >
            Cancelar
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting || exportOptions.dataTypes.length === 0}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg flex items-center gap-2"
          >
            {isExporting ? (
              <Loader className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            {isExporting ? 'Exportando...' : 'Exportar Datos'}
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}