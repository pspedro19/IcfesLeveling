'use client';

import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars, useGLTF } from '@react-three/drei';

/**
 * Simple 3D portal animation for the login screen.
 * It renders a glowing torus with rotating particles for a quick wow-effect while we iterate.
 * Later we can swap the torus for a custom GLTF portal asset.
 */
export default function PortalAnimation() {
  return (
    <div className="w-full h-64 md:h-96">
      <Canvas camera={{ position: [0, 0, 5] }}>
        {/* Background stars */}
        <Stars radius={100} depth={50} count={2000} factor={4} saturation={0} fade speed={1} />

        {/* Ambient & point lights */}
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1.2} />

        {/* Suspense wrapper for potential GLTF loading */}
        <Suspense fallback={null}>
          <RotatingPortal />
        </Suspense>

        {/* User can orbit the portal for now */}
        <OrbitControls enableZoom={false} />
      </Canvas>
    </div>
  );
}

function RotatingPortal() {
  // Simple torus geometry that rotates and changes color over time.
  const meshRef = React.useRef<THREE.Mesh>(null!);

  // Animation loop
  React.useFrame(({ clock }) => {
    const mesh = meshRef.current;
    if (!mesh) return;
    mesh.rotation.x = clock.getElapsedTime() * 0.3;
    mesh.rotation.y = clock.getElapsedTime() * 0.5;
    // Pulse the emissive intensity
    const emissiveIntensity = (Math.sin(clock.getElapsedTime() * 2) + 1.5) / 2;
    (mesh.material as THREE.MeshStandardMaterial).emissiveIntensity = emissiveIntensity;
  });

  return (
    <mesh ref={meshRef}>
      <torusGeometry args={[1.2, 0.4, 32, 64]} />
      <meshStandardMaterial color="#7a3cff" emissive="#b784ff" emissiveIntensity={0.8} />
    </mesh>
  );
}
