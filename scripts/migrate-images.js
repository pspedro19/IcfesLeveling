const fs = require('fs');
const path = require('path');

// Configuración
const SOURCE_DIRS = [
  'C:\\Users\\PEDRO_PEREZ\\Documents\\IcfesLeveling\\mathimg',
  './mathimg',
  '../mathimg'
];

const TARGET_DIR = './apps/frontend/public/mathimg';

// Colores para la consola
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m'
};

console.log(`${colors.blue}🚀 Iniciando migración de imágenes...${colors.reset}\n`);

// Crear directorio destino si no existe
if (!fs.existsSync(TARGET_DIR)) {
  fs.mkdirSync(TARGET_DIR, { recursive: true });
  console.log(`${colors.green}✅ Directorio creado: ${TARGET_DIR}${colors.reset}`);
}

// Buscar directorio fuente que exista
let sourceDir = null;
for (const dir of SOURCE_DIRS) {
  if (fs.existsSync(dir)) {
    sourceDir = dir;
    console.log(`${colors.green}✅ Directorio fuente encontrado: ${sourceDir}${colors.reset}`);
    break;
  }
}

if (!sourceDir) {
  console.error(`${colors.red}❌ No se encontró ningún directorio fuente. Verifica las rutas.${colors.reset}`);
  process.exit(1);
}

// Función para copiar archivos
function copyImages() {
  const files = fs.readdirSync(sourceDir);
  let copiedCount = 0;
  let skippedCount = 0;
  let errorCount = 0;

  console.log(`\n${colors.blue}📁 Procesando ${files.length} archivos...${colors.reset}\n`);

  files.forEach(file => {
    if (file.match(/\.(png|jpg|jpeg|gif|svg)$/i)) {
      const sourcePath = path.join(sourceDir, file);
      const targetPath = path.join(TARGET_DIR, file);
      
      try {
        // Verificar si ya existe
        if (fs.existsSync(targetPath)) {
          const sourceStats = fs.statSync(sourcePath);
          const targetStats = fs.statSync(targetPath);
          
          if (sourceStats.size === targetStats.size) {
            console.log(`${colors.yellow}⏭️  Omitido (ya existe): ${file}${colors.reset}`);
            skippedCount++;
            return;
          }
        }
        
        // Copiar archivo
        fs.copyFileSync(sourcePath, targetPath);
        console.log(`${colors.green}✅ Copiado: ${file}${colors.reset}`);
        copiedCount++;
        
      } catch (error) {
        console.error(`${colors.red}❌ Error copiando ${file}: ${error.message}${colors.reset}`);
        errorCount++;
      }
    }
  });

  // Resumen
  console.log(`\n${colors.blue}📊 Resumen de migración:${colors.reset}`);
  console.log(`${colors.green}✅ Archivos copiados: ${copiedCount}${colors.reset}`);
  console.log(`${colors.yellow}⏭️  Archivos omitidos: ${skippedCount}${colors.reset}`);
  console.log(`${colors.red}❌ Errores: ${errorCount}${colors.reset}`);
  
  // Verificar estructura final
  const finalFiles = fs.readdirSync(TARGET_DIR);
  console.log(`\n${colors.blue}📁 Total de imágenes en ${TARGET_DIR}: ${finalFiles.length}${colors.reset}`);
}

// Función para verificar imágenes faltantes del CSV
function checkMissingImages() {
  console.log(`\n${colors.blue}🔍 Verificando imágenes requeridas por el CSV...${colors.reset}\n`);
  
  try {
    // Leer el CSV
    const csvPath = './paste.txt';
    if (!fs.existsSync(csvPath)) {
      console.log(`${colors.yellow}⚠️  No se encontró paste.txt para verificar${colors.reset}`);
      return;
    }
    
    const csvContent = fs.readFileSync(csvPath, 'utf8');
    const imageUrls = new Set();
    
    // Extraer todas las URLs de imágenes del CSV
    const matches = csvContent.match(/\/mathimg\/[^\s,]+\.png/g);
    if (matches) {
      matches.forEach(url => imageUrls.add(url));
    }
    
    // Verificar qué imágenes faltan
    const missingImages = [];
    imageUrls.forEach(url => {
      const filename = path.basename(url);
      const filepath = path.join(TARGET_DIR, filename);
      if (!fs.existsSync(filepath)) {
        missingImages.push(filename);
      }
    });
    
    if (missingImages.length > 0) {
      console.log(`${colors.red}❌ Imágenes faltantes (${missingImages.length}):${colors.reset}`);
      missingImages.forEach(img => console.log(`   - ${img}`));
    } else {
      console.log(`${colors.green}✅ Todas las imágenes requeridas están presentes${colors.reset}`);
    }
    
  } catch (error) {
    console.error(`${colors.red}Error verificando CSV: ${error.message}${colors.reset}`);
  }
}

// Ejecutar migración
copyImages();
checkMissingImages();

console.log(`\n${colors.green}✨ Migración completada${colors.reset}`);
console.log(`\n${colors.blue}💡 Siguiente paso: npm run dev en apps/frontend${colors.reset}\n`);
