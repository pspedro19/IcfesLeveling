/**
 * Configuración de Style Dictionary para ICFES Leveling
 * Genera tokens CSS desde archivos YML para el sistema de diseño
 */

const StyleDictionary = require('style-dictionary');

module.exports = {
  source: ['app/styles/*.yml'],
  platforms: {
    css: {
      transformGroup: 'css',
      buildPath: 'app/styles/generated/',
      files: [
        {
          destination: 'design-tokens.css',
          format: 'css/variables',
          filter: (token) => {
            // Solo incluir tokens de nivel raíz
            return token.path.length === 2;
          }
        }
      ]
    },
    scss: {
      transformGroup: 'scss',
      buildPath: 'app/styles/generated/',
      files: [
        {
          destination: 'design-tokens.scss',
          format: 'scss/variables',
          filter: (token) => {
            // Solo incluir tokens de nivel raíz
            return token.path.length === 2;
          }
        }
      ]
    },
    js: {
      transformGroup: 'js',
      buildPath: 'app/styles/generated/',
      files: [
        {
          destination: 'design-tokens.js',
          format: 'javascript/module',
          filter: (token) => {
            // Solo incluir tokens de nivel raíz
            return token.path.length === 2;
          }
        }
      ]
    }
  }
};

// Transformaciones personalizadas
StyleDictionary.registerTransform({
  name: 'size/px',
  type: 'value',
  matcher: (prop) => {
    return prop.value.toString().includes('px');
  },
  transformer: (prop) => {
    return prop.value.toString().replace('px', '');
  }
});

StyleDictionary.registerTransform({
  name: 'size/rem',
  type: 'value',
  matcher: (prop) => {
    return prop.value.toString().includes('rem');
  },
  transformer: (prop) => {
    return prop.value.toString();
  }
});

StyleDictionary.registerTransform({
  name: 'color/hex',
  type: 'value',
  matcher: (prop) => {
    return prop.attributes.category === 'color';
  },
  transformer: (prop) => {
    return prop.value.toString();
  }
});

// Formato personalizado para CSS Variables
StyleDictionary.registerFormat({
  name: 'css/variables',
  formatter: (dictionary) => {
    return `/* Design Tokens generados automáticamente por Style Dictionary */
/* No editar manualmente - regenerar con: npm run build:tokens */

:root {
${dictionary.allProperties
  .map(prop => `  --${prop.name}: ${prop.value};`)
  .join('\n')}
}

/* Utilidades de acceso a tokens */
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'color')
  .map(prop => `.text-${prop.name} { color: var(--${prop.name}); }`)
  .join('\n')}

${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'spacing')
  .map(prop => `.p-${prop.name} { padding: var(--${prop.name}); }`)
  .join('\n')}

${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'spacing')
  .map(prop => `.m-${prop.name} { margin: var(--${prop.name}); }`)
  .join('\n')}

${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'typography' && prop.attributes.type === 'fontSize')
  .map(prop => `.text-${prop.name} { font-size: var(--${prop.name}); }`)
  .join('\n')}

${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'typography' && prop.attributes.type === 'fontWeight')
  .map(prop => `.font-${prop.name} { font-weight: var(--${prop.name}); }`)
  .join('\n')}

${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'borders' && prop.attributes.type === 'borderRadius')
  .map(prop => `.rounded-${prop.name} { border-radius: var(--${prop.name}); }`)
  .join('\n')}

${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'shadows')
  .map(prop => `.shadow-${prop.name} { box-shadow: var(--${prop.name}); }`)
  .join('\n')}
`;
  }
});

// Formato personalizado para SCSS Variables
StyleDictionary.registerFormat({
  name: 'scss/variables',
  formatter: (dictionary) => {
    return `// Design Tokens generados automáticamente por Style Dictionary
// No editar manualmente - regenerar con: npm run build:tokens

${dictionary.allProperties
  .map(prop => `$${prop.name}: ${prop.value};`)
  .join('\n')}

// Mapas de tokens por categoría
$colors: (
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'color')
  .map(prop => `  '${prop.name}': $${prop.name}`)
  .join(',\n')}
);

$spacing: (
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'spacing')
  .map(prop => `  '${prop.name}': $${prop.name}`)
  .join(',\n')}
);

$typography: (
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'typography')
  .map(prop => `  '${prop.name}': $${prop.name}`)
  .join(',\n')}
);

$borders: (
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'borders')
  .map(prop => `  '${prop.name}': $${prop.name}`)
  .join(',\n')}
);

$shadows: (
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'shadows')
  .map(prop => `  '${prop.name}': $${prop.name}`)
  .join(',\n')}
);

$animations: (
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'animations')
  .map(prop => `  '${prop.name}': $${prop.name}`)
  .join(',\n')}
);

$breakpoints: (
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'breakpoints')
  .map(prop => `  '${prop.name}': $${prop.name}`)
  .join(',\n')}
);

$z-index: (
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'zIndex')
  .map(prop => `  '${prop.name}': $${prop.name}`)
  .join(',\n')}
);
`;
  }
});

// Formato personalizado para JavaScript Module
StyleDictionary.registerFormat({
  name: 'javascript/module',
  formatter: (dictionary) => {
    return `// Design Tokens generados automáticamente por Style Dictionary
// No editar manualmente - regenerar con: npm run build:tokens

export const designTokens = {
${dictionary.allProperties
  .map(prop => `  ${prop.name}: '${prop.value}',`)
  .join('\n')}
};

// Tokens por categoría
export const colors = {
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'color')
  .map(prop => `  ${prop.name}: '${prop.value}',`)
  .join('\n')}
};

export const spacing = {
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'spacing')
  .map(prop => `  ${prop.name}: '${prop.value}',`)
  .join('\n')}
};

export const typography = {
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'typography')
  .map(prop => `  ${prop.name}: '${prop.value}',`)
  .join('\n')}
};

export const borders = {
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'borders')
  .map(prop => `  ${prop.name}: '${prop.value}',`)
  .join('\n')}
};

export const shadows = {
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'shadows')
  .map(prop => `  ${prop.name}: '${prop.value}',`)
  .join('\n')}
};

export const animations = {
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'animations')
  .map(prop => `  ${prop.name}: '${prop.value}',`)
  .join('\n')}
};

export const breakpoints = {
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'breakpoints')
  .map(prop => `  ${prop.name}: '${prop.value}',`)
  .join('\n')}
};

export const zIndex = {
${dictionary.allProperties
  .filter(prop => prop.attributes.category === 'zIndex')
  .map(prop => `  ${prop.name}: '${prop.value}',`)
  .join('\n')}
};

// Función helper para obtener tokens
export function getToken(category, name) {
  const categories = { colors, spacing, typography, borders, shadows, animations, breakpoints, zIndex };
  return categories[category]?.[name] || null;
}

// Función helper para obtener todos los tokens de una categoría
export function getTokensByCategory(category) {
  const categories = { colors, spacing, typography, borders, shadows, animations, breakpoints, zIndex };
  return categories[category] || {};
}

export default designTokens;
`;
  }
});
