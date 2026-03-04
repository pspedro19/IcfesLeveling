#!/usr/bin/env python3
"""
Script para cargar links de YouTube desde CSV
Carga el catálogo de videos educativos para ICFES
"""

import pandas as pd
import asyncio
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from database import get_db
from models.youtube_links import YouTubeLinks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeLinksLoader:
    def __init__(self):
        self.csv_path = "/app/01_icfes_youtube_catalog.csv"
        self.engine = None
        self.SessionLocal = None
        
    async def load_youtube_links(self):
        """Cargar links de YouTube desde CSV"""
        try:
            logger.info("🚀 Iniciando carga del catálogo de YouTube...")
            
            # Check if CSV exists
            if not os.path.exists(self.csv_path):
                logger.error(f"❌ CSV no encontrado en: {self.csv_path}")
                return False
            
            # Read CSV
            df = pd.read_csv(self.csv_path)
            logger.info(f"✅ CSV cargado: {len(df)} links encontrados")
            
            # Clean and prepare data
            df = self.clean_data(df)
            logger.info("✅ Datos limpiados y preparados")
            
            # Get database session
            db = next(get_db())
            
            # Create table if not exists
            await self.ensure_table_exists(db)
            
            # Insert data
            inserted_count = await self.insert_youtube_links(db, df)
            
            logger.info(f"✅ {inserted_count} links de YouTube insertados exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en el proceso de carga: {e}")
            return False
        finally:
            if 'db' in locals():
                db.close()
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpiar y preparar datos del CSV"""
        try:
            # Remove duplicates
            df = df.drop_duplicates(subset=['codigo_tema', 'youtube_url'])
            
            # Clean text fields
            df['codigo_tema'] = df['codigo_tema'].str.strip()
            df['area_evaluada'] = df['area_evaluada'].str.strip()
            df['tema_principal'] = df['tema_principal'].str.strip()
            df['canal_sugerido'] = df['canal_sugerido'].str.strip()
            df['query_sugerida'] = df['query_sugerida'].str.strip()
            df['youtube_url'] = df['youtube_url'].str.strip()
            
            # Extract YouTube ID from URL if possible
            df['youtube_id'] = df['youtube_url'].apply(self.extract_youtube_id)
            
            # Set default values for missing fields
            df['tipo_contenido'] = df.get('tipo_contenido', 'explicativo')
            df['nivel_dificultad'] = df.get('nivel_dificultad', 3)
            df['proceso_cognitivo'] = df.get('proceso_cognitivo', 'Comprender')
            df['contexto_aplicacion'] = df.get('contexto_aplicacion', 'Académico')
            df['calidad_score'] = df.get('calidad_score', 0.80)
            df['relevancia_score'] = df.get('relevancia_score', 0.85)
            df['tiempo_estimado_estudio'] = df.get('tiempo_estimado_estudio', 15)
            df['puntos_xp'] = df.get('puntos_xp', 50)
            df['orden_recomendacion'] = df.get('orden_recomendacion', 1)
            df['estado'] = df.get('estado', 'activo')
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error limpiando datos: {e}")
            raise
    
    def extract_youtube_id(self, url: str) -> str:
        """Extraer ID de YouTube de URL"""
        try:
            if 'youtube.com/watch?v=' in url:
                return url.split('v=')[1].split('&')[0]
            elif 'youtu.be/' in url:
                return url.split('youtu.be/')[1].split('?')[0]
            else:
                return None
        except Exception:
            return None
    
    async def ensure_table_exists(self, db):
        """Asegurar que la tabla existe"""
        try:
            # Check if table exists
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'youtube_links'
                );
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                logger.info("📋 Creando tabla youtube_links...")
                await db.execute(text("""
                    CREATE TABLE IF NOT EXISTS youtube_links (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        codigo_tema VARCHAR(10) NOT NULL,
                        area_evaluada VARCHAR(100) NOT NULL,
                        tema_principal TEXT NOT NULL,
                        canal_sugerido VARCHAR(100),
                        query_sugerida TEXT NOT NULL,
                        youtube_url TEXT NOT NULL,
                        youtube_id VARCHAR(20),
                        video_title TEXT,
                        channel_name VARCHAR(255),
                        channel_id VARCHAR(50),
                        duration_seconds INTEGER,
                        view_count BIGINT,
                        like_count INTEGER,
                        dislike_count INTEGER,
                        comment_count INTEGER,
                        tipo_contenido VARCHAR(50) DEFAULT 'explicativo',
                        nivel_dificultad INTEGER DEFAULT 3,
                        proceso_cognitivo VARCHAR(50) DEFAULT 'Comprender',
                        contexto_aplicacion VARCHAR(50) DEFAULT 'Académico',
                        calidad_score DECIMAL(3,2) DEFAULT 0.80,
                        relevancia_score DECIMAL(3,2) DEFAULT 0.85,
                        ratio_likes DECIMAL(3,2),
                        prerequisitos_video UUID[],
                        tiempo_estimado_estudio INTEGER DEFAULT 15,
                        puntos_xp INTEGER DEFAULT 50,
                        orden_recomendacion INTEGER DEFAULT 1,
                        verificado_instructor BOOLEAN DEFAULT false,
                        fecha_verificacion TIMESTAMP WITH TIME ZONE,
                        estado VARCHAR(20) DEFAULT 'activo',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_validated_at TIMESTAMP WITH TIME ZONE
                    );
                """))
                
                # Create indexes
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_youtube_links_tema 
                    ON youtube_links(codigo_tema);
                """))
                
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_youtube_links_area 
                    ON youtube_links(area_evaluada);
                """))
                
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_youtube_links_dificultad 
                    ON youtube_links(nivel_dificultad);
                """))
                
                logger.info("✅ Tabla youtube_links creada exitosamente")
            else:
                logger.info("✅ Tabla youtube_links ya existe")
                
        except Exception as e:
            logger.error(f"❌ Error creando tabla: {e}")
            raise
    
    async def insert_youtube_links(self, db, df: pd.DataFrame) -> int:
        """Insertar links de YouTube en la base de datos"""
        try:
            inserted_count = 0
            
            for _, row in df.iterrows():
                try:
                    # Check if link already exists
                    existing = await db.execute(text("""
                        SELECT id FROM youtube_links 
                        WHERE codigo_tema = :codigo_tema 
                        AND youtube_url = :youtube_url
                    """), {
                        'codigo_tema': row['codigo_tema'],
                        'youtube_url': row['youtube_url']
                    })
                    
                    if existing.fetchone():
                        logger.debug(f"⚠️ Link ya existe para {row['codigo_tema']}")
                        continue
                    
                    # Insert new link
                    await db.execute(text("""
                        INSERT INTO youtube_links (
                            codigo_tema, area_evaluada, tema_principal,
                            canal_sugerido, query_sugerida, youtube_url,
                            youtube_id, tipo_contenido, nivel_dificultad,
                            proceso_cognitivo, contexto_aplicacion,
                            calidad_score, relevancia_score,
                            tiempo_estimado_estudio, puntos_xp,
                            orden_recomendacion, estado
                        ) VALUES (
                            :codigo_tema, :area_evaluada, :tema_principal,
                            :canal_sugerido, :query_sugerida, :youtube_url,
                            :youtube_id, :tipo_contenido, :nivel_dificultad,
                            :proceso_cognitivo, :contexto_aplicacion,
                            :calidad_score, :relevancia_score,
                            :tiempo_estimado_estudio, :puntos_xp,
                            :orden_recomendacion, :estado
                        )
                    """), {
                        'codigo_tema': row['codigo_tema'],
                        'area_evaluada': row['area_evaluada'],
                        'tema_principal': row['tema_principal'],
                        'canal_sugerido': row['canal_sugerido'],
                        'query_sugerida': row['query_sugerida'],
                        'youtube_url': row['youtube_url'],
                        'youtube_id': row['youtube_id'],
                        'tipo_contenido': row['tipo_contenido'],
                        'nivel_dificultad': row['nivel_dificultad'],
                        'proceso_cognitivo': row['proceso_cognitivo'],
                        'contexto_aplicacion': row['contexto_aplicacion'],
                        'calidad_score': row['calidad_score'],
                        'relevancia_score': row['relevancia_score'],
                        'tiempo_estimado_estudio': row['tiempo_estimado_estudio'],
                        'puntos_xp': row['puntos_xp'],
                        'orden_recomendacion': row['orden_recomendacion'],
                        'estado': row['estado']
                    })
                    
                    inserted_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error insertando link {row['codigo_tema']}: {e}")
                    continue
            
            # Commit changes
            await db.commit()
            
            return inserted_count
            
        except Exception as e:
            logger.error(f"❌ Error en inserción masiva: {e}")
            await db.rollback()
            raise

async def main():
    """Función principal"""
    loader = YouTubeLinksLoader()
    success = await loader.load_youtube_links()
    
    if success:
        logger.info("🎉 Carga del catálogo de YouTube completada exitosamente")
    else:
        logger.error("❌ Falló la carga del catálogo de YouTube")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())



