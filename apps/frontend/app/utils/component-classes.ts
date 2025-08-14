/**
 * Utilidades para el Sistema de Componentes de ICFES Leveling V2.0
 * Proporciona funciones para construir clases de componentes usando el sistema de diseño
 */

import { clsx, type ClassValue } from 'clsx';

/**
 * Función principal para combinar clases CSS
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/**
 * Sistema de Botones
 */
export const buttonClasses = {
  base: "inline-flex items-center justify-center rounded-md text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed",
  
  size: {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
    xl: "px-8 py-4 text-lg"
  },
  
  variant: {
    primary: "bg-primary text-white hover:bg-primary/90 focus:ring-primary/50 shadow-md hover:shadow-lg",
    secondary: "bg-secondary text-white hover:bg-secondary/90 focus:ring-secondary/50 shadow-md hover:shadow-lg",
    outline: "border-2 border-primary text-primary hover:bg-primary hover:text-white focus:ring-primary/50",
    ghost: "text-primary hover:bg-primary/10 focus:ring-primary/50",
    danger: "bg-error text-white hover:bg-error/90 focus:ring-error/50 shadow-md hover:shadow-lg",
    success: "bg-success text-white hover:bg-success/90 focus:ring-success/50 shadow-md hover:shadow-lg"
  },
  
  state: {
    loading: "opacity-75 cursor-wait",
    disabled: "opacity-50 cursor-not-allowed pointer-events-none",
    active: "ring-2 ring-offset-2 ring-primary/50"
  },
  
  glow: {
    primary: "shadow-glow-primary hover:shadow-glow-primary/80",
    secondary: "shadow-glow-secondary hover:shadow-glow-secondary/80",
    success: "shadow-glow-success hover:shadow-glow-success/80",
    error: "shadow-glow-error hover:shadow-glow-error/80"
  },
  
  responsive: {
    mobile: "w-full sm:w-auto",
    tablet: "w-full md:w-auto",
    desktop: "w-auto"
  }
};

/**
 * Construye clases para botones
 */
export function buildButtonClasses(options: {
  size?: keyof typeof buttonClasses.size;
  variant?: keyof typeof buttonClasses.variant;
  state?: keyof typeof buttonClasses.state;
  glow?: keyof typeof buttonClasses.glow;
  responsive?: keyof typeof buttonClasses.responsive;
  className?: string;
}) {
  const {
    size = 'md',
    variant = 'primary',
    state,
    glow,
    responsive,
    className
  } = options;

  return cn(
    buttonClasses.base,
    buttonClasses.size[size],
    buttonClasses.variant[variant],
    state && buttonClasses.state[state],
    glow && buttonClasses.glow[glow],
    responsive && buttonClasses.responsive[responsive],
    className
  );
}

/**
 * Sistema de Tarjetas
 */
export const cardClasses = {
  base: "bg-background-card rounded-lg border border-neutral-200 shadow-sm hover:shadow-md transition-all duration-200",
  
  size: {
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
    xl: "p-10"
  },
  
  variant: {
    default: "bg-background-card border-neutral-200",
    elevated: "bg-background-card border-neutral-200 shadow-lg hover:shadow-xl",
    outlined: "bg-transparent border-2 border-primary/20",
    interactive: "bg-background-card border-neutral-200 hover:border-primary/30 hover:shadow-lg cursor-pointer"
  },
  
  state: {
    hover: "hover:shadow-lg hover:border-primary/30",
    active: "ring-2 ring-primary/20",
    selected: "border-primary bg-primary/5"
  },
  
  glow: {
    primary: "shadow-glow-primary",
    secondary: "shadow-glow-secondary",
    success: "shadow-glow-success",
    error: "shadow-glow-error"
  }
};

/**
 * Construye clases para tarjetas
 */
export function buildCardClasses(options: {
  size?: keyof typeof cardClasses.size;
  variant?: keyof typeof cardClasses.variant;
  state?: keyof typeof cardClasses.state;
  glow?: keyof typeof cardClasses.glow;
  className?: string;
}) {
  const {
    size = 'md',
    variant = 'default',
    state,
    glow,
    className
  } = options;

  return cn(
    cardClasses.base,
    cardClasses.size[size],
    cardClasses.variant[variant],
    state && cardClasses.state[state],
    glow && cardClasses.glow[glow],
    className
  );
}

/**
 * Sistema de Inputs
 */
export const inputClasses = {
  base: "block w-full rounded-md border border-neutral-300 px-3 py-2 text-sm placeholder-neutral-500 focus:border-primary focus:ring-2 focus:ring-primary/20 focus:outline-none transition-all duration-200",
  
  size: {
    sm: "px-2 py-1.5 text-xs",
    md: "px-3 py-2 text-sm",
    lg: "px-4 py-3 text-base",
    xl: "px-6 py-4 text-lg"
  },
  
  variant: {
    default: "border-neutral-300 focus:border-primary focus:ring-primary/20",
    error: "border-error focus:border-error focus:ring-error/20",
    success: "border-success focus:border-success focus:ring-success/20",
    warning: "border-warning focus:border-warning focus:ring-warning/20"
  },
  
  state: {
    disabled: "bg-neutral-100 cursor-not-allowed opacity-50",
    readonly: "bg-neutral-50 cursor-default",
    loading: "bg-neutral-50"
  },
  
  glow: {
    primary: "focus:shadow-glow-primary",
    error: "focus:shadow-glow-error",
    success: "focus:shadow-glow-success",
    warning: "focus:shadow-glow-warning"
  }
};

/**
 * Construye clases para inputs
 */
export function buildInputClasses(options: {
  size?: keyof typeof inputClasses.size;
  variant?: keyof typeof inputClasses.variant;
  state?: keyof typeof inputClasses.state;
  glow?: keyof typeof inputClasses.glow;
  className?: string;
}) {
  const {
    size = 'md',
    variant = 'default',
    state,
    glow,
    className
  } = options;

  return cn(
    inputClasses.base,
    inputClasses.size[size],
    inputClasses.variant[variant],
    state && inputClasses.state[state],
    glow && inputClasses.glow[glow],
    className
  );
}

/**
 * Sistema de Badges
 */
export const badgeClasses = {
  base: "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
  
  size: {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-0.5 text-xs",
    lg: "px-3 py-1 text-sm"
  },
  
  variant: {
    primary: "bg-primary/10 text-primary border border-primary/20",
    secondary: "bg-secondary/10 text-secondary border border-secondary/20",
    success: "bg-success/10 text-success border border-success/20",
    warning: "bg-warning/10 text-warning border border-warning/20",
    error: "bg-error/10 text-error border border-error/20",
    info: "bg-info/10 text-info border border-info/20",
    neutral: "bg-neutral/10 text-neutral-700 border border-neutral-200"
  },
  
  state: {
    solid: "text-white",
    outline: "bg-transparent",
    soft: "bg-opacity-10"
  },
  
  glow: {
    primary: "shadow-glow-primary",
    secondary: "shadow-glow-secondary",
    success: "shadow-glow-success",
    error: "shadow-glow-error"
  }
};

/**
 * Construye clases para badges
 */
export function buildBadgeClasses(options: {
  size?: keyof typeof badgeClasses.size;
  variant?: keyof typeof badgeClasses.variant;
  state?: keyof typeof badgeClasses.state;
  glow?: keyof typeof badgeClasses.glow;
  className?: string;
}) {
  const {
    size = 'md',
    variant = 'primary',
    state,
    glow,
    className
  } = options;

  return cn(
    badgeClasses.base,
    badgeClasses.size[size],
    badgeClasses.variant[variant],
    state && badgeClasses.state[state],
    glow && badgeClasses.glow[glow],
    className
  );
}

/**
 * Sistema de Alertas
 */
export const alertClasses = {
  base: "rounded-lg border p-4",
  
  variant: {
    info: "bg-info/10 border-info/20 text-info-800",
    success: "bg-success/10 border-success/20 text-success-800",
    warning: "bg-warning/10 border-warning/20 text-warning-800",
    error: "bg-error/10 border-error/20 text-error-800"
  },
  
  size: {
    sm: "p-3 text-sm",
    md: "p-4 text-base",
    lg: "p-6 text-lg"
  },
  
  state: {
    dismissible: "pr-12",
    withIcon: "pl-12",
    interactive: "cursor-pointer hover:shadow-md transition-shadow duration-200"
  }
};

/**
 * Construye clases para alertas
 */
export function buildAlertClasses(options: {
  variant?: keyof typeof alertClasses.variant;
  size?: keyof typeof alertClasses.size;
  state?: keyof typeof alertClasses.state;
  className?: string;
}) {
  const {
    variant = 'info',
    size = 'md',
    state,
    className
  } = options;

  return cn(
    alertClasses.base,
    alertClasses.variant[variant],
    alertClasses.size[size],
    state && alertClasses.state[state],
    className
  );
}

/**
 * Sistema de Loading
 */
export const loadingClasses = {
  base: "inline-flex items-center justify-center",
  
  spinner: {
    base: "animate-spin rounded-full border-2 border-neutral-200 border-t-transparent",
    size: {
      sm: "w-4 h-4",
      md: "w-6 h-6",
      lg: "w-8 h-8",
      xl: "w-12 h-12"
    },
    color: {
      primary: "border-primary border-t-transparent",
      secondary: "border-secondary border-t-transparent",
      white: "border-white border-t-transparent"
    }
  },
  
  skeleton: {
    base: "animate-pulse bg-neutral-200 rounded",
    text: "h-4 bg-neutral-200 rounded",
    title: "h-6 bg-neutral-200 rounded",
    avatar: "w-10 h-10 bg-neutral-200 rounded-full",
    card: "h-32 bg-neutral-200 rounded-lg"
  }
};

/**
 * Construye clases para spinners de loading
 */
export function buildSpinnerClasses(options: {
  size?: keyof typeof loadingClasses.spinner.size;
  color?: keyof typeof loadingClasses.spinner.color;
  className?: string;
}) {
  const {
    size = 'md',
    color = 'primary',
    className
  } = options;

  return cn(
    loadingClasses.spinner.base,
    loadingClasses.spinner.size[size],
    loadingClasses.spinner.color[color],
    className
  );
}

/**
 * Construye clases para skeletons de loading
 */
export function buildSkeletonClasses(type: keyof typeof loadingClasses.skeleton, className?: string) {
  return cn(
    loadingClasses.skeleton.base,
    loadingClasses.skeleton[type],
    className
  );
}

/**
 * Utilidades de Espaciado Responsivo
 */
export const spacingClasses = {
  container: "container-responsive",
  section: "py-12 md:py-16 lg:py-20",
  sectionSmall: "py-8 md:py-12",
  sectionLarge: "py-16 md:py-20 lg:py-24",
  
  padding: {
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
    xl: "p-10"
  },
  
  margin: {
    sm: "m-4",
    md: "m-6",
    lg: "m-8",
    xl: "m-10"
  }
};

/**
 * Utilidades de Tipografía
 */
export const typographyClasses = {
  heading: {
    h1: "text-4xl md:text-5xl lg:text-6xl font-bold font-display",
    h2: "text-3xl md:text-4xl lg:text-5xl font-bold font-display",
    h3: "text-2xl md:text-3xl lg:text-4xl font-semibold font-display",
    h4: "text-xl md:text-2xl lg:text-3xl font-semibold font-display",
    h5: "text-lg md:text-xl lg:text-2xl font-medium font-display",
    h6: "text-base md:text-lg lg:text-xl font-medium font-display"
  },
  
  body: {
    large: "text-lg leading-relaxed",
    base: "text-base leading-normal",
    small: "text-sm leading-normal",
    caption: "text-xs leading-tight"
  },
  
  font: {
    primary: "font-primary",
    secondary: "font-secondary",
    mono: "font-mono",
    display: "font-display"
  }
};

/**
 * Utilidades de Animación
 */
export const animationClasses = {
  enter: "animate-fade-in",
  slideUp: "animate-slide-up",
  scaleIn: "animate-scale-in",
  bounceCorrect: "animate-bounce-correct",
  shakeWrong: "animate-shake-wrong",
  
  duration: {
    fast: "duration-150",
    base: "duration-300",
    slow: "duration-500",
    slower: "duration-700"
  },
  
  easing: {
    ease: "ease-out",
    linear: "ease-linear",
    bounce: "ease-bounce"
  }
};

/**
 * Utilidades de Accesibilidad
 */
export const accessibilityClasses = {
  srOnly: "sr-only",
  focusVisible: "focus-visible",
  reducedMotion: "motion-reduce:animate-none"
};

/**
 * Utilidades de Estado
 */
export const stateClasses = {
  hover: "hover:",
  focus: "focus:",
  active: "active:",
  disabled: "disabled:",
  group: "group-hover:",
  peer: "peer-focus:"
};

/**
 * Función helper para construir clases condicionales
 */
export function conditionalClasses(
  baseClasses: string,
  conditionalClasses: Record<string, boolean> = {},
  additionalClasses?: string
) {
  const conditional = Object.entries(conditionalClasses)
    .filter(([, condition]) => condition)
    .map(([className]) => className)
    .join(' ');

  return cn(baseClasses, conditional, additionalClasses);
}

/**
 * Función helper para construir clases responsivas
 */
export function responsiveClasses(
  baseClasses: string,
  responsiveVariants: Record<string, string> = {},
  additionalClasses?: string
) {
  const responsive = Object.entries(responsiveVariants)
    .map(([breakpoint, classes]) => `${breakpoint}:${classes}`)
    .join(' ');

  return cn(baseClasses, responsive, additionalClasses);
}
