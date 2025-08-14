'use client';

import { useState, useEffect } from 'react';

export default function TestImagesPage() {
  const [imageStats, setImageStats] = useState({
    total: 0,
    loaded: 0,
    failed: 0,
    checking: true
  });

  // Casos de prueba
  const testCases = [
    {
      title: 'Ruta relativa directa',
      text: '/mathimg/Math_12_R_A_Doc1.png'
    },
    {
      title: 'Formato [Imagen: ...]',
      text: '[Imagen: /mathimg/Math_12_R_B_Doc1.png]'
    },
    {
      title: 'Ruta Windows',
      text: 'C:\\Users\\PEDRO_PEREZ\\Documents\\IcfesLeveling\\mathimg\\Math_12_R_C_Doc1.png'
    },
    {
      title: 'Texto mixto',
      text: 'La respuesta correcta es [Imagen: /mathimg/Math_12_R_D_Doc1.png] según el gráfico.'
    },
    {
      title: 'Múltiples imágenes',
      text: 'Opción A: /mathimg/Math_32_R_A_Doc1.png y Opción B: /mathimg/Math_32_R_B_Doc1.png'
    }
  ];

  // Verificar todas las imágenes en public/mathimg
  useEffect(() => {
    const checkImages = async () => {
      try {
        // Lista de imágenes conocidas (deberías generar esta lista dinámicamente)
        const knownImages = [
          'Math_12_R_A_Doc1.png',
          'Math_12_R_B_Doc1.png',
          'Math_12_R_C_Doc1.png',
          'Math_12_R_D_Doc1.png',
          'Math_32_R_A_Doc1.png',
          'Math_32_R_B_Doc1.png',
          'Math_41_1_Doc1.png',
          'Math_42_1_Doc1.png'
        ];

        let loaded = 0;
        let failed = 0;

        await Promise.all(
          knownImages.map(filename => 
            new Promise((resolve) => {
              const img = new Image();
              img.onload = () => {
                loaded++;
                resolve(true);
              };
              img.onerror = () => {
                failed++;
                resolve(false);
              };
              img.src = `/mathimg/${filename}`;
            })
          )
        );

        setImageStats({
          total: knownImages.length,
          loaded,
          failed,
          checking: false
        });
      } catch (error) {
        console.error('Error verificando imágenes:', error);
      }
    };

    checkImages();
  }, []);

  // Función para parsear contenido de imagen (similar a la que implementamos)
  const parseImageContent = (text: string) => {
    if (!text) return { type: 'text', content: text };

    // Patrón [Imagen: /path/to/image.ext]
    const bracketMatch = text.match(/^\[Imagen:\s*([^\]]+)\]/i);
    if (bracketMatch && bracketMatch[1]) {
      return {
        type: 'image',
        content: (
          <img
            src={bracketMatch[1].trim()}
            alt="Imagen"
            className="max-w-full h-auto rounded"
            onError={(e) => {
              const target = e.currentTarget as HTMLImageElement;
              target.style.display = 'none';
            }}
          />
        )
      };
    }

    // Patrón ruta directa /mathimg/...
    const urlMatch = text.match(/(\/mathimg\/[^\s,]+\.(png|jpg|jpeg|gif))/i);
    if (urlMatch && urlMatch[1]) {
      return {
        type: 'image',
        content: (
          <img
            src={urlMatch[1]}
            alt="Imagen"
            className="max-w-full h-auto rounded"
            onError={(e) => {
              const target = e.currentTarget as HTMLImageElement;
              target.style.display = 'none';
            }}
          />
        )
      };
    }

    // Patrón ruta Windows
    const windowsMatch = text.match(/([A-Z]:\\[^\s,]+\.(png|jpg|jpeg|gif))/i);
    if (windowsMatch && windowsMatch[1]) {
      const filename = windowsMatch[1].split(/[\\\/]/).pop() || '';
      return {
        type: 'image',
        content: (
          <img
            src={`/mathimg/${filename}`}
            alt="Imagen"
            className="max-w-full h-auto rounded"
            onError={(e) => {
              const target = e.currentTarget as HTMLImageElement;
              target.style.display = 'none';
            }}
          />
        )
      };
    }

    return { type: 'text', content: text };
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">🧪 Test de Renderizado de Imágenes</h1>
        
        {/* Estado de las imágenes */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">📊 Estado de Imágenes</h2>
          {imageStats.checking ? (
            <p className="text-gray-600">Verificando imágenes...</p>
          ) : (
            <div className="space-y-2">
              <p>Total de imágenes: <span className="font-bold">{imageStats.total}</span></p>
              <p className="text-green-600">
                ✅ Cargadas: <span className="font-bold">{imageStats.loaded}</span>
              </p>
              {imageStats.failed > 0 && (
                <p className="text-red-600">
                  ❌ Fallidas: <span className="font-bold">{imageStats.failed}</span>
                </p>
              )}
            </div>
          )}
        </div>

        {/* Casos de prueba */}
        <div className="space-y-6">
          {testCases.map((testCase, index) => {
            const parsed = parseImageContent(testCase.text);
            
            return (
              <div key={index} className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-2">{testCase.title}</h3>
                
                <div className="mb-4 p-3 bg-gray-100 rounded font-mono text-sm overflow-x-auto">
                  {testCase.text}
                </div>
                
                <div className="border-t pt-4">
                  <p className="text-sm text-gray-600 mb-2">Resultado renderizado:</p>
                  <div className="p-4 bg-blue-50 rounded">
                    {parsed.content}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Tipo detectado: <span className="font-semibold">{parsed.type}</span>
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Instrucciones */}
        <div className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-2">📝 Instrucciones de verificación:</h3>
          <ol className="list-decimal list-inside space-y-1 text-sm">
            <li>Verifica que las imágenes se muestren correctamente en cada caso</li>
            <li>Si ves "[Error cargando imagen...]", verifica que el archivo existe en public/mathimg/</li>
            <li>Abre la consola del navegador (F12) para ver mensajes de error detallados</li>
            <li>Revisa la pestaña Network para ver qué URLs está intentando cargar</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
