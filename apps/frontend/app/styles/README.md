# Sistema de Diseño ICFES Leveling V2.0

Este directorio contiene el sistema de diseño completo para la aplicación ICFES Leveling, implementado siguiendo las mejores prácticas de diseño moderno y accesibilidad.

## 🎨 Estructura del Sistema de Diseño

```
app/styles/
├── design-tokens.yml          # Tokens de diseño en formato YAML
├── component-system.yml       # Sistema de componentes y variantes
├── tailwind-v4.css           # Configuración de Tailwind CSS v4
├── generated/                 # Archivos generados automáticamente
│   ├── design-tokens.css     # Variables CSS generadas
│   ├── design-tokens.scss    # Variables SCSS generadas
│   └── design-tokens.js      # Módulo JavaScript generado
└── README.md                 # Esta documentación
```

## 🚀 Características Principales

### 1. Design Tokens
- **Colores**: Sistema de colores semánticos y neutrales
- **Tipografía**: Escalas de fuentes, pesos y alturas de línea
- **Espaciado**: Sistema de espaciado consistente (0.25rem a 24rem)
- **Bordes**: Radios y anchos de borde estandarizados
- **Sombras**: Sistema de sombras y efectos de glow
- **Animaciones**: Duración, easing y keyframes personalizados
- **Breakpoints**: Puntos de quiebre responsivos
- **Z-Index**: Sistema de capas organizado

### 2. Sistema de Componentes
- **Botones**: Múltiples variantes, tamaños y estados
- **Tarjetas**: Diferentes estilos y variantes interactivas
- **Inputs**: Estados de validación y feedback visual
- **Badges**: Sistema de etiquetas con variantes semánticas
- **Alertas**: Diferentes tipos de notificaciones
- **Modales**: Sistema de overlays y contenido modal
- **Tooltips**: Información contextual con posicionamiento
- **Loading**: Spinners y skeletons de carga
- **Navegación**: Menús, tabs y breadcrumbs
- **Formularios**: Campos, etiquetas y mensajes de error
- **Data Display**: Tablas, listas y estadísticas
- **Feedback**: Toasts y barras de progreso

### 3. Tailwind CSS v4
- Directiva `@theme` para design tokens
- Variables CSS personalizadas
- Utilidades de glow y efectos especiales
- Animaciones personalizadas
- Sistema responsivo mobile-first
- Utilidades de accesibilidad

## 🛠️ Uso del Sistema

### 1. Importar Utilidades

```typescript
import {
  buildButtonClasses,
  buildCardClasses,
  buildBadgeClasses,
  spacingClasses,
  typographyClasses,
  animationClasses,
  cn
} from '../../utils/component-classes';
```

### 2. Construir Clases de Componentes

```typescript
// Botón primario con glow
const buttonClasses = buildButtonClasses({
  variant: 'primary',
  size: 'lg',
  glow: 'primary',
  responsive: 'mobile'
});

// Tarjeta elevada con estado hover
const cardClasses = buildCardClasses({
  size: 'lg',
  variant: 'elevated',
  state: 'hover'
});

// Badge de éxito con glow
const badgeClasses = buildBadgeClasses({
  variant: 'success',
  size: 'md',
  glow: 'success'
});
```

### 3. Usar Clases de Utilidad

```typescript
// Espaciado responsivo
<div className={cn(spacingClasses.container, "py-8")}>

// Tipografía
<h1 className={cn(typographyClasses.heading.h1, "text-primary")}>

// Animaciones
<motion.div className={animationClasses.enter}>
```

### 4. Combinar Clases

```typescript
import { cn } from '../../utils/component-classes';

// Combinar clases base con variantes
const finalClasses = cn(
  'base-class',
  variant && 'variant-class',
  size && 'size-class',
  className // Clases adicionales del prop
);
```

## 🔧 Generación de Tokens

### 1. Instalar Dependencias

```bash
npm install
```

### 2. Generar Tokens

```bash
# Generar una vez
npm run build:tokens

# Generar y observar cambios
npm run watch:tokens
```

### 3. Archivos Generados

Los tokens se generan automáticamente en:
- `app/styles/generated/design-tokens.css` - Variables CSS
- `app/styles/generated/design-tokens.scss` - Variables SCSS  
- `app/styles/generated/design-tokens.js` - Módulo JavaScript

## 📱 Responsive Design

### Breakpoints
- **sm**: 640px (Mobile)
- **md**: 768px (Tablet)
- **lg**: 1024px (Desktop)
- **xl**: 1280px (Large Desktop)
- **2xl**: 1536px (Extra Large)

### Clases Responsivas

```typescript
// Botón full-width en mobile, auto en desktop
const buttonClasses = buildButtonClasses({
  responsive: 'mobile'
});

// Contenedor responsivo
<div className={spacingClasses.container}>
```

## ♿ Accesibilidad

### 1. Reducción de Movimiento

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 2. Focus Visible

```css
.focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### 3. Screen Reader Only

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

## 🎭 Animaciones

### 1. Duración
- **fast**: 150ms
- **base**: 300ms
- **slow**: 500ms
- **slower**: 700ms
- **slowest**: 1000ms

### 2. Easing
- **ease**: cubic-bezier(0.4, 0, 0.2, 1)
- **easeIn**: cubic-bezier(0.4, 0, 1, 1)
- **easeOut**: cubic-bezier(0, 0, 0.2, 1)
- **easeInOut**: cubic-bezier(0.4, 0, 0.2, 1)

### 3. Keyframes Personalizados

```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes scaleIn {
  from { transform: scale(0.8); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
```

## 🌟 Efectos Especiales

### 1. Glow Effects

```css
.glow-primary {
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
}

.glow-secondary {
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
}

.glow-success {
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
}

.glow-error {
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
}
```

### 2. Text Glow

```css
.text-glow-primary {
  text-shadow: 0 0 10px var(--color-primary);
}

.text-glow-secondary {
  text-shadow: 0 0 10px var(--color-secondary);
}
```

## 📚 Ejemplos de Uso

### 1. Componente de Botón

```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  glow?: 'primary' | 'secondary' | 'success' | 'error';
  responsive?: 'mobile' | 'tablet' | 'desktop';
  disabled?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  glow,
  responsive,
  disabled,
  loading,
  children,
  className,
  onClick
}) => {
  const buttonClasses = buildButtonClasses({
    variant,
    size,
    glow,
    responsive,
    state: loading ? 'loading' : disabled ? 'disabled' : undefined,
    className
  });

  return (
    <button
      className={buttonClasses}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  );
};
```

### 2. Componente de Tarjeta

```typescript
interface CardProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'elevated' | 'outlined' | 'interactive';
  glow?: 'primary' | 'secondary' | 'success' | 'error';
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({
  size = 'md',
  variant = 'default',
  glow,
  children,
  className,
  onClick
}) => {
  const cardClasses = buildCardClasses({
    size,
    variant,
    glow,
    state: onClick ? 'interactive' : undefined,
    className
  });

  return (
    <div className={cardClasses} onClick={onClick}>
      {children}
    </div>
  );
};
```

## 🔄 Flujo de Trabajo

### 1. Desarrollo
1. Editar `design-tokens.yml` para nuevos tokens
2. Editar `component-system.yml` para nuevos componentes
3. Ejecutar `npm run watch:tokens` para generar automáticamente
4. Usar las utilidades en los componentes

### 2. Build
1. Los tokens se generan automáticamente con `npm run build`
2. Los archivos CSS se incluyen en el build de Next.js
3. Las utilidades están disponibles en runtime

### 3. Mantenimiento
1. Revisar tokens obsoletos regularmente
2. Actualizar documentación cuando se agreguen nuevos componentes
3. Mantener consistencia en el naming de tokens

## 📖 Referencias

- [Style Dictionary Documentation](https://amzn.github.io/style-dictionary/)
- [Tailwind CSS v4](https://tailwindcss.com/docs)
- [Framer Motion](https://www.framer.com/motion/)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## 🤝 Contribución

1. Seguir las convenciones de naming establecidas
2. Documentar nuevos tokens y componentes
3. Mantener la consistencia del sistema
4. Probar en diferentes dispositivos y tamaños de pantalla
5. Verificar la accesibilidad de nuevos componentes

---

**Nota**: Este sistema de diseño está diseñado para ser escalable y mantenible. Cualquier cambio debe seguir las convenciones establecidas y ser documentado apropiadamente.
