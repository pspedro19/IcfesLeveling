"""
Servicio de procesamiento multimedia para ICFES Leveling
Maneja imágenes, PDFs, videos y otros recursos multimedia
"""

import os
import hashlib
import mimetypes
from typing import Optional, Dict, List, Any
from pathlib import Path
import asyncio
from datetime import datetime
import aiofiles
from PIL import Image
import io
import base64
from fastapi import UploadFile, HTTPException
import cv2
import numpy as np
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.question import Question
from ..core.logging import logger

class MultimediaService:
    """Servicio completo para manejo de contenido multimedia"""
    
    def __init__(self):
        self.base_path = Path("/c/Users/HOME/Documents/icfes")
        self.mathimg_path = self.base_path / "IcfesLeveling" / "mathimg"
        self.dataimg_path = self.base_path / "dataimg"
        self.upload_path = self.base_path / "IcfesLeveling" / "uploads"
        self.cache_path = self.base_path / "IcfesLeveling" / "cache"
        
        # Crear directorios si no existen
        for path in [self.mathimg_path, self.upload_path, self.cache_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Configuración de procesamiento
        self.max_image_size = (1920, 1080)  # Máximo tamaño de imagen
        self.thumbnail_size = (300, 300)    # Tamaño de miniaturas
        self.supported_formats = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
            'video': ['.mp4', '.webm', '.avi', '.mov'],
            'document': ['.pdf', '.doc', '.docx'],
            'audio': ['.mp3', '.wav', '.ogg']
        }
    
    async def process_uploaded_file(
        self,
        file: UploadFile,
        category: str = "general",
        optimize: bool = True
    ) -> Dict[str, Any]:
        """
        Procesa un archivo subido y lo optimiza para web
        """
        try:
            # Validar tipo de archivo
            file_ext = Path(file.filename).suffix.lower()
            file_type = self._get_file_type(file_ext)
            
            if not file_type:
                raise HTTPException(400, f"Tipo de archivo no soportado: {file_ext}")
            
            # Generar nombre único
            file_hash = hashlib.md5(f"{file.filename}{datetime.now()}".encode()).hexdigest()
            safe_name = f"{file_hash}{file_ext}"
            
            # Determinar ruta de destino
            category_path = self.upload_path / category / file_type
            category_path.mkdir(parents=True, exist_ok=True)
            file_path = category_path / safe_name
            
            # Guardar archivo
            content = await file.read()
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Procesar según tipo
            result = {
                'original_name': file.filename,
                'stored_name': safe_name,
                'file_type': file_type,
                'category': category,
                'path': str(file_path.relative_to(self.base_path)),
                'size': len(content),
                'uploaded_at': datetime.now().isoformat()
            }
            
            if file_type == 'image' and optimize:
                optimization_result = await self.optimize_image(file_path)
                result.update(optimization_result)
            elif file_type == 'video':
                video_info = await self.process_video(file_path)
                result.update(video_info)
            elif file_type == 'document' and file_ext == '.pdf':
                pdf_info = await self.process_pdf(file_path)
                result.update(pdf_info)
            
            return result
            
        except Exception as e:
            logger.error(f"Error procesando archivo: {str(e)}")
            raise HTTPException(500, f"Error procesando archivo: {str(e)}")
    
    async def optimize_image(self, image_path: Path) -> Dict[str, Any]:
        """
        Optimiza una imagen para web
        """
        try:
            with Image.open(image_path) as img:
                # Obtener información original
                original_size = img.size
                original_format = img.format
                
                # Convertir a RGB si es necesario
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img
                
                # Redimensionar si es muy grande
                if img.size[0] > self.max_image_size[0] or img.size[1] > self.max_image_size[1]:
                    img.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
                
                # Crear thumbnail
                thumbnail = img.copy()
                thumbnail.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # Guardar versión optimizada
                optimized_path = image_path.parent / f"optimized_{image_path.name}"
                img.save(optimized_path, 'JPEG', quality=85, optimize=True)
                
                # Guardar thumbnail
                thumb_path = image_path.parent / f"thumb_{image_path.name}"
                thumbnail.save(thumb_path, 'JPEG', quality=75, optimize=True)
                
                return {
                    'original_dimensions': original_size,
                    'optimized_dimensions': img.size,
                    'thumbnail_path': str(thumb_path.relative_to(self.base_path)),
                    'optimized_path': str(optimized_path.relative_to(self.base_path)),
                    'optimization_ratio': round(
                        os.path.getsize(optimized_path) / os.path.getsize(image_path), 2
                    )
                }
                
        except Exception as e:
            logger.error(f"Error optimizando imagen: {str(e)}")
            return {'optimization_error': str(e)}
    
    async def process_video(self, video_path: Path) -> Dict[str, Any]:
        """
        Procesa un video y extrae información
        """
        try:
            cap = cv2.VideoCapture(str(video_path))
            
            # Obtener información del video
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            # Extraer thumbnail del primer frame
            ret, frame = cap.read()
            if ret:
                thumb_path = video_path.parent / f"thumb_{video_path.stem}.jpg"
                cv2.imwrite(str(thumb_path), frame)
            
            cap.release()
            
            return {
                'video_info': {
                    'duration': round(duration, 2),
                    'fps': fps,
                    'resolution': f"{width}x{height}",
                    'frame_count': frame_count,
                    'thumbnail': str(thumb_path.relative_to(self.base_path)) if ret else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error procesando video: {str(e)}")
            return {'video_error': str(e)}
    
    async def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Procesa un PDF y extrae información
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            
            # Extraer texto de la primera página
            first_page_text = ""
            if page_count > 0:
                page = doc[0]
                first_page_text = page.get_text()[:500]  # Primeros 500 caracteres
            
            # Crear thumbnail de la primera página
            if page_count > 0:
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))  # 50% del tamaño
                thumb_path = pdf_path.parent / f"thumb_{pdf_path.stem}.jpg"
                pix.save(str(thumb_path))
            
            doc.close()
            
            return {
                'pdf_info': {
                    'page_count': page_count,
                    'preview_text': first_page_text,
                    'thumbnail': str(thumb_path.relative_to(self.base_path)) if page_count > 0 else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error procesando PDF: {str(e)}")
            return {'pdf_error': str(e)}
    
    def _get_file_type(self, extension: str) -> Optional[str]:
        """
        Determina el tipo de archivo basado en la extensión
        """
        for file_type, extensions in self.supported_formats.items():
            if extension in extensions:
                return file_type
        return None
    
    async def get_question_images(self, db: Session, question_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las imágenes asociadas a una pregunta
        """
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return []
        
        images = []
        
        # Imagen principal de la pregunta
        if question.image_url:
            images.append({
                'type': 'question',
                'url': question.image_url,
                'alt': f"Pregunta {question_id}"
            })
        
        # Imágenes de opciones (si las hay en el JSON)
        if question.options:
            for i, option in enumerate(question.options):
                if isinstance(option, dict) and 'image' in option:
                    images.append({
                        'type': 'option',
                        'index': i,
                        'url': option['image'],
                        'alt': f"Opción {chr(65 + i)}"
                    })
        
        # Procesar URLs para asegurar rutas correctas
        for img in images:
            img['full_path'] = self._resolve_image_path(img['url'])
            img['exists'] = os.path.exists(img['full_path'])
        
        return images
    
    def _resolve_image_path(self, url: str) -> str:
        """
        Resuelve la ruta completa de una imagen
        """
        if url.startswith('http'):
            return url
        
        # Intentar diferentes ubicaciones
        possible_paths = [
            self.mathimg_path / url,
            self.dataimg_path / url,
            self.upload_path / url,
            self.base_path / url
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return str(self.base_path / url)
    
    async def generate_image_manifest(self) -> Dict[str, Any]:
        """
        Genera un manifiesto de todas las imágenes disponibles
        """
        manifest = {
            'mathimg': [],
            'dataimg': [],
            'uploads': [],
            'total_count': 0,
            'total_size': 0
        }
        
        # Escanear mathimg
        if self.mathimg_path.exists():
            for img_file in self.mathimg_path.rglob('*'):
                if img_file.is_file() and img_file.suffix.lower() in self.supported_formats['image']:
                    size = img_file.stat().st_size
                    manifest['mathimg'].append({
                        'name': img_file.name,
                        'path': str(img_file.relative_to(self.mathimg_path)),
                        'size': size,
                        'modified': datetime.fromtimestamp(img_file.stat().st_mtime).isoformat()
                    })
                    manifest['total_size'] += size
        
        # Escanear dataimg
        if self.dataimg_path.exists():
            for img_file in self.dataimg_path.rglob('*'):
                if img_file.is_file() and img_file.suffix.lower() in self.supported_formats['image']:
                    size = img_file.stat().st_size
                    manifest['dataimg'].append({
                        'name': img_file.name,
                        'path': str(img_file.relative_to(self.dataimg_path)),
                        'size': size,
                        'modified': datetime.fromtimestamp(img_file.stat().st_mtime).isoformat()
                    })
                    manifest['total_size'] += size
        
        # Escanear uploads
        if self.upload_path.exists():
            for img_file in self.upload_path.rglob('*'):
                if img_file.is_file() and img_file.suffix.lower() in self.supported_formats['image']:
                    size = img_file.stat().st_size
                    manifest['uploads'].append({
                        'name': img_file.name,
                        'path': str(img_file.relative_to(self.upload_path)),
                        'size': size,
                        'modified': datetime.fromtimestamp(img_file.stat().st_mtime).isoformat()
                    })
                    manifest['total_size'] += size
        
        manifest['total_count'] = (
            len(manifest['mathimg']) + 
            len(manifest['dataimg']) + 
            len(manifest['uploads'])
        )
        
        return manifest
    
    async def cleanup_unused_images(self, db: Session) -> Dict[str, Any]:
        """
        Limpia imágenes no utilizadas en la base de datos
        """
        # Obtener todas las URLs de imágenes de la base de datos
        used_images = set()
        
        # Imágenes de preguntas
        questions = db.query(Question).filter(Question.image_url.isnot(None)).all()
        for q in questions:
            used_images.add(q.image_url)
        
        # Generar manifiesto
        manifest = await self.generate_image_manifest()
        
        # Identificar imágenes no utilizadas
        all_images = set()
        for category in ['mathimg', 'dataimg', 'uploads']:
            for img in manifest[category]:
                all_images.add(img['path'])
        
        unused_images = all_images - used_images
        
        return {
            'total_images': len(all_images),
            'used_images': len(used_images),
            'unused_images': len(unused_images),
            'unused_list': list(unused_images)[:100]  # Limitar a 100 para no sobrecargar
        }

# Instancia global del servicio
multimedia_service = MultimediaService()