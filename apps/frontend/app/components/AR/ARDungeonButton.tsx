'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Smartphone,
  View,
  AlertCircle,
  CheckCircle,
  Loader2,
  Camera
} from 'lucide-react';
import { useARSupport, requestARPermissions, isMobileDevice } from '@/hooks/useARSupport';
import DungeonARPreview from './DungeonARPreview';

interface ARDungeonButtonProps {
  dungeonData: {
    name: string;
    difficulty: number;
    floors: number;
    theme: string;
    monsters: string[];
  };
  className?: string;
}

export default function ARDungeonButton({ dungeonData, className = '' }: ARDungeonButtonProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [showCapabilityModal, setShowCapabilityModal] = useState(false);
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const arSupport = useARSupport();
  
  const handleARClick = async () => {
    setPermissionError(null);
    
    // If AR is supported, check permissions
    if (arSupport.isSupported && isMobileDevice()) {
      const hasPermissions = await requestARPermissions();
      if (!hasPermissions) {
        setPermissionError('Necesitamos acceso a la cámara y sensores para AR');
        return;
      }
    }
    
    // Show preview or capability modal
    if (arSupport.isSupported || !isMobileDevice()) {
      setShowPreview(true);
    } else {
      setShowCapabilityModal(true);
    }
  };
  
  const getButtonIcon = () => {
    if (arSupport.isChecking) {
      return <Loader2 className="w-5 h-5 animate-spin" />;
    }
    
    if (arSupport.isSupported) {
      return <Camera className="w-5 h-5" />;
    }
    
    return <View className="w-5 h-5" />;
  };
  
  const getButtonText = () => {
    if (arSupport.isChecking) {
      return 'Verificando...';
    }
    
    if (arSupport.isSupported && isMobileDevice()) {
      return 'Ver en AR';
    }
    
    return 'Vista 3D';
  };
  
  return (
    <>
      <motion.button
        onClick={handleARClick}
        disabled={arSupport.isChecking}
        className={`
          relative overflow-hidden group
          px-6 py-3 rounded-lg font-semibold
          bg-gradient-to-r from-purple-600 to-blue-600
          hover:from-purple-700 hover:to-blue-700
          text-white shadow-lg
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-all duration-300
          ${className}
        `}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <div className="flex items-center gap-2">
          {getButtonIcon()}
          <span>{getButtonText()}</span>
        </div>
        
        {/* Shimmer effect */}
        <div className="absolute inset-0 -top-[2px] -bottom-[2px] 
          bg-gradient-to-r from-transparent via-white/20 to-transparent 
          -skew-x-12 translate-x-[-200%] group-hover:translate-x-[200%] 
          transition-transform duration-1000" />
      </motion.button>
      
      {/* Permission Error */}
      {permissionError && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-red-400 text-sm mt-2"
        >
          {permissionError}
        </motion.p>
      )}
      
      {/* AR Preview Modal */}
      <AnimatePresence>
        {showPreview && (
          <DungeonARPreview
            dungeonData={dungeonData}
            onClose={() => setShowPreview(false)}
          />
        )}
      </AnimatePresence>
      
      {/* Capability Modal */}
      <AnimatePresence>
        {showCapabilityModal && (
          <motion.div
            className="fixed inset-0 bg-black/80 z-50 flex items-center 
              justify-center p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowCapabilityModal(false)}
          >
            <motion.div
              className="bg-gray-900 rounded-lg p-6 max-w-md w-full"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-yellow-600/20 rounded-lg">
                  <AlertCircle className="w-6 h-6 text-yellow-400" />
                </div>
                <h3 className="text-xl font-semibold text-white">
                  Compatibilidad AR
                </h3>
              </div>
              
              <p className="text-gray-300 mb-6">
                Tu dispositivo no es totalmente compatible con WebAR. 
                Aquí está el estado de las capacidades necesarias:
              </p>
              
              <div className="space-y-3 mb-6">
                <CapabilityItem
                  name="WebXR API"
                  supported={arSupport.capabilities.webXR}
                />
                <CapabilityItem
                  name="AR Inmersivo"
                  supported={arSupport.capabilities.immersiveAR}
                />
                <CapabilityItem
                  name="Cámara"
                  supported={arSupport.capabilities.camera}
                />
                <CapabilityItem
                  name="Giroscopio"
                  supported={arSupport.capabilities.gyroscope}
                />
              </div>
              
              <div className="bg-blue-900/20 rounded-lg p-4 mb-6 border 
                border-blue-500/30">
                <p className="text-sm text-blue-300">
                  <strong>Tip:</strong> Para la mejor experiencia AR, usa un 
                  dispositivo móvil moderno con Chrome o Safari actualizado.
                </p>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowCapabilityModal(false);
                    setShowPreview(true);
                  }}
                  className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 
                    text-white rounded-lg font-semibold transition-all"
                >
                  Ver Vista 3D
                </button>
                
                <button
                  onClick={() => setShowCapabilityModal(false)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 
                    text-white rounded-lg font-semibold transition-all"
                >
                  Cerrar
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// Capability Item Component
function CapabilityItem({ name, supported }: { name: string; supported: boolean }) {
  return (
    <div className="flex items-center justify-between bg-gray-800/50 
      rounded-lg p-3">
      <span className="text-gray-300">{name}</span>
      {supported ? (
        <div className="flex items-center gap-2 text-green-400">
          <CheckCircle className="w-5 h-5" />
          <span className="text-sm">Soportado</span>
        </div>
      ) : (
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <span className="text-sm">No soportado</span>
        </div>
      )}
    </div>
  );
}