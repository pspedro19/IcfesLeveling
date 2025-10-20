#!/usr/bin/env python3
"""
Script para verificar el estado actual de la base de datos
Muestra qué tablas existen, cuántos datos hay, y qué campos están disponibles
"""

import psycopg2
import json
import os
from datetime import datetime

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'gameplay_db'),
    'user': os.getenv('DB_USER', 'gameplay'),
    'password': os.getenv('DB_PASSWORD', 'gameplay123')
}

def check_database_status():
    """Verificar estado de la base de datos"""
    try:
        print("🔍 VERIFICACIÓN DEL ESTADO DE LA BASE DE DATOS")
        print("=" * 60)
        
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("✅ Conexión exitosa a la base de datos")
        print()
        
        # 1. Verificar tablas principales
        print("📋 TABLAS PRINCIPALES:")
        tables_to_check = ['subjects', 'topics', 'questions', 'users']
        
        for table in tables_to_check:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  ✅ {table}: {count} registros")
            except Exception as e:
                print(f"  ❌ {table}: Error - {e}")
        
        print()
        
        # 2. Verificar estructura de la tabla questions
        print("🔧 ESTRUCTURA DE LA TABLA QUESTIONS:")
        try:
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'questions' 
                ORDER BY ordinal_position
            """)
            columns = cur.fetchall()
            
            print(f"  📊 Total columnas: {len(columns)}")
            
            # Mostrar primeras 20 columnas
            print("  📋 Primeras 20 columnas:")
            for i, (col_name, data_type, nullable) in enumerate(columns[:20]):
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                print(f"    {i+1:2d}. {col_name:<25} {data_type:<15} {nullable_str}")
            
            if len(columns) > 20:
                print(f"    ... y {len(columns) - 20} columnas más")
                
        except Exception as e:
            print(f"  ❌ Error verificando estructura: {e}")
        
        print()
        
        # 3. Verificar datos en subjects
        print("📚 MATERIAS DISPONIBLES:")
        try:
            cur.execute("SELECT id, name, description FROM subjects ORDER BY name")
            subjects = cur.fetchall()
            
            for subject_id, name, description in subjects:
                # Contar preguntas por materia
                cur.execute("SELECT COUNT(*) FROM questions WHERE subject_id = %s", (subject_id,))
                question_count = cur.fetchone()[0]
                
                print(f"  📖 {name}")
                print(f"      ID: {subject_id}")
                print(f"      Descripción: {description}")
                print(f"      Preguntas: {question_count}")
                print()
                
        except Exception as e:
            print(f"  ❌ Error verificando materias: {e}")
        
        # 4. Verificar preguntas por área (si existe el campo)
        print("📊 DISTRIBUCIÓN DE PREGUNTAS:")
        try:
            # Verificar si existe el campo area_evaluada
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'questions' AND column_name = 'area_evaluada'
            """)
            
            if cur.fetchone():
                cur.execute("""
                    SELECT area_evaluada, COUNT(*) as count
                    FROM questions 
                    WHERE area_evaluada IS NOT NULL
                    GROUP BY area_evaluada 
                    ORDER BY count DESC
                """)
                areas = cur.fetchall()
                
                if areas:
                    print("  Por área evaluada:")
                    for area, count in areas:
                        print(f"    📈 {area}: {count} preguntas")
                else:
                    print("  ⚠️ No hay datos en el campo area_evaluada")
            else:
                print("  ⚠️ Campo area_evaluada no existe en la tabla")
                
        except Exception as e:
            print(f"  ❌ Error verificando distribución: {e}")
        
        print()
        
        # 5. Verificar campos ICFES
        print("🎯 CAMPOS ICFES DISPONIBLES:")
        icfes_fields = [
            'area_evaluada', 'competencia', 'componente', 'tema_especifico',
            'requiere_imagen', 'imagen_pregunta_url', 'puntos_xp', 'tiempo_estimado'
        ]
        
        for field in icfes_fields:
            try:
                cur.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'questions' AND column_name = %s
                """, (field,))
                
                if cur.fetchone():
                    # Contar valores no nulos
                    cur.execute(f"SELECT COUNT(*) FROM questions WHERE {field} IS NOT NULL")
                    count = cur.fetchone()[0]
                    print(f"  ✅ {field}: {count} valores")
                else:
                    print(f"  ❌ {field}: Campo no existe")
                    
            except Exception as e:
                print(f"  ⚠️ {field}: Error - {e}")
        
        print()
        
        # 6. Verificar últimas preguntas cargadas
        print("📝 ÚLTIMAS PREGUNTAS CARGADAS:")
        try:
            cur.execute("""
                SELECT id, question_text, created_at
                FROM questions 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            recent_questions = cur.fetchall()
            
            for q_id, text, created_at in recent_questions:
                text_preview = text[:50] + "..." if len(text) > 50 else text
                print(f"  📄 {q_id}")
                print(f"      Texto: {text_preview}")
                print(f"      Creado: {created_at}")
                print()
                
        except Exception as e:
            print(f"  ❌ Error verificando preguntas recientes: {e}")
        
        # 7. Generar reporte JSON
        print("📊 GENERANDO REPORTE JSON...")
        try:
            cur.execute("SELECT COUNT(*) FROM questions")
            total_questions = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM subjects")
            total_subjects = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM topics")
            total_topics = cur.fetchone()[0]
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "database_status": "connected",
                "totals": {
                    "questions": total_questions,
                    "subjects": total_subjects,
                    "topics": total_topics
                },
                "icfes_fields_available": [],
                "subjects_with_questions": []
            }
            
            # Verificar campos ICFES disponibles
            for field in icfes_fields:
                cur.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'questions' AND column_name = %s
                """, (field,))
                if cur.fetchone():
                    report["icfes_fields_available"].append(field)
            
            # Materias con preguntas
            cur.execute("""
                SELECT s.name, COUNT(q.id) as count
                FROM subjects s
                LEFT JOIN questions q ON s.id = q.subject_id
                GROUP BY s.name
                ORDER BY count DESC
            """)
            for name, count in cur.fetchall():
                report["subjects_with_questions"].append({"name": name, "questions": count})
            
            # Guardar reporte
            with open('database/seed_data/database_status_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print("✅ Reporte guardado en: database/seed_data/database_status_report.json")
            
        except Exception as e:
            print(f"❌ Error generando reporte: {e}")
        
        cur.close()
        conn.close()
        
        print()
        print("🎉 VERIFICACIÓN COMPLETADA")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False

if __name__ == "__main__":
    check_database_status()
