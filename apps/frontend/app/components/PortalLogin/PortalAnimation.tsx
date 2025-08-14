'use client';

import React, { Suspense, useRef, useEffect, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import PortalFallback from './PortalFallback';
import { useAudioEngine } from './AudioEngine';

interface PortalAnimationProps {
  isTyping?: boolean;
  loginError?: boolean;
  loginSuccess?: boolean;
  onPortalReady?: () => void;
}

export default function PortalAnimation({ 
  isTyping = false, 
  loginError = false,
  loginSuccess = false,
  onPortalReady
}: PortalAnimationProps) {
  const isReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
  const [isLowBattery, setIsLowBattery] = useState(false);
  const [webGLSupported, setWebGLSupported] = useState(true);
  const { playSound, stopSound } = useAudioEngine();

  useEffect(() => {
    // Check WebGL support
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    setWebGLSupported(!!gl);

    // Check battery level
    if ('getBattery' in navigator) {
      (navigator as any).getBattery().then((battery: any) => {
        setIsLowBattery(battery.level < 0.2);
        battery.addEventListener('levelchange', () => {
          setIsLowBattery(battery.level < 0.2);
        });
      });
    }

    // Start portal ambient sound
    if (!isReducedMotion) {
      playSound('portal_hum', { loop: true, volume: 0.3 });
    }

    return () => {
      stopSound('portal_hum');
    };
  }, [isReducedMotion, playSound, stopSound]);

  // Handle interaction sounds
  useEffect(() => {
    if (isTyping && !isReducedMotion) {
      playSound('typing_pulse', { volume: 0.2 });
    }
    if (loginError && !isReducedMotion) {
      playSound('portal_reject', { volume: 0.4 });
      // Haptic feedback on error
      if ('vibrate' in navigator) {
        navigator.vibrate([100, 50, 100]);
      }
    }
    if (loginSuccess && !isReducedMotion) {
      playSound('portal_success', { volume: 0.5 });
      // Success haptic pattern
      if ('vibrate' in navigator) {
        navigator.vibrate([50, 100, 50]);
      }
    }
  }, [isTyping, loginError, loginSuccess, isReducedMotion, playSound]);

  // Fallback for no WebGL support
  if (!webGLSupported) {
    return <PortalFallback isTyping={isTyping} loginError={loginError} />;
  }

  const performanceMode = isLowBattery || isReducedMotion;

  return (
    <div 
      className="w-full h-64 md:h-96 relative overflow-hidden rounded-lg"
      aria-label="Portal de Invocación de Hunters - Animación 3D interactiva"
      role="img"
    >
      <Canvas 
        camera={{ position: [0, 0, 5], fov: 45 }}
        gl={{ antialias: !performanceMode, alpha: true }}
        dpr={performanceMode ? 1 : [1, 2]}
      >
        {/* Background stars - reduced in performance mode */}
        {!performanceMode && (
          <Stars 
            radius={50} 
            depth={30}
            count={isLowBattery ? 300 : 800} 
            factor={3} 
            saturation={0}
            fade 
            speed={isTyping ? 2 : 1}
          />
        )}
        
        {/* Lighting setup */}
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#8a2be2" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#4169e1" />
        
        <Suspense fallback={null}>
          <ThematicPortal 
            isTyping={isTyping} 
            loginError={loginError}
            loginSuccess={loginSuccess}
            performanceMode={performanceMode}
          />
          {!performanceMode && (
            <ReactiveParticles 
              isTyping={isTyping} 
              loginError={loginError}
              loginSuccess={loginSuccess}
            />
          )}
        </Suspense>
        
        {/* Orbit controls - disabled in reduced motion */}
        {!isReducedMotion && (
          <OrbitControls 
            enableZoom={false} 
            enablePan={false}
            enableRotate={!loginSuccess}
            minPolarAngle={Math.PI / 3}
            maxPolarAngle={Math.PI / 1.5}
          />
        )}
      </Canvas>
      
      {/* Loading indicator */}
      <div className="absolute inset-0 pointer-events-none">
        <div className={`
          absolute top-4 right-4 text-xs font-mono
          ${loginError ? 'text-red-400' : 'text-purple-400'}
          transition-all duration-300
        `}>
          {loginError ? 'ACCESO DENEGADO' : 'SISTEMA ACTIVO'}
        </div>
      </div>
    </div>
  );
}

function ThematicPortal({ isTyping, loginError, loginSuccess, performanceMode }: any) {
  const groupRef = useRef<THREE.Group>(null!);
  const innerRingRef = useRef<THREE.Mesh>(null!);
  const outerRingRef = useRef<THREE.Mesh>(null!);
  const portalPlaneRef = useRef<THREE.Mesh>(null!);
  const scaleRef = useRef(1);

  // Custom shader material for portal effect
  const portalMaterial = new THREE.ShaderMaterial({
    uniforms: {
      uTime: { value: 0 },
      uColorA: { value: new THREE.Color('#8a2be2') },
      uColorB: { value: new THREE.Color('#4169e1') },
      uError: { value: loginError ? 1.0 : 0.0 },
      uSuccess: { value: loginSuccess ? 1.0 : 0.0 }
    },
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform vec3 uColorA;
      uniform vec3 uColorB;
      uniform float uError;
      uniform float uSuccess;
      varying vec2 vUv;
      
      void main() {
        vec2 center = vec2(0.5);
        float dist = distance(vUv, center);
        float pulse = sin(uTime * 2.0 + dist * 10.0) * 0.5 + 0.5;
        
        vec3 color = mix(uColorA, uColorB, pulse);
        
        // Error state - red tint
        if (uError > 0.0) {
          color = mix(color, vec3(1.0, 0.2, 0.2), uError);
        }
        
        // Success state - golden glow
        if (uSuccess > 0.0) {
          color = mix(color, vec3(1.0, 0.843, 0.0), uSuccess * 0.5);
        }
        
        float alpha = 1.0 - smoothstep(0.3, 0.5, dist);
        gl_FragColor = vec4(color, alpha * 0.8);
      }
    `,
    transparent: true,
    side: THREE.DoubleSide
  });

  useFrame(({ clock }) => {
    if (!groupRef.current) return;
    
    const time = clock.getElapsedTime();
    portalMaterial.uniforms.uTime.value = time;
    
    // Rotation animations
    if (!performanceMode) {
      innerRingRef.current.rotation.z = time * (isTyping ? 0.5 : 0.3);
      outerRingRef.current.rotation.z = -time * (isTyping ? 0.4 : 0.2);
    }
    
    // Error shake effect
    if (loginError) {
      groupRef.current.position.x = Math.sin(time * 20) * 0.05;
      groupRef.current.position.y = Math.cos(time * 15) * 0.03;
    } else {
      groupRef.current.position.x = 0;
      groupRef.current.position.y = 0;
    }
    
    // Success expansion
    if (loginSuccess) {
      scaleRef.current = Math.min(scaleRef.current + 0.02, 3);
      groupRef.current.scale.setScalar(scaleRef.current);
      portalPlaneRef.current.material.opacity = Math.max(0, 1 - (scaleRef.current - 1) / 2);
    }
  });

  return (
    <group ref={groupRef}>
      {/* Portal plane */}
      <mesh ref={portalPlaneRef}>
        <planeGeometry args={[3, 3, 32, 32]} />
        <primitive object={portalMaterial} attach="material" />
      </mesh>
      
      {/* Inner ring with runes */}
      <mesh ref={innerRingRef} position={[0, 0, 0.1]}>
        <torusGeometry args={[1.5, 0.1, performanceMode ? 8 : 16, performanceMode ? 32 : 64]} />
        <meshStandardMaterial 
          color={loginError ? '#ff4444' : '#b784ff'} 
          emissive={loginError ? '#ff0000' : '#8a2be2'}
          emissiveIntensity={isTyping ? 1.5 : 1}
          metalness={0.7}
          roughness={0.3}
        />
      </mesh>
      
      {/* Outer ring */}
      <mesh ref={outerRingRef} position={[0, 0, 0.05]}>
        <torusGeometry args={[2, 0.08, performanceMode ? 8 : 16, performanceMode ? 32 : 64]} />
        <meshStandardMaterial 
          color={loginError ? '#ff6666' : '#4169e1'} 
          emissive={loginError ? '#ff3333' : '#4169e1'}
          emissiveIntensity={isTyping ? 1.2 : 0.8}
          metalness={0.6}
          roughness={0.4}
        />
      </mesh>
    </group>
  );
}

function ReactiveParticles({ isTyping, loginError, loginSuccess }: any) {
  const pointsRef = useRef<THREE.Points>(null!);
  const particlesCount = 500;
  const positions = useRef(new Float32Array(particlesCount * 3));
  const velocities = useRef(new Float32Array(particlesCount * 3));
  const colors = useRef(new Float32Array(particlesCount * 3));

  // Initialize particle positions and velocities
  useEffect(() => {
    for (let i = 0; i < particlesCount; i++) {
      const angle = (i / particlesCount) * Math.PI * 2;
      const radius = 2 + Math.random() * 2;
      
      positions.current[i * 3] = Math.cos(angle) * radius;
      positions.current[i * 3 + 1] = Math.sin(angle) * radius;
      positions.current[i * 3 + 2] = (Math.random() - 0.5) * 2;
      
      velocities.current[i * 3] = (Math.random() - 0.5) * 0.02;
      velocities.current[i * 3 + 1] = (Math.random() - 0.5) * 0.02;
      velocities.current[i * 3 + 2] = (Math.random() - 0.5) * 0.02;
      
      // Initial color
      colors.current[i * 3] = 0.54; // R
      colors.current[i * 3 + 1] = 0.17; // G
      colors.current[i * 3 + 2] = 0.89; // B
    }
  }, [particlesCount]);

  useFrame(() => {
    if (!pointsRef.current) return;
    
    const positionsArray = pointsRef.current.geometry.attributes.position.array as Float32Array;
    const colorsArray = pointsRef.current.geometry.attributes.color.array as Float32Array;
    
    for (let i = 0; i < particlesCount; i++) {
      // Update positions
      const speedMultiplier = isTyping ? 3 : loginSuccess ? 5 : 1;
      positionsArray[i * 3] += velocities.current[i * 3] * speedMultiplier;
      positionsArray[i * 3 + 1] += velocities.current[i * 3 + 1] * speedMultiplier;
      positionsArray[i * 3 + 2] += velocities.current[i * 3 + 2] * speedMultiplier;
      
      // Boundary check and bounce
      const radius = Math.sqrt(
        positionsArray[i * 3] ** 2 + 
        positionsArray[i * 3 + 1] ** 2
      );
      
      if (radius > 5 || radius < 0.5) {
        velocities.current[i * 3] *= -1;
        velocities.current[i * 3 + 1] *= -1;
      }
      
      // Update colors based on state
      if (loginError) {
        colorsArray[i * 3] = 1; // Red
        colorsArray[i * 3 + 1] = 0.2;
        colorsArray[i * 3 + 2] = 0.2;
      } else if (loginSuccess) {
        colorsArray[i * 3] = 1; // Gold
        colorsArray[i * 3 + 1] = 0.84;
        colorsArray[i * 3 + 2] = 0;
      } else if (isTyping) {
        colorsArray[i * 3] = 0.64; // Brighter purple
        colorsArray[i * 3 + 1] = 0.27;
        colorsArray[i * 3 + 2] = 0.99;
      } else {
        colorsArray[i * 3] = 0.54; // Default purple
        colorsArray[i * 3 + 1] = 0.17;
        colorsArray[i * 3 + 2] = 0.89;
      }
    }
    
    pointsRef.current.geometry.attributes.position.needsUpdate = true;
    pointsRef.current.geometry.attributes.color.needsUpdate = true;
  });

  return (
    <Points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute 
          attach="attributes-position" 
          count={particlesCount}
          array={positions.current}
          itemSize={3}
        />
        <bufferAttribute 
          attach="attributes-color" 
          count={particlesCount}
          array={colors.current}
          itemSize={3}
        />
      </bufferGeometry>
      <PointMaterial
        size={0.05}
        sizeAttenuation
        transparent
        opacity={0.8}
        vertexColors
        blending={THREE.AdditiveBlending}
      />
    </Points>
  );
}