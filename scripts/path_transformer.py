#!/usr/bin/env python3
"""
Path Transformer Script - ICFES Leveling System

Este script es CRÍTICO para el funcionamiento del sistema de imágenes.
Transforma rutas absolutas hardcodeadas del Excel a rutas relativas
funcionales para el sistema de multimedia.

Funciones principales:
1. Normalizar rutas de C:/Users/natus/... a database/allquestions/...
2. Validar existencia física de archivos
3. Generar reportes de integridad
4. Limpiar y estandarizar nombres de archivos

Author: Claude Code Assistant
Date: 2024
"""

import argparse
import os
import sys
import logging
import pandas as pd
import unicodedata
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json
from collections import defaultdict

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PathTransformer:
    """
    Clase principal para transformar rutas de imágenes del Excel ICFES
    """
    
    def __init__(self, project_root: str = None):
        """
        Inicializar el transformador de rutas
        
        Args:
            project_root: Ruta raíz del proyecto (opcional)
        """
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            # Auto-detectar la raíz del proyecto
            current_dir = Path(__file__).parent.parent
            self.project_root = current_dir.resolve()
            
        self.base_media_path = self.project_root / "database" / "allquestions"
        
        # Patrones de mapeo por materia (según roadmap)
        self.subject_patterns = {
            'matematicas': 'database/allquestions/Matematicas/Imagenes_Matematicas/',
            'ciencias_naturales': 'database/allquestions/Ciencias Naturales/imagenes/',
            'ciencias_sociales': 'database/allquestions/Ciencias Sociales/imagenes_ciencias_sociales/',
            'lectura_critica': 'database/allquestions/Lectura Critica/Imagenes_Lectura_Critica/',
            'ingles': 'database/allquestions/Ingles/imagenes/',
        }
        
        # Estadísticas del procesamiento
        self.stats = {
            'total_processed': 0,
            'successful_transforms': 0,
            'failed_transforms': 0,
            'files_found': 0,
            'files_missing': 0,
            'duplicates_found': 0
        }
        
        logger.info(f"PathTransformer inicializado con raíz: {self.project_root}")
        logger.info(f"Base media path: {self.base_media_path}")

    def normalize_unicode(self, text: str) -> str:
        """
        Normalizar texto Unicode a NFC según roadmap
        
        Args:
            text: Texto a normalizar
            
        Returns:
            Texto normalizado
        """
        if not text or pd.isna(text):
            return ""
        
        # Normalización Unicode NFC
        normalized = unicodedata.normalize('NFC', str(text))
        
        # Trim whitespace
        normalized = normalized.strip()
        
        return normalized

    def sanitize_path_component(self, component: str, is_filename: bool = False) -> str:
        """
        Sanitizar componente de ruta según roadmap
        
        Args:
            component: Componente de ruta a sanitizar
            is_filename: Si es True, mantiene el nombre de archivo original
            
        Returns:
            Componente sanitizado
        """
        if not component:
            return ""
        
        # Normalizar Unicode
        sanitized = self.normalize_unicode(component)
        
        # Colapsar separadores múltiples
        sanitized = re.sub(r'[/\\]+', '/', sanitized)
        
        if not is_filename:
            # Para directorios: lowercase
            sanitized = sanitized.lower()
        
        # Sustituir caracteres problemáticos en Windows [:*?"<>|]
        sanitized = re.sub(r'[:*?"<>|]', '_', sanitized)
        
        # Remover barras al inicio/final
        sanitized = sanitized.strip('/')
        
        return sanitized

    def detect_subject_from_path(self, path: str) -> Optional[str]:
        """
        Detectar materia basada en la ruta
        
        Args:
            path: Ruta a analizar
            
        Returns:
            Nombre de la materia detectada o None
        """
        path_lower = path.lower()
        
        # Patrones de detección por materia
        patterns = {
            'matematicas': ['matematica', 'math', 'mat_'],
            'ciencias_naturales': ['ciencias naturales', 'naturales', 'biologia', 'quimica', 'fisica'],
            'ciencias_sociales': ['ciencias sociales', 'sociales', 'historia', 'geografia'],
            'lectura_critica': ['lectura critica', 'lectura crítica', 'lenguaje', 'español'],
            'ingles': ['ingles', 'inglés', 'english']
        }
        
        for subject, keywords in patterns.items():
            for keyword in keywords:
                if keyword in path_lower:
                    return subject
        
        return None

    def transform_path_to_relative(self, absolute_path: str) -> Tuple[str, bool, str]:
        """
        Transformar ruta absoluta a relativa según patrones del roadmap
        
        Args:
            absolute_path: Ruta absoluta del Excel
            
        Returns:
            Tuple: (ruta_relativa, existe_archivo, razon)
        """
        if not absolute_path or pd.isna(absolute_path):
            return "", False, "Ruta vacía o nula"
        
        try:
            # Normalizar la ruta
            path_str = self.normalize_unicode(str(absolute_path))
            
            # Detectar materia
            subject = self.detect_subject_from_path(path_str)
            
            if not subject:
                logger.warning(f"No se pudo detectar materia para: {path_str}")
                return "", False, "Materia no detectada"
            
            # Extraer nombre de archivo
            filename = Path(path_str).name
            if not filename:
                return "", False, "Nombre de archivo no encontrado"
            
            # Sanitizar nombre de archivo
            sanitized_filename = self.sanitize_path_component(filename, is_filename=True)
            
            # Construir ruta relativa usando patrones del roadmap
            base_pattern = self.subject_patterns.get(subject, f"database/allquestions/{subject.title()}/imagenes/")
            relative_path = f"{base_pattern}{sanitized_filename}"
            
            # Verificar existencia física
            full_physical_path = self.project_root / relative_path
            file_exists = full_physical_path.exists()
            
            # Si no existe, buscar en subdirectorios
            if not file_exists:
                relative_path, file_exists = self._find_file_in_subdirs(subject, sanitized_filename)
            
            reason = "Archivo encontrado" if file_exists else "Archivo no encontrado físicamente"
            
            self.stats['successful_transforms'] += 1
            if file_exists:
                self.stats['files_found'] += 1
            else:
                self.stats['files_missing'] += 1
                
            return relative_path, file_exists, reason
            
        except Exception as e:
            logger.error(f"Error transformando ruta {absolute_path}: {str(e)}")
            self.stats['failed_transforms'] += 1
            return "", False, f"Error: {str(e)}"

    def _find_file_in_subdirs(self, subject: str, filename: str) -> Tuple[str, bool]:
        """
        Buscar archivo en subdirectorios de la materia
        
        Args:
            subject: Nombre de la materia
            filename: Nombre del archivo a buscar
            
        Returns:
            Tuple: (ruta_relativa, encontrado)
        """
        subject_path = self.base_media_path / self._get_subject_dir(subject)
        
        if not subject_path.exists():
            return f"database/allquestions/{subject}/{filename}", False
        
        # Buscar recursivamente
        for file_path in subject_path.rglob(filename):
            # Construir ruta relativa desde project_root
            relative = file_path.relative_to(self.project_root)
            return str(relative).replace('\\', '/'), True
        
        # Buscar con nombre similar (case-insensitive)
        filename_lower = filename.lower()
        for file_path in subject_path.rglob("*"):
            if file_path.is_file() and file_path.name.lower() == filename_lower:
                relative = file_path.relative_to(self.project_root)
                return str(relative).replace('\\', '/'), True
        
        return f"database/allquestions/{subject}/{filename}", False

    def _get_subject_dir(self, subject: str) -> str:
        """
        Obtener directorio físico para una materia
        
        Args:
            subject: Nombre de la materia
            
        Returns:
            Nombre del directorio físico
        """
        mapping = {
            'matematicas': 'Matematicas',
            'ciencias_naturales': 'Ciencias Naturales', 
            'ciencias_sociales': 'Ciencias Sociales',
            'lectura_critica': 'Lectura Critica',
            'ingles': 'Ingles'
        }
        return mapping.get(subject, subject.title())

    def process_excel_file(self, excel_path: str, output_path: str = None, dry_run: bool = False) -> Dict:
        """
        Procesar archivo Excel completo transformando todas las rutas
        
        Args:
            excel_path: Ruta al archivo Excel
            output_path: Ruta de salida (opcional)
            dry_run: Si es True, no guarda cambios
            
        Returns:
            Diccionario con estadísticas del procesamiento
        """
        logger.info(f"Procesando Excel: {excel_path}")
        
        try:
            # Leer Excel
            df = pd.read_excel(excel_path)
            logger.info(f"Excel cargado: {len(df)} filas, {len(df.columns)} columnas")
            
            # Identificar columnas de imágenes
            image_columns = [col for col in df.columns if 
                           'imagen' in col.lower() or 
                           'url' in col.lower() or
                           col.lower().endswith('_url')]
            
            logger.info(f"Columnas de imágenes identificadas: {image_columns}")
            
            # Procesar cada columna de imagen
            transformation_report = defaultdict(list)
            
            for col in image_columns:
                logger.info(f"Procesando columna: {col}")
                
                for idx, original_path in enumerate(df[col]):
                    if pd.isna(original_path) or not original_path:
                        continue
                    
                    self.stats['total_processed'] += 1
                    
                    # Transformar ruta
                    relative_path, exists, reason = self.transform_path_to_relative(original_path)
                    
                    # Registrar transformación
                    transformation_report[col].append({
                        'row': idx + 2,  # +2 porque Excel empieza en 1 y tiene header
                        'original': str(original_path),
                        'transformed': relative_path,
                        'exists': exists,
                        'reason': reason
                    })
                    
                    # Actualizar DataFrame
                    if not dry_run and relative_path:
                        df.loc[idx, col] = relative_path
            
            # Guardar archivo modificado
            if not dry_run and output_path:
                df.to_excel(output_path, index=False)
                logger.info(f"Excel actualizado guardado en: {output_path}")
            elif not dry_run:
                # Sobrescribir archivo original
                df.to_excel(excel_path, index=False)
                logger.info(f"Excel original actualizado")
            
            # Generar reporte
            report = {
                'stats': self.stats,
                'transformations': dict(transformation_report),
                'excel_info': {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'image_columns': image_columns
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error procesando Excel: {str(e)}")
            raise

    def generate_integrity_report(self, excel_path: str) -> Dict:
        """
        Generar reporte de integridad de archivos sin modificar el Excel
        
        Args:
            excel_path: Ruta al archivo Excel
            
        Returns:
            Diccionario con reporte de integridad
        """
        logger.info(f"Generando reporte de integridad para: {excel_path}")
        
        report = self.process_excel_file(excel_path, dry_run=True)
        
        # Estadísticas adicionales
        missing_files = []
        found_files = []
        
        for col, transformations in report['transformations'].items():
            for trans in transformations:
                if trans['exists']:
                    found_files.append(trans)
                else:
                    missing_files.append(trans)
        
        report['integrity'] = {
            'total_image_references': len(found_files) + len(missing_files),
            'found_files': len(found_files),
            'missing_files': len(missing_files),
            'integrity_percentage': (len(found_files) / (len(found_files) + len(missing_files)) * 100) if (found_files or missing_files) else 0,
            'missing_details': missing_files[:10],  # Primeros 10 para no saturar
            'found_sample': found_files[:5]  # Muestra de encontrados
        }
        
        return report

    def save_report(self, report: Dict, output_path: str):
        """
        Guardar reporte en formato JSON
        
        Args:
            report: Diccionario con reporte
            output_path: Ruta donde guardar el reporte
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Reporte guardado en: {output_path}")


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Transformador de rutas ICFES - Convierte rutas absolutas a relativas"
    )
    
    parser.add_argument(
        '--excel', 
        required=True,
        help='Ruta al archivo Excel con rutas a transformar'
    )
    
    parser.add_argument(
        '--verify', 
        action='store_true',
        help='Solo verificar integridad sin modificar archivo'
    )
    
    parser.add_argument(
        '--inplace', 
        action='store_true',
        help='Modificar archivo Excel original'
    )
    
    parser.add_argument(
        '--out',
        help='Ruta de salida para Excel modificado'
    )
    
    parser.add_argument(
        '--project-root',
        help='Ruta raíz del proyecto (opcional, se autodetecta)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true', 
        help='Ejecutar sin hacer cambios (solo reportar)'
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.verify and not args.inplace and not args.out and not args.dry_run:
        parser.error("Debe especificar --verify, --inplace, --out, o --dry-run")
    
    if not Path(args.excel).exists():
        logger.error(f"Archivo Excel no encontrado: {args.excel}")
        sys.exit(1)
    
    # Inicializar transformador
    transformer = PathTransformer(args.project_root)
    
    try:
        if args.verify or args.dry_run:
            # Solo generar reporte
            logger.info("Modo verificación - generando reporte de integridad")
            report = transformer.generate_integrity_report(args.excel)
            
            # Guardar reporte
            report_path = args.excel.replace('.xlsx', '_integrity_report.json')
            transformer.save_report(report, report_path)
            
            # Mostrar estadísticas
            print("\n" + "="*50)
            print("REPORTE DE INTEGRIDAD")
            print("="*50)
            print(f"Total referencias de imagen: {report['integrity']['total_image_references']}")
            print(f"Archivos encontrados: {report['integrity']['found_files']}")
            print(f"Archivos faltantes: {report['integrity']['missing_files']}")
            print(f"Porcentaje de integridad: {report['integrity']['integrity_percentage']:.1f}%")
            print(f"Reporte detallado guardado en: {report_path}")
            
        else:
            # Procesar y transformar
            output_path = args.out if args.out else (args.excel if args.inplace else None)
            
            logger.info("Iniciando transformación de rutas")
            report = transformer.process_excel_file(
                args.excel, 
                output_path=output_path,
                dry_run=False
            )
            
            # Guardar reporte
            report_path = (output_path or args.excel).replace('.xlsx', '_transformation_report.json')
            transformer.save_report(report, report_path)
            
            # Mostrar estadísticas
            print("\n" + "="*50)
            print("TRANSFORMACIÓN COMPLETADA")
            print("="*50)
            print(f"Rutas procesadas: {report['stats']['total_processed']}")
            print(f"Transformaciones exitosas: {report['stats']['successful_transforms']}")
            print(f"Transformaciones fallidas: {report['stats']['failed_transforms']}")
            print(f"Archivos encontrados: {report['stats']['files_found']}")
            print(f"Archivos faltantes: {report['stats']['files_missing']}")
            print(f"Archivo Excel {'actualizado' if output_path else 'procesado'}")
            print(f"Reporte guardado en: {report_path}")
            
    except Exception as e:
        logger.error(f"Error ejecutando script: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()