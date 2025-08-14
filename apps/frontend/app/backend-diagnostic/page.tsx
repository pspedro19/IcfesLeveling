'use client';

import { useState, useEffect } from 'react';
import { backendHealthService, BackendHealthStatus } from '../services/backend-health.service';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Separator } from '../components/ui/separator';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  RefreshCw, 
  Server, 
  Database, 
  Shield, 
  FileText,
  Clock,
  Wifi,
  WifiOff
} from 'lucide-react';

export default function BackendDiagnosticPage() {
  const [healthStatus, setHealthStatus] = useState<BackendHealthStatus | null>(null);
  const [detailedHealth, setDetailedHealth] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [connectionInfo, setConnectionInfo] = useState<any>(null);

  useEffect(() => {
    setConnectionInfo(backendHealthService.getConnectionInfo());
    performHealthCheck();
  }, []);

  const performHealthCheck = async (forceCheck: boolean = false) => {
    setIsLoading(true);
    try {
      const health = await backendHealthService.checkHealth(forceCheck);
      setHealthStatus(health);
      
      if (health.isConnected) {
        const detailed = await backendHealthService.checkDetailedHealth();
        setDetailedHealth(detailed);
      }
      
      setLastCheck(new Date());
    } catch (error) {
      console.error('Error en verificación de salud:', error);
      setHealthStatus({
        isConnected: false,
        status: 'unreachable',
        error: error instanceof Error ? error.message : 'Error desconocido'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'unhealthy':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'unreachable':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <Badge variant="default" className="bg-green-500">Conectado</Badge>;
      case 'unhealthy':
        return <Badge variant="secondary" className="bg-yellow-500">Problemas</Badge>;
      case 'unreachable':
        return <Badge variant="destructive">Desconectado</Badge>;
      default:
        return <Badge variant="outline">Desconocido</Badge>;
    }
  };

  const getConnectionIcon = (isConnected: boolean) => {
    return isConnected ? 
      <Wifi className="h-4 w-4 text-green-500" /> : 
      <WifiOff className="h-4 w-4 text-red-500" />;
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">🔧 Diagnóstico del Backend</h1>
        <p className="text-muted-foreground">
          Verifica el estado de conexión y salud del servidor backend
        </p>
      </div>

      {/* Información de Conexión */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Información de Conexión
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-2">
              <span className="font-medium">URL:</span>
              <code className="bg-muted px-2 py-1 rounded text-sm">
                {connectionInfo?.url || 'N/A'}
              </code>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium">Puerto:</span>
              <Badge variant="outline">{connectionInfo?.port || 'N/A'}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-medium">Protocolo:</span>
              <Badge variant="outline">{connectionInfo?.protocol || 'N/A'}</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Estado General */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getStatusIcon(healthStatus?.status || 'unreachable')}
            Estado General del Backend
          </CardTitle>
          <CardDescription>
            Última verificación: {lastCheck ? lastCheck.toLocaleString() : 'Nunca'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {getConnectionIcon(healthStatus?.isConnected || false)}
              <span className="font-medium">Estado de Conexión:</span>
              {getStatusBadge(healthStatus?.status || 'unreachable')}
            </div>
            <Button 
              onClick={() => performHealthCheck(true)}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              {isLoading ? 'Verificando...' : 'Verificar Ahora'}
            </Button>
          </div>

          {healthStatus?.responseTime && (
            <div className="flex items-center gap-2 mb-4">
              <Clock className="h-4 w-4 text-blue-500" />
              <span>Tiempo de respuesta: <strong>{healthStatus.responseTime}ms</strong></span>
            </div>
          )}

          {healthStatus?.error && (
            <Alert className="mt-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>Error:</strong> {healthStatus.error}
              </AlertDescription>
            </Alert>
          )}

          {healthStatus?.details && (
            <div className="mt-4">
              <h4 className="font-medium mb-2">Detalles de la Respuesta:</h4>
              <pre className="bg-muted p-3 rounded text-sm overflow-x-auto">
                {JSON.stringify(healthStatus.details, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Verificación Detallada */}
      {detailedHealth && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Verificación Detallada de Servicios</CardTitle>
            <CardDescription>
              Estado de los diferentes componentes del backend
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-3 p-3 border rounded">
                <Database className={`h-5 w-5 ${detailedHealth.database ? 'text-green-500' : 'text-red-500'}`} />
                <div>
                  <div className="font-medium">Base de Datos</div>
                  <div className="text-sm text-muted-foreground">
                    {detailedHealth.database ? 'Conectada' : 'Desconectada'}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 border rounded">
                <Shield className={`h-5 w-5 ${detailedHealth.auth ? 'text-green-500' : 'text-red-500'}`} />
                <div>
                  <div className="font-medium">Autenticación</div>
                  <div className="text-sm text-muted-foreground">
                    {detailedHealth.auth ? 'Funcionando' : 'Error'}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 border rounded">
                <FileText className={`h-5 w-5 ${detailedHealth.questions ? 'text-green-500' : 'text-red-500'}`} />
                <div>
                  <div className="font-medium">Preguntas</div>
                  <div className="text-sm text-muted-foreground">
                    {detailedHealth.questions ? 'Disponible' : 'Error'}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Soluciones */}
      {healthStatus?.status === 'unreachable' && (
        <Card className="mb-6 border-red-200">
          <CardHeader>
            <CardTitle className="text-red-600">🚨 Problema de Conexión Detectado</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>El backend no está respondiendo.</strong> Esto puede deberse a:
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <h4 className="font-medium">Posibles Soluciones:</h4>
                <ol className="list-decimal list-inside space-y-1 text-sm">
                  <li>
                    <strong>Verificar que el backend esté ejecutándose:</strong>
                    <div className="ml-6 mt-1">
                      <code className="bg-muted px-2 py-1 rounded text-xs">
                        cd apps/backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
                      </code>
                    </div>
                  </li>
                  <li>
                    <strong>Verificar el puerto:</strong> Asegúrate de que el backend esté ejecutándose en el puerto 4000
                  </li>
                  <li>
                    <strong>Verificar firewall:</strong> Asegúrate de que el puerto 4000 no esté bloqueado
                  </li>
                  <li>
                    <strong>Verificar logs del backend:</strong> Revisa la consola donde ejecutaste el backend para ver errores
                  </li>
                </ol>
              </div>

              <Separator />

              <div className="space-y-2">
                <h4 className="font-medium">Comandos de Verificación:</h4>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm">1. Verificar si el puerto está en uso:</span>
                    <code className="bg-muted px-2 py-1 rounded text-xs">
                      netstat -an | findstr :4000
                    </code>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm">2. Probar conexión directa:</span>
                    <code className="bg-muted px-2 py-1 rounded text-xs">
                      curl http://localhost:4000/api/v1/health
                    </code>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Estado Exitoso */}
      {healthStatus?.status === 'healthy' && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            <strong>¡Excelente!</strong> El backend está funcionando correctamente. 
            Puedes continuar usando la aplicación normalmente.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
} 