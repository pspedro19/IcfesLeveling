'use client';

import React, { Suspense, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useGLTF, OrbitControls, Environment, Html, Points } from '@react-three/drei'; // Añadido Points para partículas
import { PointsMaterial } from 'three';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  CheckCircle, 
  XCircle, 
  RotateCcw, 
  Eye, 
  Zap,
  FileText,
  Download
} from 'lucide-react';

// Añadido para sonido épico (asumir asset en /sounds)
const portalSound = typeof Audio !== 'undefined' ? new Audio('/sounds/portal-hum.mp3') : null;

function PortalModel({ portalVersion = 'portal2' }: { portalVersion: string }) {
  const groupRef = useRef<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  try {
    // Intentar cargar el modelo del portal
    const { scene, animations } = useGLTF(`/models/${portalVersion}.glb`);
    
    React.useEffect(() => {
      if (scene) {
        setLoaded(true);
        console.log('✅ Portal loaded successfully!', {
          scene,
          animations: animations?.length || 0,
          children: scene.children.length
        });
        // Reproducir sonido épico al cargar
        portalSound?.play();
      }
    }, [scene, animations]);

    useFrame(({ clock }) => {
      if (groupRef.current && loaded) {
        // Rotación suave del portal
        groupRef.current.rotation.y = clock.getElapsedTime() * 0.3;
        // Efecto de levitación
        groupRef.current.position.y = Math.sin(clock.getElapsedTime() * 2) * 0.1;
      }
    });

    return (
      <group ref={groupRef}>
        <primitive object={scene} scale={[1, 1, 1]} />
        {/* Añadido: Partículas místicas para inmersión */}
        <Points positions={new Float32Array(1000).map(() => Math.random() * 2 - 1)} scale={2}>
          <PointsMaterial color="#8a2be2" size={0.02} transparent opacity={0.8} />
        </Points>
      </group>
    );

  } catch (err: any) {
    console.error('❌ Error loading portal:', err);
    setError(err.message || 'Error desconocido');
    
    // Mostrar modelo de fallback (torus) con mensaje épico
    return (
      <mesh ref={groupRef}>
        <torusGeometry args={[1.2, 0.4, 16, 32]} />
        <meshStandardMaterial 
          color="#8a2be2" 
          emissive="#4a148c" 
          emissiveIntensity={0.3}
          roughness={0.3}
          metalness={0.7}
        />
      </mesh>
    );
  }
}

function LoadingFallback() {
  return (
    <Html center>
      <div className="text-white text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
        <div>Cargando Portal Místico...</div> {/* Actualizado a épico */}
      </div>
    </Html>
  );
}

export default function TestPortalPage() {
  const [showStats, setShowStats] = useState(false);
  const [modelInfo, setModelInfo] = useState<any>(null);
  const [selectedPortal, setSelectedPortal] = useState<'portal' | 'portal2'>('portal2');
  const [hunterRank, setHunterRank] = useState('E'); // Añadido: Gamificación con rango

  React.useEffect(() => {
    // Intentar obtener información del modelo
    fetch('/models/portal.glb')
      .then(response => {
        if (response.ok) {
          return response.blob();
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      })
      .then(blob => {
        setModelInfo({
          exists: true,
          size: blob.size,
          sizeFormatted: (blob.size / (1024 * 1024)).toFixed(2) + ' MB',
          type: blob.type || 'application/octet-stream'
        });
        // Gamificación: Subir rango si existe
        setHunterRank('D');
      })
      .catch(error => {
        console.log('❌ Portal file not found:', error.message);
        setModelInfo({
          exists: false,
          error: error.message
        });
      });
  }, []);

  return (
    <div className="container mx-auto px-4 py-8 bg-gradient-to-br from-black to-purple-900"> {/* Fondo cósmico épico */}
      {/* Header con lore */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gold-500 mb-2 font-cinzel"> {/* Font épica */}
          🌀 Prueba del Portal Místico del Hunter
        </h1>
        <p className="text-gray-300">
          En el Reino de Hunters, prueba tu entrada a las Mazmorras del Conocimiento para conquistar el ICFES.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Visualización del Portal con glass morphism */}
        <Card className="bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_10px_#8a2be2]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gold-500">
              <Eye className="w-5 h-5" />
              Vista del Portal Épico
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="aspect-square bg-gradient-to-br from-purple-900 via-blue-900 to-black rounded-lg overflow-hidden">
              <Canvas 
                camera={{ position: [0, 0, 5], fov: 45 }}
                gl={{ antialias: true, alpha: true }}
              >
                {/* Iluminación mejorada para místico */}
                <ambientLight intensity={0.4} />
                <directionalLight position={[10, 10, 5]} intensity={1} color="#ffd700" /> {/* Gold light */}
                <pointLight position={[-10, -10, -10]} intensity={0.5} color="#8a2be2" />
                
                {/* Environment para reflejos */}
                <Environment preset="sunset" />
                
                {/* Modelo del Portal */}
                <Suspense fallback={<LoadingFallback />}>
                  <PortalModel portalVersion={selectedPortal} />
                </Suspense>
                
                {/* Controles de cámara */}
                <OrbitControls 
                  enableZoom={true} 
                  enablePan={true}
                  autoRotate={false}
                  minDistance={2}
                  maxDistance={10}
                />
              </Canvas>
            </div>
            
            <div className="flex gap-2 mt-4 flex-wrap">
              <Button 
                variant="outline" 
                size="sm"
                className="shadow-[0_0_5px_#ffd700]" // Glow gold
                onClick={() => window.location.reload()}
              >
                <RotateCcw className="w-4 h-4 mr-1" />
                Recargar Portal
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                className="shadow-[0_0_5px_#ffd700]"
                onClick={() => setShowStats(!showStats)}
              >
                <FileText className="w-4 h-4 mr-1" />
                {showStats ? 'Ocultar' : 'Mostrar'} Runas Técnicas
              </Button>
              <Button 
                variant={selectedPortal === 'portal2' ? 'default' : 'outline'}
                size="sm"
                className="shadow-[0_0_5px_#ffd700]"
                onClick={() => setSelectedPortal('portal2')}
              >
                Portal Optimizado (8MB)
              </Button>
              <Button 
                variant={selectedPortal === 'portal' ? 'default' : 'outline'}
                size="sm"
                className="shadow-[0_0_5px_#ffd700]"
                onClick={() => setSelectedPortal('portal')}
              >
                Portal Legendario (24MB)
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Estado y Diagnóstico con glass */}
        <div className="space-y-6">
          {/* Estado del archivo */}
          <Card className="bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_10px_#8a2be2]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-gold-500">
                <CheckCircle className="w-5 h-5" />
                Estado del Portal Místico
              </CardTitle>
            </CardHeader>
            <CardContent>
              {modelInfo === null ? (
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500"></div>
                  <span>Verificando runas del portal...</span>
                </div>
              ) : modelInfo.exists ? (
                <Alert className="bg-green-900/50">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <AlertTitle>¡Portal Desbloqueado! Rango {hunterRank} Alcanzado</AlertTitle> {/* Gamificación */}
                  <AlertDescription>
                    <div className="mt-2 space-y-1 text-gray-300">
                      <div>📁 Runa: <code>/models/portal.glb</code></div>
                      <div>📊 Poder: <strong>{modelInfo.sizeFormatted}</strong></div>
                      <div>🎭 Tipo: <code>{modelInfo.type}</code></div>
                    </div>
                  </AlertDescription>
                </Alert>
              ) : (
                <Alert variant="destructive" className="bg-red-900/50">
                  <XCircle className="h-4 w-4" />
                  <AlertTitle>Portal Corrompido por Monstruos</AlertTitle> {/* Mensaje épico */}
                  <AlertDescription>
                    <div className="mt-2">
                      <p>La runa <code>/models/portal.glb</code> ha sido devorada.</p>
                      <p className="mt-2 text-sm">Maldición: {modelInfo.error}</p>
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Instrucciones con lore */}
          <Card className="bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_10px_#8a2be2]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-gold-500">
                <Download className="w-5 h-5" />
                Cómo Invocar Tu Portal
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-gray-800/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2 text-gold-500">1. Exportar desde el Reino de Blender:</h4>
                <ul className="text-sm space-y-1 text-gray-300">
                  <li>• File → Export → glTF 2.0</li>
                  <li>• Formato: GLB (Binary)</li>
                  <li>• Nombre: "portal.glb"</li>
                </ul>
              </div>
              
              <div className="bg-gray-800/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2 text-gold-500">2. Colocar en el Gremio:</h4>
                <code className="text-sm bg-black p-2 rounded block text-purple-300">
                  apps/frontend/public/models/portal.glb
                </code>
              </div>
              
              <div className="bg-gray-800/50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2 text-gold-500">3. Invocar de Nuevo</h4>
                <p className="text-sm text-gray-300">
                  Una vez invocado, recarga para entrar en las mazmorras.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Estadísticas técnicas */}
          {showStats && (
            <Card className="bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_10px_#8a2be2]">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-gold-500">
                  <Zap className="w-5 h-5" />
                  Runas Técnicas Épicas
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-gray-300">
                  <div className="flex justify-between">
                    <span>WebGL:</span>
                    <span className="text-green-600">✓ Invocado</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Three.js:</span>
                    <span className="text-green-600">✓ Cargado</span>
                  </div>
                  <div className="flex justify-between">
                    <span>useGLTF:</span>
                    <span className="text-green-600">✓ Disponible</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Runa Esperada:</span>
                    <span><code>/models/portal.glb</code></span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Código de ejemplo con épico */}
      {modelInfo?.exists && (
        <Card className="mt-6 bg-black/30 backdrop-blur-md border-purple-500 shadow-[0_0_10px_#8a2be2]">
          <CardHeader>
            <CardTitle className="text-gold-500">✅ ¡Tu Portal Está Listo para la Conquista!</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-gray-300">
              Una vez que veas tu portal invocando gloria, intégralo en el gremio principal con este hechizo:
            </p>
            <pre className="bg-gray-800 p-4 rounded-lg text-sm overflow-x-auto text-purple-300">
{`// En LoginPortal.tsx, reemplaza:
import PortalAnimation from './PortalAnimation';

// Por:
import BlenderPortal from './BlenderPortal';

// Y usa:
<BlenderPortal 
  isTyping={isTyping}
  loginError={loginError}
  loginSuccess={loginSuccess}
/>`}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Pre-cargar el modelo si existe
if (typeof window !== 'undefined') {
  import('@react-three/drei').then(({ useGLTF }) => {
    try {
      useGLTF.preload('/models/portal.glb');
    } catch (e) {
      console.log('Portal preload skipped (file may not exist yet)');
    }
  });
}