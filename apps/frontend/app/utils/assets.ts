// Utilidad para manejo centralizado de assets
export class AssetsManager {
  // Sonidos
  public static readonly SOUNDS = {
    // Efectos de UI
    CLICK: '/sounds/click.mp3',
    HOVER: '/sounds/hover.mp3',
    SUCCESS: '/sounds/success.mp3',
    ERROR: '/sounds/error.mp3',
    NOTIFICATION: '/sounds/notification.mp3',
    
    // Progreso y logros
    LEVEL_UP: '/sounds/level_up.mp3',
    MAGIC: '/sounds/magic.mp3',
    UNLOCK: '/sounds/unlock.mp3',
    REWARD: '/sounds/reward.mp3',
    VICTORY: '/sounds/victory.mp3',
    DEFEAT: '/sounds/defeat.mp3',
    
    // Combate y habilidades
    SPELL_CAST: '/sounds/spell-cast.mp3',
    WARRIOR_ROAR: '/sounds/warrior-roar.mp3',
    BOW_RELEASE: '/sounds/bow-release.mp3',
    HEALING_SPELL: '/sounds/healing-spell.mp3',
    STEALTH_MOVE: '/sounds/stealth-move.mp3',
    DAMAGE_HIT: '/sounds/damage_hit.mp3',
    DEFEND: '/sounds/defend.mp3',
    CRITICAL: '/sounds/critical.mp3',
    COMBO_BREAK: '/sounds/combo_break.mp3',
    ULTIMATE_READY: '/sounds/ultimate_ready.mp3',
    
    // Ambientes
    MENU: '/sounds/menu.mp3',
    STUDY: '/sounds/study.mp3',
    PORTAL_HUM: '/sounds/portal_hum.mp3',
    PORTAL_SUCCESS: '/sounds/portal_success.mp3',
    PORTAL_REJECT: '/sounds/portal_reject.mp3',
    TYPING_PULSE: '/sounds/typing_pulse.mp3'
  } as const;

  // Iconos
  public static readonly ICONS = {
    FAVICON_16: '/icons/16.png',
    FAVICON_32: '/icons/32.png',
    APP_ICON_192: '/icons/192.png',
    APP_ICON_512: '/icons/512.png',
    LARGE_TILE: '/icons/LargeTile.scale-400.png',
    SPLASH_SCREEN: '/icons/SplashScreen.scale-400.png'
  } as const;

  // Cache para elementos de audio
  private static audioCache = new Map<string, HTMLAudioElement>();

  /**
   * Precarga un sonido específico
   */
  public static preloadSound(soundPath: string): HTMLAudioElement {
    if (typeof Audio === 'undefined') return null;
    
    if (!this.audioCache.has(soundPath)) {
      const audio = new Audio(soundPath);
      audio.preload = 'auto';
      audio.volume = 0.7; // Volumen por defecto
      this.audioCache.set(soundPath, audio);
    }
    
    return this.audioCache.get(soundPath);
  }

  /**
   * Reproduce un sonido con manejo de errores
   */
  public static playSound(soundPath: string, volume: number = 0.7): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const audio = this.preloadSound(soundPath);
        if (!audio) {
          resolve(); // En SSR, resolver sin error
          return;
        }

        audio.volume = Math.max(0, Math.min(1, volume));
        audio.currentTime = 0;
        
        const playPromise = audio.play();
        
        if (playPromise !== undefined) {
          playPromise
            .then(() => resolve())
            .catch((error) => {
              console.warn('Audio play failed:', error);
              resolve(); // No rechazar para evitar romper la UX
            });
        } else {
          resolve();
        }
      } catch (error) {
        console.warn('Audio error:', error);
        resolve(); // No rechazar para evitar romper la UX
      }
    });
  }

  /**
   * Precarga todos los sonidos esenciales
   */
  public static preloadEssentialSounds(): void {
    const essentialSounds = [
      this.SOUNDS.CLICK,
      this.SOUNDS.HOVER,
      this.SOUNDS.SUCCESS,
      this.SOUNDS.ERROR,
      this.SOUNDS.LEVEL_UP,
      this.SOUNDS.MAGIC
    ];

    essentialSounds.forEach(sound => {
      this.preloadSound(sound);
    });
  }

  /**
   * Para todos los sonidos que estén reproduciéndose
   */
  public static stopAllSounds(): void {
    this.audioCache.forEach(audio => {
      audio.pause();
      audio.currentTime = 0;
    });
  }

  /**
   * Ajusta el volumen global de todos los sonidos
   */
  public static setGlobalVolume(volume: number): void {
    const normalizedVolume = Math.max(0, Math.min(1, volume));
    this.audioCache.forEach(audio => {
      audio.volume = normalizedVolume;
    });
  }

  /**
   * Verifica si un asset existe (para imágenes)
   */
  public static checkImageExists(imagePath: string): Promise<boolean> {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(true);
      img.onerror = () => resolve(false);
      img.src = imagePath;
    });
  }

  /**
   * Obtiene el path correcto para un icono según el tamaño
   */
  public static getIconPath(size: number): string {
    const validSizes = [16, 20, 24, 30, 32, 36, 40, 44, 48, 60, 64, 72, 80, 96, 114, 120, 128, 144, 152, 167, 180, 192, 256, 512, 1024];
    const closestSize = validSizes.reduce((prev, curr) => 
      Math.abs(curr - size) < Math.abs(prev - size) ? curr : prev
    );
    return `/icons/${closestSize}.png`;
  }
}

// Hook para usar sonidos en componentes React
export function useSound() {
  const playSound = (soundPath: string, volume?: number) => {
    AssetsManager.playSound(soundPath, volume);
  };

  const playClickSound = () => playSound(AssetsManager.SOUNDS.CLICK);
  const playHoverSound = () => playSound(AssetsManager.SOUNDS.HOVER);
  const playSuccessSound = () => playSound(AssetsManager.SOUNDS.SUCCESS);
  const playErrorSound = () => playSound(AssetsManager.SOUNDS.ERROR);
  const playLevelUpSound = () => playSound(AssetsManager.SOUNDS.LEVEL_UP);
  const playMagicSound = () => playSound(AssetsManager.SOUNDS.MAGIC);
  const playVictorySound = () => playSound(AssetsManager.SOUNDS.VICTORY);
  const playDefeatSound = () => playSound(AssetsManager.SOUNDS.DEFEAT);

  return {
    playSound,
    playClickSound,
    playHoverSound,
    playSuccessSound,
    playErrorSound,
    playLevelUpSound,
    playMagicSound,
    playVictorySound,
    playDefeatSound,
    stopAllSounds: AssetsManager.stopAllSounds,
    setGlobalVolume: AssetsManager.setGlobalVolume
  };
}

// Precargar sonidos esenciales cuando se importe este módulo
if (typeof window !== 'undefined') {
  // Delay para evitar bloquear la carga inicial
  setTimeout(() => {
    AssetsManager.preloadEssentialSounds();
  }, 1000);
}