#!/usr/bin/env python3
"""
Verify Assets Script - ICFES Leveling System

Script para verificar la integridad completa de todos los assets multimedia
del sistema ICFES. Genera reportes detallados de archivos faltantes,
optimizaciones necesarias y salud general del sistema multimedia.

Funciones principales:
1. Verificar integridad de todas las imágenes referenciadas
2. Detectar archivos huérfanos (físicos sin referencia en BD)
3. Identificar archivos que necesitan optimización
4. Generar reportes CSV/JSON detallados
5. Crear placeholders automáticamente para archivos faltantes

Author: Claude Code Assistant  
Date: 2024
"""

import argparse
import os
import sys
import logging
import pandas as pd
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import json
import csv
from datetime import datetime
from PIL import Image
import mimetypes
from collections import defaultdict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AssetVerifier:
    """
    Clase principal para verificar integridad de assets multimedia
    """
    
    def __init__(self, project_root: str = None):
        """
        Inicializar verificador de assets
        
        Args:
            project_root: Ruta raíz del proyecto (opcional)
        """
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(__file__).parent.parent.resolve()
            
        self.base_media_path = self.project_root / "database" / "allquestions"
        self.placeholders_path = self.base_media_path / "placeholders"
        
        # Formatos soportados según roadmap
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf'}
        self.image_formats = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        
        # Límites según roadmap
        self.min_dimensions = (256, 256)  # Mínimo 256x256
        self.max_file_size = 1.5 * 1024 * 1024  # 1.5 MB recomendado
        self.optimization_threshold = 500 * 1024  # 500 KB para WebP
        
        # Estadísticas
        self.stats = {
            'total_references': 0,
            'files_found': 0,
            'files_missing': 0,
            'files_oversized': 0,
            'files_undersized': 0,
            'files_need_optimization': 0,
            'orphaned_files': 0,
            'placeholders_created': 0,
            'integrity_percentage': 0.0
        }
        
        # Caches para evitar procesamiento duplicado
        self.file_cache = {}
        self.dimension_cache = {}
        
        logger.info(f"AssetVerifier inicializado")
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"Base media path: {self.base_media_path}")

    def get_file_info(self, file_path: Path) -> Dict:
        """
        Obtener información completa de un archivo
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Diccionario con información del archivo
        """
        if str(file_path) in self.file_cache:
            return self.file_cache[str(file_path)]
        
        info = {
            'exists': False,
            'size': 0,
            'format': '',
            'dimensions': (0, 0),
            'is_image': False,
            'is_pdf': False,
            'mime_type': '',
            'needs_optimization': False,
            'is_undersized': False,
            'is_oversized': False,
            'error': None
        }
        
        try:
            if not file_path.exists():
                info['error'] = 'File not found'
                return info
            
            info['exists'] = True
            info['size'] = file_path.stat().st_size
            info['format'] = file_path.suffix.lower()
            info['mime_type'] = mimetypes.guess_type(str(file_path))[0] or 'unknown'
            
            # Verificar si es imagen
            if info['format'] in self.image_formats:
                info['is_image'] = True
                
                try:
                    with Image.open(file_path) as img:
                        info['dimensions'] = img.size
                        
                        # Verificar dimensiones mínimas
                        if (img.width < self.min_dimensions[0] or 
                            img.height < self.min_dimensions[1]):
                            info['is_undersized'] = True
                        
                        # Verificar si necesita optimización
                        if (info['size'] > self.optimization_threshold and 
                            info['format'] != '.webp'):
                            info['needs_optimization'] = True
                        
                        # Verificar tamaño máximo recomendado
                        if info['size'] > self.max_file_size:
                            info['is_oversized'] = True
                            
                except Exception as img_error:
                    info['error'] = f'Image processing error: {str(img_error)}'
                    
            elif info['format'] == '.pdf':
                info['is_pdf'] = True
                # Para PDFs, consideramos que siempre necesitan miniatura si son grandes
                if info['size'] > self.max_file_size:
                    info['needs_optimization'] = True
                    info['is_oversized'] = True
        
        except Exception as e:
            info['error'] = f'General error: {str(e)}'
        
        # Cache result
        self.file_cache[str(file_path)] = info
        return info

    def extract_image_references_from_excel(self, excel_path: str) -> List[Dict]:
        """
        Extraer todas las referencias de imágenes del Excel
        
        Args:
            excel_path: Ruta al archivo Excel
            
        Returns:
            Lista de diccionarios con referencias de imágenes
        """
        logger.info(f"Extrayendo referencias de: {excel_path}")
        
        try:
            df = pd.read_excel(excel_path)
            logger.info(f"Excel cargado: {len(df)} filas")
            
            # Identificar columnas de imágenes
            image_columns = [col for col in df.columns if 
                           'imagen' in col.lower() or 
                           'url' in col.lower() and col.lower().endswith('_url')]
            
            logger.info(f"Columnas de imagen: {image_columns}")
            
            references = []
            
            for idx, row in df.iterrows():
                for col in image_columns:
                    image_path = row.get(col, '')
                    
                    if pd.notna(image_path) and image_path:
                        references.append({
                            'row': idx + 2,  # +2 por header y índice base-1
                            'column': col,
                            'original_path': str(image_path),
                            'subject': row.get('Área_Evaluada', 'Unknown'),
                            'question_id': row.get('ID_Pregunta', f'row_{idx}'),
                            'question_text': str(row.get('Pregunta', ''))[:100] + '...' if len(str(row.get('Pregunta', ''))) > 100 else str(row.get('Pregunta', ''))
                        })
            
            self.stats['total_references'] = len(references)
            logger.info(f"Referencias extraídas: {len(references)}")
            
            return references
            
        except Exception as e:
            logger.error(f"Error extrayendo referencias: {str(e)}")
            raise

    def transform_path_to_physical(self, original_path: str) -> Optional[Path]:
        """
        Transformar ruta del Excel a ruta física usando patrones conocidos
        
        Args:
            original_path: Ruta original del Excel
            
        Returns:
            Path físico o None si no se puede determinar
        """
        if not original_path:
            return None
        
        try:
            # Detectar materia del path
            path_lower = original_path.lower()
            
            # Extraer nombre de archivo
            filename = Path(original_path).name
            
            # Mapear a estructura física según análisis previo
            if 'matematica' in path_lower:
                return self.base_media_path / "Matematicas" / "Imagenes_Matematicas" / filename
            elif 'ciencias naturales' in path_lower or 'naturales' in path_lower:
                return self.base_media_path / "Ciencias Naturales" / "imagenes" / filename
            elif 'ciencias sociales' in path_lower or 'sociales' in path_lower:
                return self.base_media_path / "Ciencias Sociales" / filename
            elif 'lectura' in path_lower:
                return self.base_media_path / "Lectura Critica" / filename
            elif 'ingles' in path_lower:
                return self.base_media_path / "Ingles" / filename
            else:
                # Buscar en todas las carpetas
                return self._find_file_by_name(filename)
        
        except Exception as e:
            logger.debug(f"Error transformando path {original_path}: {str(e)}")
            return None

    def _find_file_by_name(self, filename: str) -> Optional[Path]:
        """
        Buscar archivo por nombre en toda la estructura
        
        Args:
            filename: Nombre del archivo a buscar
            
        Returns:
            Path si se encuentra, None si no
        """
        if not self.base_media_path.exists():
            return None
        
        # Búsqueda recursiva
        for file_path in self.base_media_path.rglob(filename):
            if file_path.is_file():
                return file_path
        
        # Búsqueda case-insensitive
        filename_lower = filename.lower()
        for file_path in self.base_media_path.rglob("*"):
            if file_path.is_file() and file_path.name.lower() == filename_lower:
                return file_path
        
        return None

    def find_orphaned_files(self, referenced_files: Set[Path]) -> List[Path]:
        """
        Encontrar archivos físicos sin referencia en el Excel
        
        Args:
            referenced_files: Set de archivos referenciados
            
        Returns:
            Lista de archivos huérfanos
        """
        logger.info("Buscando archivos huérfanos...")
        
        orphaned = []
        
        if not self.base_media_path.exists():
            logger.warning(f"Base media path no existe: {self.base_media_path}")
            return orphaned
        
        # Recorrer todos los archivos físicos
        for file_path in self.base_media_path.rglob("*"):
            if (file_path.is_file() and 
                file_path.suffix.lower() in self.supported_formats and
                file_path not in referenced_files and
                'placeholder' not in str(file_path).lower()):
                orphaned.append(file_path)
        
        logger.info(f"Archivos huérfanos encontrados: {len(orphaned)}")
        return orphaned

    def verify_all_references(self, references: List[Dict]) -> List[Dict]:
        """
        Verificar todas las referencias de imágenes
        
        Args:
            references: Lista de referencias extraídas del Excel
            
        Returns:
            Lista de referencias con información de verificación
        """
        logger.info(f"Verificando {len(references)} referencias...")
        
        verified_references = []
        referenced_files = set()
        
        for i, ref in enumerate(references):
            # Transformar ruta a física
            physical_path = self.transform_path_to_physical(ref['original_path'])
            
            verification = {
                **ref,
                'physical_path': str(physical_path) if physical_path else None,
                'file_info': None,
                'status': 'not_found'
            }
            
            if physical_path:
                referenced_files.add(physical_path)
                file_info = self.get_file_info(physical_path)
                verification['file_info'] = file_info
                
                if file_info['exists']:
                    verification['status'] = 'found'
                    self.stats['files_found'] += 1
                    
                    # Clasificar problemas
                    if file_info['is_oversized']:
                        self.stats['files_oversized'] += 1
                    if file_info['is_undersized']:
                        self.stats['files_undersized'] += 1
                    if file_info['needs_optimization']:
                        self.stats['files_need_optimization'] += 1
                else:
                    self.stats['files_missing'] += 1
            else:
                self.stats['files_missing'] += 1
            
            verified_references.append(verification)
            
            # Log progreso
            if (i + 1) % 100 == 0:
                logger.info(f"Progreso: {i + 1}/{len(references)} referencias verificadas")
        
        # Encontrar huérfanos
        orphaned_files = self.find_orphaned_files(referenced_files)
        self.stats['orphaned_files'] = len(orphaned_files)
        
        # Calcular porcentaje de integridad
        if self.stats['total_references'] > 0:
            self.stats['integrity_percentage'] = (
                self.stats['files_found'] / self.stats['total_references']
            ) * 100
        
        return verified_references

    def create_placeholder(self, missing_path: Path, subject: str, image_type: str) -> bool:
        """
        Crear placeholder para imagen faltante
        
        Args:
            missing_path: Ruta donde debería estar el archivo
            subject: Materia de la pregunta
            image_type: Tipo de imagen (question, option_a, etc.)
            
        Returns:
            True si se creó exitosamente
        """
        try:
            # Asegurar que existe directorio de destino
            missing_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Buscar placeholder apropiado
            placeholder_name = f"placeholder_{subject.lower().replace(' ', '_')}_{image_type}.png"
            placeholder_source = self.placeholders_path / placeholder_name
            
            # Fallback a placeholder genérico
            if not placeholder_source.exists():
                placeholder_source = self.placeholders_path / f"placeholder_{image_type}.png"
            
            # Fallback final
            if not placeholder_source.exists():
                placeholder_source = self.placeholders_path / "placeholder_question.png"
            
            # Copiar placeholder si existe
            if placeholder_source.exists():
                import shutil
                shutil.copy2(placeholder_source, missing_path)
                self.stats['placeholders_created'] += 1
                logger.debug(f"Placeholder creado: {missing_path}")
                return True
            else:
                logger.warning(f"No se encontró placeholder para: {placeholder_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error creando placeholder para {missing_path}: {str(e)}")
            return False

    def generate_reports(self, verified_references: List[Dict], output_dir: str):
        """
        Generar reportes detallados de verificación
        
        Args:
            verified_references: Referencias verificadas
            output_dir: Directorio de salida para reportes
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Reporte de archivos faltantes
        missing_files = [ref for ref in verified_references if ref['status'] == 'not_found']
        if missing_files:
            missing_csv_path = output_path / f"missing_images_{timestamp}.csv"
            self._save_csv_report(missing_files, missing_csv_path, [
                'row', 'column', 'original_path', 'physical_path', 
                'subject', 'question_id', 'question_text'
            ])
            logger.info(f"Reporte de faltantes guardado: {missing_csv_path}")
        
        # 2. Reporte de archivos que necesitan optimización
        need_optimization = [
            ref for ref in verified_references 
            if ref['status'] == 'found' and ref['file_info']['needs_optimization']
        ]
        if need_optimization:
            optimization_csv_path = output_path / f"optimization_needed_{timestamp}.csv"
            self._save_optimization_report(need_optimization, optimization_csv_path)
            logger.info(f"Reporte de optimización guardado: {optimization_csv_path}")
        
        # 3. Reporte de archivos con problemas de tamaño
        size_problems = [
            ref for ref in verified_references
            if ref['status'] == 'found' and (
                ref['file_info']['is_oversized'] or ref['file_info']['is_undersized']
            )
        ]
        if size_problems:
            size_csv_path = output_path / f"size_problems_{timestamp}.csv"
            self._save_size_report(size_problems, size_csv_path)
            logger.info(f"Reporte de tamaños guardado: {size_csv_path}")
        
        # 4. Reporte maestro JSON
        master_report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_references': len(verified_references),
                'verification_stats': self.stats
            },
            'summary': {
                'integrity_percentage': self.stats['integrity_percentage'],
                'files_found': self.stats['files_found'],
                'files_missing': self.stats['files_missing'],
                'optimization_needed': len(need_optimization),
                'size_problems': len(size_problems)
            },
            'detailed_results': verified_references[:100]  # Limitar para no saturar
        }
        
        master_json_path = output_path / f"asset_verification_report_{timestamp}.json"
        with open(master_json_path, 'w', encoding='utf-8') as f:
            json.dump(master_report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Reporte maestro guardado: {master_json_path}")

    def _save_csv_report(self, data: List[Dict], file_path: Path, columns: List[str]):
        """Guardar reporte CSV"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)

    def _save_optimization_report(self, data: List[Dict], file_path: Path):
        """Guardar reporte de optimización"""
        columns = ['original_path', 'physical_path', 'current_size_mb', 
                  'format', 'dimensions', 'recommended_action']
        
        processed_data = []
        for item in data:
            info = item['file_info']
            processed_data.append({
                'original_path': item['original_path'],
                'physical_path': item['physical_path'],
                'current_size_mb': round(info['size'] / (1024*1024), 2),
                'format': info['format'],
                'dimensions': f"{info['dimensions'][0]}x{info['dimensions'][1]}" if info['dimensions'] != (0,0) else 'N/A',
                'recommended_action': 'Convert to WebP' if info['format'] != '.webp' else 'Compress'
            })
        
        self._save_csv_report(processed_data, file_path, columns)

    def _save_size_report(self, data: List[Dict], file_path: Path):
        """Guardar reporte de problemas de tamaño"""
        columns = ['original_path', 'physical_path', 'size_mb', 
                  'dimensions', 'problem_type', 'recommendation']
        
        processed_data = []
        for item in data:
            info = item['file_info']
            problem_type = []
            if info['is_oversized']:
                problem_type.append('oversized')
            if info['is_undersized']:
                problem_type.append('undersized')
            
            processed_data.append({
                'original_path': item['original_path'],
                'physical_path': item['physical_path'],
                'size_mb': round(info['size'] / (1024*1024), 2),
                'dimensions': f"{info['dimensions'][0]}x{info['dimensions'][1]}" if info['dimensions'] != (0,0) else 'N/A',
                'problem_type': ', '.join(problem_type),
                'recommendation': 'Resize and optimize' if info['is_oversized'] else 'Check if image is complete'
            })
        
        self._save_csv_report(processed_data, file_path, columns)


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Verificador de integridad de assets multimedia ICFES"
    )
    
    parser.add_argument(
        '--excel',
        required=True,
        help='Ruta al archivo Excel con referencias de imágenes'
    )
    
    parser.add_argument(
        '--output-dir',
        default='reports',
        help='Directorio para guardar reportes (default: reports)'
    )
    
    parser.add_argument(
        '--create-placeholders',
        action='store_true',
        help='Crear placeholders para archivos faltantes'
    )
    
    parser.add_argument(
        '--project-root',
        help='Ruta raíz del proyecto (opcional)'
    )
    
    args = parser.parse_args()
    
    # Validar archivo Excel
    if not Path(args.excel).exists():
        logger.error(f"Archivo Excel no encontrado: {args.excel}")
        sys.exit(1)
    
    # Inicializar verificador
    verifier = AssetVerifier(args.project_root)
    
    try:
        # Extraer referencias
        references = verifier.extract_image_references_from_excel(args.excel)
        
        if not references:
            logger.warning("No se encontraron referencias de imágenes en el Excel")
            return
        
        # Verificar referencias
        verified_references = verifier.verify_all_references(references)
        
        # Crear placeholders si se solicitó
        if args.create_placeholders:
            logger.info("Creando placeholders para archivos faltantes...")
            for ref in verified_references:
                if ref['status'] == 'not_found' and ref['physical_path']:
                    # Determinar tipo de imagen
                    column = ref['column'].lower()
                    if 'pregunta' in column:
                        image_type = 'question'
                    elif 'opcion_a' in column:
                        image_type = 'option_a'
                    elif 'opcion_b' in column:
                        image_type = 'option_b'
                    elif 'opcion_c' in column:
                        image_type = 'option_c'
                    elif 'opcion_d' in column:
                        image_type = 'option_d'
                    else:
                        image_type = 'question'
                    
                    verifier.create_placeholder(
                        Path(ref['physical_path']),
                        ref['subject'],
                        image_type
                    )
        
        # Generar reportes
        verifier.generate_reports(verified_references, args.output_dir)
        
        # Mostrar estadísticas finales
        print("\n" + "="*60)
        print("VERIFICACIÓN DE ASSETS COMPLETADA")
        print("="*60)
        print(f"Total referencias: {verifier.stats['total_references']}")
        print(f"Archivos encontrados: {verifier.stats['files_found']}")
        print(f"Archivos faltantes: {verifier.stats['files_missing']}")
        print(f"Archivos huérfanos: {verifier.stats['orphaned_files']}")
        print(f"Archivos sobrepeso: {verifier.stats['files_oversized']}")
        print(f"Archivos muy pequeños: {verifier.stats['files_undersized']}")
        print(f"Necesitan optimización: {verifier.stats['files_need_optimization']}")
        if args.create_placeholders:
            print(f"Placeholders creados: {verifier.stats['placeholders_created']}")
        print(f"Porcentaje de integridad: {verifier.stats['integrity_percentage']:.1f}%")
        print(f"Reportes guardados en: {args.output_dir}")
        
        # Recomendaciones
        if verifier.stats['integrity_percentage'] < 80:
            print("\n⚠️  ACCIÓN REQUERIDA:")
            print("   La integridad es baja. Revisar reportes y corregir rutas.")
        elif verifier.stats['files_need_optimization'] > 10:
            print("\n💡 RECOMENDACIÓN:")
            print("   Considerar optimizar imágenes para mejorar rendimiento.")
        else:
            print("\n✅ ESTADO BUENO:")
            print("   La integridad de assets es aceptable.")
            
    except Exception as e:
        logger.error(f"Error ejecutando verificación: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()