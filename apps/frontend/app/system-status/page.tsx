'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Server,
  Globe,
  Database,
  Shield,
  Zap,
  Activity
} from 'lucide-react';

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'error' | 'warning' | 'loading';
  message: string;
  icon: React.ElementType;
  endpoint?: string;
}

export default function SystemStatusPage() {
  const [services, setServices] = useState<ServiceStatus[]>([
    {
      name: 'Frontend (Next.js)',
      status: 'loading',
      message: 'Checking...',
      icon: Globe,
    },
    {
      name: 'Backend API',
      status: 'loading',
      message: 'Checking...',
      icon: Server,
      endpoint: 'http://localhost:4000/api/v1/health'
    },
    {
      name: 'Student Dashboard API',
      status: 'loading',
      message: 'Checking...',
      icon: Activity,
      endpoint: 'http://localhost:4000/api/v1/dashboard/student'
    },
    {
      name: 'Teacher Dashboard API',
      status: 'loading',
      message: 'Checking...',
      icon: Shield,
      endpoint: 'http://localhost:4000/api/v1/dashboard/teacher'
    },
    {
      name: 'Authentication',
      status: 'loading',
      message: 'Checking...',
      icon: Zap,
      endpoint: 'http://localhost:4000/api/v1/auth-simple/login'
    },
    {
      name: 'PostgreSQL Database',
      status: 'loading',
      message: 'Checking...',
      icon: Database,
    }
  ]);

  const [loading, setLoading] = useState(false);

  const checkServices = async () => {
    setLoading(true);
    const updatedServices = [...services];

    // Frontend is always healthy if this page loads
    updatedServices[0] = {
      ...updatedServices[0],
      status: 'healthy',
      message: 'Frontend is running on port 3000'
    };

    // Check each API endpoint
    for (let i = 1; i < updatedServices.length - 1; i++) {
      const service = updatedServices[i];
      if (service.endpoint) {
        try {
          const response = await fetch(service.endpoint, {
            method: service.name === 'Authentication' ? 'POST' : 'GET',
            headers: {
              'Content-Type': 'application/json'
            },
            body: service.name === 'Authentication' 
              ? JSON.stringify({ username: 'test', password: 'wrong' })
              : undefined
          });

          if (service.name === 'Authentication') {
            // For auth, we expect a 401 error with wrong credentials
            updatedServices[i] = {
              ...service,
              status: response.status === 401 ? 'healthy' : 'warning',
              message: response.status === 401 
                ? 'Authentication endpoint is working'
                : `Unexpected response: ${response.status}`
            };
          } else if (response.ok) {
            updatedServices[i] = {
              ...service,
              status: 'healthy',
              message: 'API endpoint is responding'
            };
          } else {
            updatedServices[i] = {
              ...service,
              status: 'warning',
              message: `HTTP ${response.status}: ${response.statusText}`
            };
          }
        } catch (error) {
          updatedServices[i] = {
            ...service,
            status: 'error',
            message: 'Connection failed - service may be down'
          };
        }
      }
    }

    // Check database (assume healthy if backend is healthy)
    const backendHealthy = updatedServices[1].status === 'healthy';
    updatedServices[updatedServices.length - 1] = {
      ...updatedServices[updatedServices.length - 1],
      status: backendHealthy ? 'healthy' : 'warning',
      message: backendHealthy 
        ? 'Database connection via backend is working'
        : 'Cannot verify database status - backend issues'
    };

    setServices(updatedServices);
    setLoading(false);
  };

  useEffect(() => {
    checkServices();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle2 className="w-6 h-6 text-green-400" />;
      case 'error':
        return <XCircle className="w-6 h-6 text-red-400" />;
      case 'warning':
        return <AlertCircle className="w-6 h-6 text-yellow-400" />;
      default:
        return <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'border-green-500/50 bg-green-900/20';
      case 'error':
        return 'border-red-500/50 bg-red-900/20';
      case 'warning':
        return 'border-yellow-500/50 bg-yellow-900/20';
      default:
        return 'border-gray-500/50 bg-gray-900/20';
    }
  };

  const healthyCount = services.filter(s => s.status === 'healthy').length;
  const totalServices = services.length;
  const overallHealth = healthyCount / totalServices;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 text-white p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            System Status
          </h1>
          <p className="text-gray-300 text-lg">
            ICFES Leveling Platform Health Monitor
          </p>
        </div>

        {/* Overall Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`mb-8 p-6 rounded-xl border-2 ${
            overallHealth === 1 
              ? 'border-green-500/50 bg-green-900/20'
              : overallHealth > 0.7
              ? 'border-yellow-500/50 bg-yellow-900/20'
              : 'border-red-500/50 bg-red-900/20'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2">
                {overallHealth === 1 
                  ? '🟢 All Systems Operational'
                  : overallHealth > 0.7
                  ? '🟡 Partial Service Issues'
                  : '🔴 Multiple Service Issues'
                }
              </h2>
              <p className="text-gray-300">
                {healthyCount} of {totalServices} services are healthy
              </p>
            </div>
            <button
              onClick={checkServices}
              disabled={loading}
              className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 px-4 py-2 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>

          {/* Health Bar */}
          <div className="mt-4 w-full bg-gray-800 rounded-full h-3">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${overallHealth * 100}%` }}
              transition={{ duration: 1, ease: "easeInOut" }}
              className={`h-3 rounded-full ${
                overallHealth === 1
                  ? 'bg-green-500'
                  : overallHealth > 0.7
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
            />
          </div>
        </motion.div>

        {/* Service Status Cards */}
        <div className="grid gap-4 md:grid-cols-2">
          {services.map((service, index) => {
            const Icon = service.icon;
            return (
              <motion.div
                key={service.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`p-4 rounded-xl border-2 ${getStatusColor(service.status)} backdrop-blur-sm`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <Icon className="w-8 h-8 text-purple-400" />
                    <div>
                      <h3 className="font-bold text-lg">{service.name}</h3>
                      <p className="text-gray-300 text-sm">{service.message}</p>
                    </div>
                  </div>
                  {getStatusIcon(service.status)}
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Quick Links */}
        <div className="mt-8 text-center">
          <h3 className="text-xl font-bold mb-4">Quick Access</h3>
          <div className="flex flex-wrap justify-center gap-4">
            <a
              href="http://localhost:3000"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors"
            >
              Frontend (Port 3000)
            </a>
            <a
              href="http://localhost:4000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg transition-colors"
            >
              API Docs (Port 8000)
            </a>
            <a
              href="/login"
              className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg transition-colors"
            >
              Login Page
            </a>
            <a
              href="/student-dashboard"
              className="bg-pink-600 hover:bg-pink-700 px-4 py-2 rounded-lg transition-colors"
            >
              Student Dashboard
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}