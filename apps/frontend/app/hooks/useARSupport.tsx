import { useState, useEffect } from 'react';

interface ARSupportInfo {
  isSupported: boolean;
  isChecking: boolean;
  error: string | null;
  capabilities: {
    webXR: boolean;
    immersiveAR: boolean;
    immersiveVR: boolean;
    gyroscope: boolean;
    accelerometer: boolean;
    camera: boolean;
  };
}

export function useARSupport(): ARSupportInfo {
  const [support, setSupport] = useState<ARSupportInfo>({
    isSupported: false,
    isChecking: true,
    error: null,
    capabilities: {
      webXR: false,
      immersiveAR: false,
      immersiveVR: false,
      gyroscope: false,
      accelerometer: false,
      camera: false
    }
  });

  useEffect(() => {
    checkARSupport();
  }, []);

  const checkARSupport = async () => {
    const capabilities = {
      webXR: false,
      immersiveAR: false,
      immersiveVR: false,
      gyroscope: false,
      accelerometer: false,
      camera: false
    };

    try {
      // Check WebXR support
      if ('xr' in navigator && navigator.xr) {
        capabilities.webXR = true;

        // Check AR support
        try {
          const arSupported = await navigator.xr.isSessionSupported('immersive-ar');
          capabilities.immersiveAR = arSupported;
        } catch (e) {
          console.warn('AR check failed:', e);
        }

        // Check VR support
        try {
          const vrSupported = await navigator.xr.isSessionSupported('immersive-vr');
          capabilities.immersiveVR = vrSupported;
        } catch (e) {
          console.warn('VR check failed:', e);
        }
      }

      // Check device sensors
      if ('DeviceOrientationEvent' in window && 
          typeof (DeviceOrientationEvent as any).requestPermission !== 'function') {
        capabilities.gyroscope = true;
      }

      if ('DeviceMotionEvent' in window && 
          typeof (DeviceMotionEvent as any).requestPermission !== 'function') {
        capabilities.accelerometer = true;
      }

      // Check camera access
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } 
          });
          stream.getTracks().forEach(track => track.stop());
          capabilities.camera = true;
        } catch (e) {
          console.warn('Camera check failed:', e);
        }
      }

      // Determine overall support
      const isSupported = capabilities.webXR && capabilities.immersiveAR;

      setSupport({
        isSupported,
        isChecking: false,
        error: isSupported ? null : 'Tu dispositivo no soporta WebAR completamente',
        capabilities
      });
    } catch (error) {
      setSupport({
        isSupported: false,
        isChecking: false,
        error: 'Error al verificar soporte AR',
        capabilities
      });
    }
  };

  return support;
}

// Helper to request permissions on iOS
export async function requestARPermissions(): Promise<boolean> {
  try {
    // Request camera permission
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
    }

    // Request motion sensors permission (iOS 13+)
    if (typeof (DeviceOrientationEvent as any).requestPermission === 'function') {
      const response = await (DeviceOrientationEvent as any).requestPermission();
      if (response !== 'granted') {
        return false;
      }
    }

    if (typeof (DeviceMotionEvent as any).requestPermission === 'function') {
      const response = await (DeviceMotionEvent as any).requestPermission();
      if (response !== 'granted') {
        return false;
      }
    }

    return true;
  } catch (error) {
    console.error('Error requesting AR permissions:', error);
    return false;
  }
}

// Check if device is mobile
export function isMobileDevice(): boolean {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  );
}

// Get AR readiness message
export function getARReadinessMessage(support: ARSupportInfo): string {
  if (support.isChecking) {
    return 'Verificando soporte AR...';
  }

  if (support.isSupported) {
    return '¡Tu dispositivo es compatible con AR!';
  }

  const missing = [];
  
  if (!support.capabilities.webXR) {
    missing.push('WebXR API');
  }
  
  if (!support.capabilities.immersiveAR) {
    missing.push('Modo AR inmersivo');
  }
  
  if (!support.capabilities.camera) {
    missing.push('Acceso a cámara');
  }

  if (missing.length > 0) {
    return `Falta soporte para: ${missing.join(', ')}`;
  }

  return support.error || 'AR no disponible';
}