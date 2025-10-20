#!/usr/bin/env python3
"""
Script to analyze file sizes and optimization opportunities
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

def format_size(size_bytes):
    """Format size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def analyze_file_optimization():
    base_path = r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\database\allquestions"
    
    print("ANÁLISIS DE OPTIMIZACIÓN DE ARCHIVOS MULTIMEDIA")
    print("="*80)
    
    # Dictionaries to store analysis results
    image_stats = defaultdict(lambda: {
        'count': 0, 
        'total_size': 0, 
        'files': [], 
        'large_files': [],
        'formats': defaultdict(int)
    })
    
    pdf_stats = defaultdict(lambda: {
        'count': 0, 
        'total_size': 0, 
        'files': [], 
        'large_files': []
    })
    
    # File extensions to analyze
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    pdf_extensions = {'.pdf'}
    
    # Size thresholds for optimization recommendations
    large_image_threshold = 500 * 1024  # 500KB
    large_pdf_threshold = 5 * 1024 * 1024  # 5MB
    
    total_files = 0
    total_size = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk(base_path):
        subject = None
        for part in Path(root).parts:
            if part in ['Matematicas', 'Ciencias Naturales', 'Ciencias Sociales', 'Lectura Critica', 'Ingles']:
                subject = part
                break
        
        if not subject:
            subject = 'Unknown'
        
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                file_ext = Path(file).suffix.lower()
                
                total_files += 1
                total_size += file_size
                
                if file_ext in image_extensions:
                    image_stats[subject]['count'] += 1
                    image_stats[subject]['total_size'] += file_size
                    image_stats[subject]['files'].append({
                        'name': file,
                        'path': file_path,
                        'size': file_size,
                        'size_formatted': format_size(file_size)
                    })
                    image_stats[subject]['formats'][file_ext] += 1
                    
                    if file_size > large_image_threshold:
                        image_stats[subject]['large_files'].append({
                            'name': file,
                            'path': file_path,
                            'size': file_size,
                            'size_formatted': format_size(file_size)
                        })
                
                elif file_ext in pdf_extensions:
                    pdf_stats[subject]['count'] += 1
                    pdf_stats[subject]['total_size'] += file_size
                    pdf_stats[subject]['files'].append({
                        'name': file,
                        'path': file_path,
                        'size': file_size,
                        'size_formatted': format_size(file_size)
                    })
                    
                    if file_size > large_pdf_threshold:
                        pdf_stats[subject]['large_files'].append({
                            'name': file,
                            'path': file_path,
                            'size': file_size,
                            'size_formatted': format_size(file_size)
                        })
            
            except OSError:
                continue
    
    # Print results
    print(f"RESUMEN GENERAL:")
    print(f"  Total de archivos analizados: {total_files}")
    print(f"  Tamaño total: {format_size(total_size)}")
    
    print(f"\nIMÁGENES POR MATERIA:")
    for subject in sorted(image_stats.keys()):
        stats = image_stats[subject]
        if stats['count'] > 0:
            print(f"\n  {subject}:")
            print(f"    Total imágenes: {stats['count']}")
            print(f"    Tamaño total: {format_size(stats['total_size'])}")
            print(f"    Tamaño promedio: {format_size(stats['total_size'] / stats['count']) if stats['count'] > 0 else 'N/A'}")
            
            # Format distribution
            print(f"    Formatos:")
            for fmt, count in stats['formats'].items():
                print(f"      {fmt}: {count} archivos")
            
            # Large files
            if stats['large_files']:
                print(f"    Archivos grandes (>{format_size(large_image_threshold)}):")
                for file_info in sorted(stats['large_files'], key=lambda x: x['size'], reverse=True)[:5]:
                    print(f"      {file_info['name']}: {file_info['size_formatted']}")
                if len(stats['large_files']) > 5:
                    print(f"      ... y {len(stats['large_files']) - 5} más")
    
    print(f"\nPDFs POR MATERIA:")
    for subject in sorted(pdf_stats.keys()):
        stats = pdf_stats[subject]
        if stats['count'] > 0:
            print(f"\n  {subject}:")
            print(f"    Total PDFs: {stats['count']}")
            print(f"    Tamaño total: {format_size(stats['total_size'])}")
            print(f"    Tamaño promedio: {format_size(stats['total_size'] / stats['count']) if stats['count'] > 0 else 'N/A'}")
            
            # Large files
            if stats['large_files']:
                print(f"    PDFs grandes (>{format_size(large_pdf_threshold)}):")
                for file_info in sorted(stats['large_files'], key=lambda x: x['size'], reverse=True):
                    print(f"      {file_info['name']}: {file_info['size_formatted']}")
    
    # Optimization recommendations
    print(f"\n" + "="*80)
    print(f"RECOMENDACIONES DE OPTIMIZACIÓN:")
    print(f"="*80)
    
    total_large_images = sum(len(stats['large_files']) for stats in image_stats.values())
    total_large_pdfs = sum(len(stats['large_files']) for stats in pdf_stats.values())
    
    if total_large_images > 0:
        print(f"1. OPTIMIZACIÓN DE IMÁGENES:")
        print(f"   - {total_large_images} imágenes exceden {format_size(large_image_threshold)}")
        print(f"   - Convertir PNG a WEBP puede reducir tamaño 50-80%")
        print(f"   - Implementar lazy loading para imágenes grandes")
        print(f"   - Considerar múltiples resoluciones (responsive images)")
    
    if total_large_pdfs > 0:
        print(f"\n2. OPTIMIZACIÓN DE PDFs:")
        print(f"   - {total_large_pdfs} PDFs exceden {format_size(large_pdf_threshold)}")
        print(f"   - Comprimir PDFs existentes")
        print(f"   - Extraer imágenes de PDFs y servirlas por separado")
        print(f"   - Implementar carga por demanda de PDFs")
    
    # Format analysis
    total_png = sum(stats['formats']['.png'] for stats in image_stats.values())
    total_jpg = sum(stats['formats']['.jpg'] + stats['formats']['.jpeg'] for stats in image_stats.values())
    
    print(f"\n3. OPTIMIZACIÓN DE FORMATOS:")
    print(f"   - PNG encontrados: {total_png}")
    print(f"   - JPG encontrados: {total_jpg}")
    print(f"   - Considerar WEBP para mejor compresión")
    print(f"   - Usar JPEG para fotografías, PNG para diagramas")
    
    # CDN readiness
    print(f"\n4. PREPARACIÓN PARA CDN:")
    print(f"   - Configurar headers de cache apropiados")
    print(f"   - Implementar ETags para validación de cache")
    print(f"   - Configurar compresión gzip/brotli")
    print(f"   - Establecer políticas de caché por tipo de contenido")
    
    return {
        'total_files': total_files,
        'total_size': total_size,
        'image_stats': dict(image_stats),
        'pdf_stats': dict(pdf_stats),
        'large_images': total_large_images,
        'large_pdfs': total_large_pdfs
    }

if __name__ == "__main__":
    analyze_file_optimization()