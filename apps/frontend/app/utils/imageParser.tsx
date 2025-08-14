import React from 'react';

export interface ParsedContent {
  type: 'text' | 'image' | 'mixed';
  content: React.ReactNode;
}

/**
 * Parser mejorado para detectar y renderizar imágenes en texto
 * Soporta múltiples formatos:
 * - [Imagen: /mathimg/file.png]
 * - /mathimg/file.png
 * - C:\path\to\file.png (convierte a /mathimg/file.png)
 * - ![alt text](/mathimg/file.png) (formato markdown)
 */
export function parseImageContent(text: string | null | undefined): ParsedContent {
  if (!text || typeof text !== 'string') {
    return { type: 'text', content: null };
  }

  // Patrones de detección mejorados
  const patterns = [
    // [Imagen: /path/to/image.ext]
    /\[Imagen:\s*([^\]]+)\]/gi,
    // Rutas directas de imagen
    /(\/mathimg\/[^\s,'"]+\.(png|jpg|jpeg|gif|svg))/gi,
    // Rutas de Windows
    /([A-Z]:\\[^\s,'"]+\.(png|jpg|jpeg|gif|svg))/gi,
    // Markdown images
    /!\[([^\]]*)\]\(([^)]+)\)/gi,
    // URLs completas
    /(https?:\/\/[^\s,'"]+\.(png|jpg|jpeg|gif|svg))/gi
  ];

  let hasImages = false;
  let processedText = text;
  const imageElements: Array<{ original: string; element: React.ReactNode }> = [];

  // Procesar cada patrón
  patterns.forEach((pattern, index) => {
    const matches = [...text.matchAll(pattern)];
    matches.forEach(match => {
      hasImages = true;
      let imagePath = '';
      let altText = 'Imagen';

      switch (index) {
        case 0: // [Imagen: path]
          imagePath = match[1].trim();
          break;
        case 1: // Ruta directa /mathimg/
          imagePath = match[1];
          break;
        case 2: // Ruta Windows
          const filename = match[1].split(/[\\\/]/).pop() || '';
          imagePath = `/mathimg/${filename}`;
          break;
        case 3: // Markdown
          altText = match[1] || 'Imagen';
          imagePath = match[2];
          break;
        case 4: // URL completa
          imagePath = match[1];
          break;
      }

      const imageElement = (
        <img
          key={`img-${imagePath}-${imageElements.length}`}
          src={imagePath}
          alt={altText}
          className="inline-block max-w-full h-auto my-2 rounded shadow-sm"
          loading="lazy"
          onError={(e) => {
            const img = e.target as HTMLImageElement;
            img.style.display = 'none';
            // Insertar mensaje de error después de la imagen
            const errorMsg = document.createElement('span');
            errorMsg.className = 'text-red-500 text-sm italic';
            errorMsg.textContent = `[Error cargando imagen: ${imagePath}]`;
            img.parentNode?.insertBefore(errorMsg, img.nextSibling);
          }}
        />
      );

      imageElements.push({
        original: match[0],
        element: imageElement
      });
    });
  });

  // Si no hay imágenes, retornar texto simple
  if (!hasImages) {
    return { type: 'text', content: text };
  }

  // Si solo hay imágenes (sin texto adicional)
  const textWithoutImages = imageElements.reduce(
    (txt, { original }) => txt.replace(original, '').trim(),
    processedText
  );

  if (!textWithoutImages) {
    return {
      type: 'image',
      content: <>{imageElements.map(({ element }) => element)}</>
    };
  }

  // Contenido mixto (texto + imágenes)
  let elements: React.ReactNode[] = [];
  let lastIndex = 0;

  // Ordenar las imágenes por posición en el texto
  const sortedImages = imageElements
    .map(({ original, element }) => ({
      original,
      element,
      index: text.indexOf(original)
    }))
    .sort((a, b) => a.index - b.index);

  sortedImages.forEach(({ original, element, index }) => {
    // Agregar texto antes de la imagen
    if (index > lastIndex) {
      elements.push(
        <span key={`text-${lastIndex}`}>
          {text.substring(lastIndex, index)}
        </span>
      );
    }
    // Agregar la imagen
    elements.push(element);
    lastIndex = index + original.length;
  });

  // Agregar texto restante
  if (lastIndex < text.length) {
    elements.push(
      <span key={`text-${lastIndex}`}>
        {text.substring(lastIndex)}
      </span>
    );
  }

  return {
    type: 'mixed',
    content: <>{elements}</>
  };
}

// Hook para usar el parser con estado de carga
export function useImageParser(text: string | null | undefined) {
  const [isLoading, setIsLoading] = React.useState(true);
  const [parsed, setParsed] = React.useState<ParsedContent>({ type: 'text', content: null });

  React.useEffect(() => {
    setIsLoading(true);
    const result = parseImageContent(text);
    setParsed(result);
    setIsLoading(false);
  }, [text]);

  return { isLoading, parsed };
}

// Componente wrapper para facilitar el uso
export function ParsedText({ text, className = '' }: { text: string | null | undefined; className?: string }) {
  const { parsed } = useImageParser(text);
  
  return (
    <div className={className}>
      {parsed.content}
    </div>
  );
}
