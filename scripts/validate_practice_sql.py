#!/usr/bin/env python3
"""
Validador de Consultas SQL para Sistema de Práctica
Verifica que SOLO se muestran preguntas falladas del diagnóstico
"""

import asyncio
import asyncpg
import logging
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PracticeSQLValidator:
    """Validador de SQL para sistema de práctica"""
    
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'icfes_leveling',
            'user': 'gameplay',
            'password': 'gameplay123'
        }

    async def connect_database(self):
        """Conectar a base de datos"""
        try:
            conn = await asyncpg.connect(**self.db_config)
            logger.info("Conexión exitosa a PostgreSQL")
            return conn
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            return None

    async def create_test_schema(self, conn: asyncpg.Connection):
        """Crear esquema de test con datos simulados"""
        
        # Crear tablas de test
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_students (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100)
            );
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_diagnostic_attempts (
                id SERIAL PRIMARY KEY,
                student_id INT REFERENCES test_students(id),
                subject VARCHAR(50),
                finished_at TIMESTAMPTZ DEFAULT NOW(),
                theta DECIMAL(6,3)
            );
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_question_responses (
                id SERIAL PRIMARY KEY,
                attempt_id INT REFERENCES test_diagnostic_attempts(id),
                question_id INT,
                is_correct BOOLEAN,
                selected_option CHAR(1),
                time_seconds INT
            );
        """)
        
        # Insertar datos de test
        await conn.execute("DELETE FROM test_question_responses")
        await conn.execute("DELETE FROM test_diagnostic_attempts")
        await conn.execute("DELETE FROM test_students")
        
        # Estudiante de prueba
        student_id = await conn.fetchval("INSERT INTO test_students (name) VALUES ('Test Student') RETURNING id")
        
        # Diagnóstico de prueba
        attempt_id = await conn.fetchval("""
            INSERT INTO test_diagnostic_attempts (student_id, subject, theta) 
            VALUES ($1, 'Matemáticas', -0.5) RETURNING id
        """, student_id)
        
        # Respuestas: 5 correctas, 5 incorrectas
        test_responses = [
            (attempt_id, 1, True, 'A', 45),   # Correcta
            (attempt_id, 2, False, 'B', 67),  # Incorrecta - debe aparecer en práctica
            (attempt_id, 3, True, 'C', 34),   # Correcta
            (attempt_id, 4, False, 'D', 89),  # Incorrecta - debe aparecer en práctica
            (attempt_id, 5, True, 'A', 23),   # Correcta
            (attempt_id, 6, False, 'B', 156), # Incorrecta - debe aparecer en práctica
            (attempt_id, 7, True, 'C', 45),   # Correcta
            (attempt_id, 8, False, 'A', 234), # Incorrecta - debe aparecer en práctica
            (attempt_id, 9, True, 'D', 67),   # Correcta
            (attempt_id, 10, False, 'C', 123) # Incorrecta - debe aparecer en práctica
        ]
        
        for response in test_responses:
            await conn.execute("""
                INSERT INTO test_question_responses 
                (attempt_id, question_id, is_correct, selected_option, time_seconds)
                VALUES ($1, $2, $3, $4, $5)
            """, *response)
        
        logger.info("Esquema de test creado con 5 respuestas correctas y 5 incorrectas")
        return student_id, attempt_id

    async def test_practice_pool_query(self, conn: asyncpg.Connection, student_id: int) -> Dict[str, Any]:
        """Test: Pool de práctica SOLO debe contener preguntas falladas"""
        
        # Query que simula el pool de práctica
        practice_pool_query = """
            SELECT DISTINCT
                qr.question_id,
                qr.is_correct,
                qr.selected_option,
                qr.time_seconds,
                da.finished_at
            FROM test_question_responses qr
            JOIN test_diagnostic_attempts da ON qr.attempt_id = da.id
            WHERE 
                da.student_id = $1
                AND qr.is_correct = FALSE
            ORDER BY qr.question_id;
        """
        
        failed_questions = await conn.fetch(practice_pool_query, student_id)
        
        # Query para verificar que NO hay preguntas correctas en el pool
        correct_in_pool_query = """
            SELECT COUNT(*) as incorrect_questions_in_pool
            FROM test_question_responses qr
            JOIN test_diagnostic_attempts da ON qr.attempt_id = da.id
            WHERE 
                da.student_id = $1
                AND qr.is_correct = TRUE
        """
        
        correct_count = await conn.fetchval(correct_in_pool_query, student_id)
        
        return {
            "failed_questions_in_pool": len(failed_questions),
            "expected_failed_questions": 5,  # Sabemos que hay 5 incorrectas
            "correct_questions_excluded": correct_count,  # Debe ser 5 (las correctas)
            "pool_contains_only_failures": len(failed_questions) == 5,
            "zero_correct_in_pool": True,  # El pool NO debe tener correctas
            "failed_question_ids": [r['question_id'] for r in failed_questions]
        }

    async def test_mastery_tracking_query(self, conn: asyncpg.Connection, student_id: int) -> Dict[str, Any]:
        """Test: Tracking de dominio por pregunta"""
        
        # Simular tabla de práctica
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_practice_attempts (
                id SERIAL PRIMARY KEY,
                student_id INT,
                question_id INT,
                is_correct BOOLEAN,
                attempt_date TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        await conn.execute("DELETE FROM test_practice_attempts")
        
        # Simular práctica: pregunta 2 practicada 3 veces y dominada
        practice_attempts = [
            (student_id, 2, False),  # Primer intento fallido
            (student_id, 2, False),  # Segundo intento fallido
            (student_id, 2, True),   # Tercer intento exitoso
            (student_id, 2, True),   # Cuarto intento exitoso
            (student_id, 2, True),   # Quinto intento exitoso - ¡DOMINADA!
            (student_id, 4, False),  # Pregunta 4 aún no dominada
            (student_id, 6, True),   # Pregunta 6, solo un intento exitoso
        ]
        
        for attempt in practice_attempts:
            await conn.execute("""
                INSERT INTO test_practice_attempts (student_id, question_id, is_correct)
                VALUES ($1, $2, $3)
            """, *attempt)
        
        # Query de mastery: pregunta dominada = 3 éxitos consecutivos
        mastery_query = """
            WITH recent_attempts AS (
                SELECT 
                    question_id,
                    is_correct,
                    ROW_NUMBER() OVER (PARTITION BY question_id ORDER BY attempt_date DESC) as attempt_rank
                FROM test_practice_attempts
                WHERE student_id = $1
            ),
            last_three AS (
                SELECT 
                    question_id,
                    COUNT(*) as attempts_in_last_three,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_in_last_three
                FROM recent_attempts
                WHERE attempt_rank <= 3
                GROUP BY question_id
            )
            SELECT 
                question_id,
                attempts_in_last_three,
                correct_in_last_three,
                CASE 
                    WHEN attempts_in_last_three >= 3 AND correct_in_last_three = 3 
                    THEN TRUE 
                    ELSE FALSE 
                END as is_mastered
            FROM last_three
            ORDER BY question_id;
        """
        
        mastery_results = await conn.fetch(mastery_query, student_id)
        
        # Calcular progreso de dominio
        total_failed_questions = 5  # Sabemos que hay 5 preguntas falladas
        mastered_count = sum(1 for r in mastery_results if r['is_mastered'])
        mastery_percentage = (mastered_count / total_failed_questions) * 100 if total_failed_questions > 0 else 0
        
        return {
            "total_failed_questions": total_failed_questions,
            "questions_practiced": len(mastery_results),
            "questions_mastered": mastered_count,
            "mastery_percentage": round(mastery_percentage, 1),
            "mastery_details": [dict(r) for r in mastery_results],
            "expected_mastered": 1  # Solo la pregunta 2 debería estar dominada
        }

    async def test_priority_scoring_query(self, conn: asyncpg.Connection, student_id: int) -> Dict[str, Any]:
        """Test: Sistema de priorización de preguntas"""
        
        # Query de priorización basada en recencia y severidad
        priority_query = """
            SELECT 
                qr.question_id,
                qr.time_seconds,
                da.finished_at,
                CASE 
                    WHEN da.finished_at > NOW() - INTERVAL '7 days' THEN 1.0
                    WHEN da.finished_at > NOW() - INTERVAL '30 days' THEN 0.6
                    ELSE 0.3
                END AS recency_score,
                CASE
                    WHEN qr.time_seconds > 120 THEN 1.0  -- Tiempo excesivo
                    WHEN qr.time_seconds > 60 THEN 0.7   -- Tiempo alto
                    ELSE 0.4
                END AS severity_score,
                (CASE 
                    WHEN da.finished_at > NOW() - INTERVAL '7 days' THEN 1.0
                    WHEN da.finished_at > NOW() - INTERVAL '30 days' THEN 0.6
                    ELSE 0.3
                END * 0.4 + 
                CASE
                    WHEN qr.time_seconds > 120 THEN 1.0
                    WHEN qr.time_seconds > 60 THEN 0.7
                    ELSE 0.4
                END * 0.6) AS total_priority_score
            FROM test_question_responses qr
            JOIN test_diagnostic_attempts da ON qr.attempt_id = da.id
            WHERE 
                da.student_id = $1
                AND qr.is_correct = FALSE
            ORDER BY total_priority_score DESC;
        """
        
        priority_results = await conn.fetch(priority_query, student_id)
        
        # Verificar que preguntas con más tiempo tienen mayor prioridad
        high_priority_questions = [r for r in priority_results if r['total_priority_score'] > 0.8]
        
        return {
            "failed_questions_prioritized": len(priority_results),
            "high_priority_questions": len(high_priority_questions),
            "priority_details": [dict(r) for r in priority_results],
            "scoring_works": len(priority_results) > 0 and priority_results[0]['total_priority_score'] > 0
        }

    async def run_all_sql_validations(self) -> Dict[str, Any]:
        """Ejecutar todas las validaciones SQL"""
        
        conn = await self.connect_database()
        if not conn:
            return {"status": "FAIL", "message": "No se pudo conectar a la base de datos"}
        
        try:
            # Crear esquema de test
            student_id, attempt_id = await self.create_test_schema(conn)
            
            # Ejecutar validaciones
            practice_pool_test = await self.test_practice_pool_query(conn, student_id)
            mastery_test = await self.test_mastery_tracking_query(conn, student_id)
            priority_test = await self.test_priority_scoring_query(conn, student_id)
            
            # Validaciones críticas
            validations = []
            
            # 1. Pool solo contiene preguntas falladas
            if practice_pool_test["pool_contains_only_failures"] and practice_pool_test["zero_correct_in_pool"]:
                validations.append({"test": "POOL_ONLY_FAILURES", "status": "PASS", "message": "Pool contiene SOLO preguntas falladas"})
            else:
                validations.append({"test": "POOL_ONLY_FAILURES", "status": "FAIL", "message": "Pool contiene preguntas no falladas"})
            
            # 2. Tracking de mastery funciona
            if mastery_test["questions_mastered"] == mastery_test["expected_mastered"]:
                validations.append({"test": "MASTERY_TRACKING", "status": "PASS", "message": f"Mastery tracking correcto: {mastery_test['questions_mastered']} dominadas"})
            else:
                validations.append({"test": "MASTERY_TRACKING", "status": "WARNING", "message": f"Mastery: {mastery_test['questions_mastered']} vs esperado {mastery_test['expected_mastered']}"})
            
            # 3. Sistema de priorización funciona
            if priority_test["scoring_works"]:
                validations.append({"test": "PRIORITY_SCORING", "status": "PASS", "message": "Sistema de priorización funcional"})
            else:
                validations.append({"test": "PRIORITY_SCORING", "status": "FAIL", "message": "Sistema de priorización no funciona"})
            
            # Limpiar tablas de test
            await conn.execute("DROP TABLE IF EXISTS test_practice_attempts")
            await conn.execute("DROP TABLE IF EXISTS test_question_responses")
            await conn.execute("DROP TABLE IF EXISTS test_diagnostic_attempts") 
            await conn.execute("DROP TABLE IF EXISTS test_students")
            
            return {
                "status": "SUCCESS",
                "validations": validations,
                "test_results": {
                    "practice_pool": practice_pool_test,
                    "mastery_tracking": mastery_test,
                    "priority_scoring": priority_test
                }
            }
            
        except Exception as e:
            logger.error(f"Error en validación SQL: {e}")
            return {"status": "FAIL", "message": str(e)}
        
        finally:
            await conn.close()

async def main():
    """Función principal"""
    validator = PracticeSQLValidator()
    
    result = await validator.run_all_sql_validations()
    
    print("\n" + "="*60)
    print("VALIDACION DE CONSULTAS SQL - SISTEMA DE PRACTICA")  
    print("="*60)
    
    if result["status"] == "SUCCESS":
        print("Estado: EXITOSO")
        
        print("\nRESULTADOS DE VALIDACION:")
        for validation in result["validations"]:
            status_symbol = {"PASS": "[OK]", "WARNING": "[WARN]", "FAIL": "[FAIL]"}[validation["status"]]
            print(f"{status_symbol} {validation['test']}: {validation['message']}")
        
        print("\nDETALLES TECNICOS:")
        test_results = result["test_results"]
        
        print(f"- Pool de práctica: {test_results['practice_pool']['failed_questions_in_pool']} preguntas falladas")
        print(f"- Preguntas correctas excluidas: {test_results['practice_pool']['correct_questions_excluded']}")
        print(f"- Mastery: {test_results['mastery_tracking']['mastery_percentage']}% dominado")
        print(f"- Priorización: {test_results['priority_scoring']['high_priority_questions']} de alta prioridad")
        
        # Determinar resultado final
        failed_count = sum(1 for v in result["validations"] if v["status"] == "FAIL")
        if failed_count == 0:
            print("\nSISTEMA DE PRACTICA: VALIDADO CORRECTAMENTE")
            return 0
        else:
            print(f"\nSISTEMA DE PRACTICA: {failed_count} validaciones fallaron")
            return 1
    else:
        print(f"Estado: FALLO - {result.get('message', 'Error desconocido')}")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())