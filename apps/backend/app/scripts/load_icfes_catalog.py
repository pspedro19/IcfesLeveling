#!/usr/bin/env python3
"""
Script para cargar el catálogo completo de 337 temas ICFES
desde el archivo CSV a la base de datos PostgreSQL
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from typing import List, Dict, Any
import sys
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ICFESCatalogLoader:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None
        
    def connect(self):
        """Conectar a la base de datos PostgreSQL"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("✅ Conexión a base de datos establecida")
        except Exception as e:
            logger.error(f"❌ Error conectando a la base de datos: {e}")
            raise
    
    def disconnect(self):
        """Desconectar de la base de datos"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Conexión a base de datos cerrada")
    
    def load_csv_data(self, csv_path: str) -> pd.DataFrame:
        """Cargar datos desde el archivo CSV"""
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"✅ CSV cargado: {len(df)} temas encontrados")
            return df
        except Exception as e:
            logger.error(f"❌ Error cargando CSV: {e}")
            raise
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpiar y preparar los datos para inserción"""
        # Limpiar campos de array (prerequisitos, temas_relacionados, recursos, indicadores)
        array_columns = ['prerequisitos', 'temas_relacionados', 'recursos_teoria', 
                        'recursos_practica', 'recursos_evaluacion', 'indicadores_dominio']
        
        for col in array_columns:
            if col in df.columns:
                df[col] = df[col].apply(self._parse_array_field)
        
        # Convertir campos numéricos
        numeric_columns = ['nivel_dificultad', 'importancia_icfes', 'orden_secuencial',
                          'horas_teoria', 'horas_practica', 'numero_ejercicios_recomendados',
                          'sesiones_refuerzo', 'umbral_dominio', 'tiempo_retencion']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Convertir frecuencia_evaluacion
        if 'frecuencia_evaluacion' in df.columns:
            df['frecuencia_evaluacion'] = pd.to_numeric(df['frecuencia_evaluacion'], errors='coerce').fillna(0)
        
        logger.info("✅ Datos limpiados y preparados")
        return df
    
    def _parse_array_field(self, field_value):
        """Parsear campos de array desde el CSV"""
        if pd.isna(field_value) or field_value == '':
            return []
        
        if isinstance(field_value, str):
            # Separar por punto y coma y limpiar
            items = [item.strip() for item in field_value.split(';') if item.strip()]
            return items
        
        return []
    
    def create_table_if_not_exists(self):
        """Crear la tabla si no existe"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS study_topics_catalog (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            codigo_tema VARCHAR(20) UNIQUE NOT NULL,
            area_evaluada VARCHAR(30) NOT NULL,
            tema_principal VARCHAR(100) NOT NULL,
            subtema VARCHAR(100),
            tema_especifico VARCHAR(150),
            competencia_icfes VARCHAR(150) NOT NULL,
            componente VARCHAR(50),
            afirmacion TEXT,
            evidencia TEXT,
            grado_introduccion VARCHAR(10),
            prerequisitos TEXT[],
            temas_relacionados TEXT[],
            orden_secuencial INTEGER,
            nivel_dificultad INTEGER,
            importancia_icfes INTEGER,
            frecuencia_evaluacion DECIMAL(5,2),
            horas_teoria INTEGER,
            horas_practica INTEGER,
            numero_ejercicios_recomendados INTEGER,
            sesiones_refuerzo INTEGER,
            recursos_teoria TEXT[],
            recursos_practica TEXT[],
            recursos_evaluacion TEXT[],
            umbral_dominio DECIMAL(5,2),
            tiempo_retencion INTEGER,
            indicadores_dominio TEXT[],
            estilo_aprendizaje_optimo VARCHAR(30),
            metodologia_recomendada VARCHAR(50),
            tipo_evaluacion VARCHAR(30),
            estado VARCHAR(20) DEFAULT 'activo',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_sql)
                self.connection.commit()
                logger.info("✅ Tabla study_topics_catalog creada/verificada")
        except Exception as e:
            logger.error(f"❌ Error creando tabla: {e}")
            raise
    
    def insert_topics(self, df: pd.DataFrame):
        """Insertar todos los temas en la base de datos"""
        insert_sql = """
        INSERT INTO study_topics_catalog (
            codigo_tema, area_evaluada, tema_principal, subtema, tema_especifico,
            competencia_icfes, componente, afirmacion, evidencia, grado_introduccion,
            prerequisitos, temas_relacionados, orden_secuencial, nivel_dificultad,
            importancia_icfes, frecuencia_evaluacion, horas_teoria, horas_practica,
            numero_ejercicios_recomendados, sesiones_refuerzo, recursos_teoria,
            recursos_practica, recursos_evaluacion, umbral_dominio, tiempo_retencion,
            indicadores_dominio, estilo_aprendizaje_optimo, metodologia_recomendada,
            tipo_evaluacion, estado
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (codigo_tema) DO UPDATE SET
            area_evaluada = EXCLUDED.area_evaluada,
            tema_principal = EXCLUDED.tema_principal,
            subtema = EXCLUDED.subtema,
            tema_especifico = EXCLUDED.tema_especifico,
            competencia_icfes = EXCLUDED.competencia_icfes,
            componente = EXCLUDED.componente,
            afirmacion = EXCLUDED.afirmacion,
            evidencia = EXCLUDED.evidencia,
            grado_introduccion = EXCLUDED.grado_introduccion,
            prerequisitos = EXCLUDED.prerequisitos,
            temas_relacionados = EXCLUDED.temas_relacionados,
            orden_secuencial = EXCLUDED.orden_secuencial,
            nivel_dificultad = EXCLUDED.nivel_dificultad,
            importancia_icfes = EXCLUDED.importancia_icfes,
            frecuencia_evaluacion = EXCLUDED.frecuencia_evaluacion,
            horas_teoria = EXCLUDED.horas_teoria,
            horas_practica = EXCLUDED.horas_practica,
            numero_ejercicios_recomendados = EXCLUDED.numero_ejercicios_recomendados,
            sesiones_refuerzo = EXCLUDED.sesiones_refuerzo,
            recursos_teoria = EXCLUDED.recursos_teoria,
            recursos_practica = EXCLUDED.recursos_practica,
            recursos_evaluacion = EXCLUDED.recursos_evaluacion,
            umbral_dominio = EXCLUDED.umbral_dominio,
            tiempo_retencion = EXCLUDED.tiempo_retencion,
            indicadores_dominio = EXCLUDED.indicadores_dominio,
            estilo_aprendizaje_optimo = EXCLUDED.estilo_aprendizaje_optimo,
            metodologia_recomendada = EXCLUDED.metodologia_recomendada,
            tipo_evaluacion = EXCLUDED.tipo_evaluacion,
            estado = EXCLUDED.estado,
            updated_at = CURRENT_TIMESTAMP
        """
        
        try:
            with self.connection.cursor() as cursor:
                for index, row in df.iterrows():
                    values = (
                        row['codigo_tema'], row['area_evaluada'], row['tema_principal'],
                        row['subtema'], row['tema_especifico'], row['competencia_icfes'],
                        row['componente'], row['afirmacion'], row['evidencia'],
                        row['grado_introduccion'], row['prerequisitos'], row['temas_relacionados'],
                        row['orden_secuencial'], row['nivel_dificultad'], row['importancia_icfes'],
                        row['frecuencia_evaluacion'], row['horas_teoria'], row['horas_practica'],
                        row['numero_ejercicios_recomendados'], row['sesiones_refuerzo'],
                        row['recursos_teoria'], row['recursos_practica'], row['recursos_evaluacion'],
                        row['umbral_dominio'], row['tiempo_retencion'], row['indicadores_dominio'],
                        row['estilo_aprendizaje_optimo'], row['metodologia_recomendada'],
                        row['tipo_evaluacion'], row['estado']
                    )
                    
                    cursor.execute(insert_sql, values)
                    
                    if (index + 1) % 50 == 0:
                        logger.info(f"📚 Procesados {index + 1}/{len(df)} temas")
                
                self.connection.commit()
                logger.info(f"✅ Todos los {len(df)} temas insertados exitosamente")
                
        except Exception as e:
            logger.error(f"❌ Error insertando temas: {e}")
            self.connection.rollback()
            raise
    
    def verify_insertion(self) -> Dict[str, Any]:
        """Verificar que la inserción fue exitosa"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Contar total de temas
                cursor.execute("SELECT COUNT(*) as total FROM study_topics_catalog")
                total_count = cursor.fetchone()['total']
                
                # Contar por área
                cursor.execute("""
                    SELECT area_evaluada, COUNT(*) as count 
                    FROM study_topics_catalog 
                    GROUP BY area_evaluada 
                    ORDER BY count DESC
                """)
                area_counts = cursor.fetchall()
                
                # Verificar algunos temas específicos
                cursor.execute("""
                    SELECT codigo_tema, tema_principal, area_evaluada 
                    FROM study_topics_catalog 
                    ORDER BY codigo_tema 
                    LIMIT 5
                """)
                sample_topics = cursor.fetchall()
                
                return {
                    'total_topics': total_count,
                    'area_distribution': area_counts,
                    'sample_topics': sample_topics
                }
                
        except Exception as e:
            logger.error(f"❌ Error verificando inserción: {e}")
            raise
    
    def run(self, csv_path: str):
        """Ejecutar el proceso completo de carga"""
        try:
            logger.info("🚀 Iniciando carga del catálogo ICFES...")
            
            # 1. Conectar a la base de datos
            self.connect()
            
            # 2. Crear tabla si no existe
            self.create_table_if_not_exists()
            
            # 3. Cargar y limpiar datos CSV
            df = self.load_csv_data(csv_path)
            df = self.clean_data(df)
            
            # 4. Insertar temas
            self.insert_topics(df)
            
            # 5. Verificar inserción
            verification = self.verify_insertion()
            
            logger.info("=" * 50)
            logger.info("📊 RESUMEN DE CARGA ICFES")
            logger.info("=" * 50)
            logger.info(f"Total de temas cargados: {verification['total_topics']}")
            logger.info("Distribución por área:")
            for area in verification['area_distribution']:
                logger.info(f"  - {area['area_evaluada']}: {area['count']} temas")
            logger.info("=" * 50)
            
            return verification
            
        except Exception as e:
            logger.error(f"❌ Error en el proceso de carga: {e}")
            raise
        finally:
            self.disconnect()

def main():
    """Función principal"""
    # Configuración de la base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'icfes_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password')
    }
    
    # Ruta del archivo CSV
    csv_path = "database/catalogs/icfes_topics.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"❌ Archivo CSV no encontrado: {csv_path}")
        sys.exit(1)
    
    try:
        # Crear loader y ejecutar
        loader = ICFESCatalogLoader(db_config)
        result = loader.run(csv_path)
        
        logger.info("🎉 ¡Carga del catálogo ICFES completada exitosamente!")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
