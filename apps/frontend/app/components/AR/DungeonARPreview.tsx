'use client';

import React, { useState, useRef, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Box, Text, Environment, PerspectiveCamera } from '@react-three/drei';
import { ARButton, createXRStore } from '@react-three/xr';
import { motion } from 'framer-motion';
import { 
  Smartphone,
  Maximize,
  X,
  Loader2,
  AlertCircle,
  Camera,
  Move,
  RotateCw
} from 'lucide-react';

interface DungeonARPreviewProps {
  dungeonData: {
    name: string;
    difficulty: number;
    floors: number;
    theme: string;
    monsters: string[];
  };
  onClose?: () => void;
}

// 3D Dungeon Component
function Dungeon3D({ dungeonData }: { dungeonData: any }) {
  const floorColors = ['#1a1a2e', '#16213e', '#0f3460', '#53354a'];
  
  return (
    <group>
      {/* Dungeon Floors */}
      {Array.from({ length: dungeonData.floors }).map((_, index) => (
        <Box
          key={index}
          args={[3 - index * 0.3, 0.2, 3 - index * 0.3]}
          position={[0, index * 0.5, 0]}
        >
          <meshStandardMaterial 
            color={floorColors[index % floorColors.length]}
            metalness={0.5}
            roughness={0.5}
          />
        </Box>
      ))}
      
      {/* Dungeon Name */}
      <Text
        position={[0, dungeonData.floors * 0.5 + 0.5, 0]}
        fontSize={0.3}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
      >
        {dungeonData.name}
      </Text>
      
      {/* Difficulty Indicator */}
      <Text
        position={[0, -0.5, 1.5]}
        fontSize={0.2}
        color="#ff6b6b"
        anchorX="center"
        anchorY="middle"
      >
        {`Dificultad: ${dungeonData.difficulty}/10`}
      </Text>
      
      {/* Floating Crystals */}
      {[...Array(3)].map((_, i) => (
        <mesh
          key={i}
          position={[
            Math.sin(i * Math.PI * 2 / 3) * 2,
            1 + Math.sin(Date.now() * 0.001 + i) * 0.2,
            Math.cos(i * Math.PI * 2 / 3) * 2
          ]}
        >
          <octahedronGeometry args={[0.2, 0]} />
          <meshStandardMaterial
            color={i === 0 ? '#ff6b6b' : i === 1 ? '#4ecdc4' : '#ffe66d'}
            emissive={i === 0 ? '#ff6b6b' : i === 1 ? '#4ecdc4' : '#ffe66d'}
            emissiveIntensity={0.5}
          />
        </mesh>
      ))}
    </group>
  );
}

export default function DungeonARPreview({ dungeonData, onClose }: DungeonARPreviewProps) {
  const store = createXRStore();
  const [isARSupported, setIsARSupported] = useState(false);
  const [isARActive, setIsARActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Check AR support
  React.useEffect(() => {
    if ('xr' in navigator && navigator.xr) {
      navigator.xr.isSessionSupported('immersive-ar').then((supported) => {
        setIsARSupported(supported);
        if (!supported) {
          setError('Tu dispositivo no soporta WebAR');
        }
      }).catch(() => {
        setError('Error al verificar soporte AR');
      });
    } else {
      setError('WebXR no está disponible en este navegador');
    }
  }, []);
  
  return (
    <motion.div
      className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="relative w-full h-full max-w-6xl max-h-[90vh] mx-auto p-4">
        {/* Header */}
        <div className="absolute top-4 left-4 right-4 z-10 flex items-center 
          justify-between">
          <div className="bg-gray-900/80 rounded-lg px-4 py-2 backdrop-blur-sm">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Camera className="w-5 h-5 text-purple-400" />
              Preview AR: {dungeonData.name}
            </h2>
          </div>
          
          <button
            onClick={onClose}
            className="p-2 bg-gray-900/80 hover:bg-gray-800 rounded-lg 
              backdrop-blur-sm transition-all"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>
        
        {/* AR Canvas */}
        <div className="relative w-full h-full bg-gray-900 rounded-lg overflow-hidden">
          {error ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
                <p className="text-red-400 mb-2">{error}</p>
                <p className="text-gray-400 text-sm">
                  Prueba la vista 3D estándar en su lugar
                </p>
              </div>
            </div>
          ) : (
            <>
              <Canvas
                camera={{ position: [0, 2, 5], fov: 50 }}
                style={{ background: '#0a0a0a' }}
              >
                <>
                  <Suspense fallback={null}>
                    <PerspectiveCamera makeDefault position={[0, 2, 5]} />
                    <OrbitControls 
                      enablePan={false}
                      maxPolarAngle={Math.PI / 2}
                      minDistance={3}
                      maxDistance={10}
                    />
                    
                    {/* Lighting */}
                    <ambientLight intensity={0.5} />
                    <directionalLight position={[10, 10, 5]} intensity={1} />
                    <pointLight position={[0, 5, 0]} intensity={0.5} color="#ff6b6b" />
                    
                    {/* Environment */}
                    <Environment preset="night" />
                    
                    {/* Dungeon Model */}
                    <Dungeon3D dungeonData={dungeonData} />
                    
                    {/* Ground Grid */}
                    <gridHelper args={[10, 10, '#444444', '#222222']} />
                  </Suspense>
                </>
              </Canvas>
              
              {/* AR Button */}
              {isARSupported && (
                <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2">
                  <ARButton
                    store={store}
                    style={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white',
                      padding: '12px 24px',
                      borderRadius: '8px',
                      border: 'none',
                      fontSize: '16px',
                      fontWeight: 'bold',
                      cursor: 'pointer',
                      boxShadow: '0 4px 15px rgba(102, 126, 234, 0.5)'
                    }}
                  />
                </div>
              )}
            </>
          )}
        </div>
        
        {/* Instructions */}
        <div className="absolute bottom-4 right-4 bg-gray-900/80 rounded-lg p-4 
          backdrop-blur-sm max-w-xs">
          <h3 className="font-semibold text-white mb-2">Controles</h3>
          <div className="space-y-2 text-sm text-gray-300">
            {isARActive ? (
              <>
                <div className="flex items-center gap-2">
                  <Move className="w-4 h-4 text-purple-400" />
                  <span>Mueve tu dispositivo para explorar</span>
                </div>
                <div className="flex items-center gap-2">
                  <Smartphone className="w-4 h-4 text-purple-400" />
                  <span>Toca la pantalla para colocar</span>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center gap-2">
                  <RotateCw className="w-4 h-4 text-purple-400" />
                  <span>Arrastra para rotar</span>
                </div>
                <div className="flex items-center gap-2">
                  <Maximize className="w-4 h-4 text-purple-400" />
                  <span>Pellizca para zoom</span>
                </div>
              </>
            )}
          </div>
        </div>
        
        {/* Dungeon Info */}
        <div className="absolute top-20 left-4 bg-gray-900/80 rounded-lg p-4 
          backdrop-blur-sm max-w-xs">
          <h3 className="font-semibold text-white mb-2">Información</h3>
          <div className="space-y-1 text-sm text-gray-300">
            <p>Tema: <span className="text-purple-400">{dungeonData.theme}</span></p>
            <p>Pisos: <span className="text-blue-400">{dungeonData.floors}</span></p>
            <p>Monstruos: <span className="text-red-400">{dungeonData.monsters.length}</span></p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}