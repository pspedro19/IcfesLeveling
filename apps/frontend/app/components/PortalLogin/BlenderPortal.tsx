'use client';

import React, { Suspense, useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useGLTF, OrbitControls, Environment, Html } from '@react-three/drei';
import * as THREE from 'three';
import { useAudioEngine } from './AudioEngine';

interface BlenderPortalProps {
  isTyping?: boolean;
  loginError?: boolean;
  loginSuccess?: boolean;
  onPortalReady?: () => void;
  portalVersion?: 'portal' | 'portal2'; // Elegir entre los dos portales
}

function PortalModel({ 
  isTyping, 
  loginError, 
  loginSuccess, 
  portalVersion = 'portal2' // Por defecto usar portal2 (más liviano)
}: any) {
  const groupRef = useRef<THREE.Group>(null!);
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Cargar el modelo del portal
  const modelPath = `/models/${portalVersion}.glb`;
  
  try {
    const { scene, animations } = useGLTF(modelPath);
    
    useEffect(() => {
      if (scene) {
        setIsLoaded(true);
        console.log(`✅ Portal ${portalVersion} loaded successfully!`, {
          children: scene.children.length,
          animations: animations?.length || 0
        });
      }
    }, [scene, animations, portalVersion]);

    useFrame(({ clock }) => {
      if (!groupRef.current || !isLoaded) return;
      
      const time = clock.getElapsedTime();
      
      // Animaciones base del portal
      if (loginSuccess) {
        // Animación de éxito: crecimiento y rotación rápida
        groupRef.current.rotation.y = time * 2;
        const scale = 1 + Math.sin(time * 4) * 0.2;
        groupRef.current.scale.setScalar(scale);
        groupRef.current.position.y = Math.sin(time * 3) * 0.3;
      } else if (loginError) {
        // Animación de error: temblor
        groupRef.current.position.x = Math.sin(time * 15) * 0.1;
        groupRef.current.position.z = Math.cos(time * 15) * 0.1;
        groupRef.current.rotation.y = time * 0.5 + Math.sin(time * 10) * 0.1;
      } else if (isTyping) {
        // Animación durante escritura: rotación más rápida
        groupRef.current.rotation.y = time * 1;
        groupRef.current.position.y = Math.sin(time * 2) * 0.1;
      } else {
        // Animación idle: rotación suave
        groupRef.current.rotation.y = time * 0.3;
        groupRef.current.position.y = Math.sin(time * 1.5) * 0.05;
      }
    });

    return (
      <group ref={groupRef}>
        <primitive object={scene} />
      </group>
    );

  } catch (err: any) {
    console.error(`❌ Error loading portal ${portalVersion}:`, err);
    setError(err.message);
    
    // Fallback: Portal simple generado proceduralmente
    return <FallbackPortal ref={groupRef} />;
  }
}

const FallbackPortal = React.forwardRef<THREE.Group>((props, ref) => {
  useFrame(({ clock }) => {
    if (ref && 'current' in ref && ref.current) {
      ref.current.rotation.y = clock.getElapsedTime() * 0.5;
    }
  });

  return (
    <group ref={ref}>
      {/* Portal Ring Exterior */}
      <mesh>
        <torusGeometry args={[2, 0.1, 16, 100]} />
        <meshStandardMaterial 
          color="#8a2be2" 
          emissive="#4a148c" 
          emissiveIntensity={0.5}
          roughness={0.1}
          metalness={0.8}
        />
      </mesh>
      
      {/* Portal Ring Interior */}
      <mesh>
        <torusGeometry args={[1.5, 0.05, 16, 100]} />
        <meshStandardMaterial 
          color="#ff6b6b" 
          emissive="#ff4757" 
          emissiveIntensity={0.7}
          roughness={0.1}
          metalness={0.8}
        />
      </mesh>
      
      {/* Portal Core */}
      <mesh>
        <sphereGeometry args={[0.3, 32, 32]} />
        <meshStandardMaterial 
          color="#ffffff" 
          emissive="#ffffff" 
          emissiveIntensity={1}
          transparent
          opacity={0.8}
        />
      </mesh>
    </group>
  );
});

FallbackPortal.displayName = 'FallbackPortal';

function LoadingIndicator() {
  return (
    <Html center>
      <div className="text-white text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400 mx-auto mb-2"></div>
        <div className="text-sm opacity-80">Invocando Portal...</div>
      </div>
    </Html>
  );
}

function PortalParticles({ active }: { active: boolean }) {
  const particlesRef = useRef<THREE.Points>(null!);
  
  const particleCount = active ? 1000 : 500;
  const positions = React.useMemo(() => {
    const pos = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 8;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 8;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 8;
    }
    return pos;
  }, [particleCount]);

  useFrame(({ clock }) => {
    if (!particlesRef.current) return;
    
    const time = clock.getElapsedTime();
    particlesRef.current.rotation.y = time * 0.1;
    
    // Efecto de remolino hacia el portal
    const positions = particlesRef.current.geometry.attributes.position.array as Float32Array;
    
    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      const x = positions[i3];
      const z = positions[i3 + 2];
      const distance = Math.sqrt(x * x + z * z);
      
      // Efecto de rotación espiral
      if (distance > 0.1) {
        const angle = Math.atan2(z, x) + time * 0.5;
        const newDistance = distance - 0.01;
        
        if (newDistance > 0.5) {
          positions[i3] = Math.cos(angle) * newDistance;
          positions[i3 + 2] = Math.sin(angle) * newDistance;
        } else {
          // Resetear partícula
          positions[i3] = (Math.random() - 0.5) * 8;
          positions[i3 + 1] = (Math.random() - 0.5) * 8;
          positions[i3 + 2] = (Math.random() - 0.5) * 8;
        }
      }
    }
    
    particlesRef.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particleCount}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.02}
        sizeAttenuation={true}
        color="#8a2be2"
        transparent
        opacity={active ? 0.8 : 0.4}
      />
    </points>
  );
}

export default function BlenderPortal({
  isTyping = false,
  loginError = false,
  loginSuccess = false,
  onPortalReady,
  portalVersion = 'portal2' // Usar portal2 por defecto (más liviano)
}: BlenderPortalProps) {
  const { playSound } = useAudioEngine();
  const [isReady, setIsReady] = useState(false);

  // Efectos de sonido basados en estado
  useEffect(() => {
    if (loginSuccess) {
      playSound('portal_success');
    } else if (loginError) {
      playSound('portal_reject');
    } else if (isTyping) {
      playSound('typing_pulse');
    }
  }, [loginSuccess, loginError, isTyping, playSound]);

  useEffect(() => {
    if (isReady && onPortalReady) {
      onPortalReady();
    }
  }, [isReady, onPortalReady]);

  // Detectar si es un dispositivo móvil para optimizar performance
  const isMobile = typeof window !== 'undefined' && 
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

  return (
    <div 
      className="w-full h-64 md:h-96 relative overflow-hidden rounded-lg bg-gradient-to-br from-purple-900 via-blue-900 to-black"
      aria-label="Portal de Invocación de Hunters - Modelo 3D de Blender"
      role="img"
    >
      <Canvas 
        camera={{ position: [0, 0, 6], fov: 45 }}
        gl={{ 
          antialias: !isMobile, 
          alpha: true,
          powerPreference: "high-performance"
        }}
        dpr={isMobile ? 1 : [1, 2]}
      >
        {/* Iluminación dramática */}
        <ambientLight intensity={0.3} />
        <directionalLight 
          position={[10, 10, 5]} 
          intensity={1.2} 
          color="#ffffff"
          castShadow
        />
        <pointLight 
          position={[0, 0, 8]} 
          intensity={1} 
          color="#8a2be2"
          distance={20}
        />
        <pointLight 
          position={[-5, -5, -5]} 
          intensity={0.5} 
          color="#ff6b6b"
          distance={15}
        />
        
        {/* Environment para reflejos realistas */}
        <Environment preset="sunset" />
        
        {/* Modelo del Portal */}
        <Suspense fallback={<LoadingIndicator />}>
          <PortalModel 
            isTyping={isTyping}
            loginError={loginError}
            loginSuccess={loginSuccess}
            portalVersion={portalVersion}
          />
        </Suspense>
        
        {/* Partículas solo en desktop para mejor performance */}
        {!isMobile && (
          <PortalParticles active={isTyping || loginSuccess} />
        )}
        
        {/* Controles de cámara */}
        <OrbitControls 
          enableZoom={false} 
          enablePan={false}
          enableRotate={!loginSuccess}
          autoRotate={!isTyping && !loginError && !loginSuccess}
          autoRotateSpeed={0.5}
          minPolarAngle={Math.PI / 4}
          maxPolarAngle={Math.PI / 1.3}
        />
      </Canvas>
      
      {/* Indicador de estado */}
      <div className="absolute top-4 right-4">
        <div className={`w-3 h-3 rounded-full ${
          loginSuccess ? 'bg-green-400 animate-pulse' :
          loginError ? 'bg-red-400 animate-bounce' :
          isTyping ? 'bg-blue-400 animate-pulse' :
          'bg-purple-400'
        }`} />
      </div>
      
      {/* Indicador de versión del portal */}
      <div className="absolute bottom-4 left-4 text-white/50 text-xs">
        Portal {portalVersion === 'portal' ? 'HD' : 'Optimizado'}
      </div>
    </div>
  );
}

// Pre-cargar ambos modelos
if (typeof window !== 'undefined') {
  // Pre-cargar portal2 (más liviano) inmediatamente
  useGLTF.preload('/models/portal2.glb');
  
  // Pre-cargar portal1 después de un delay
  setTimeout(() => {
    useGLTF.preload('/models/portal.glb');
  }, 2000);
}