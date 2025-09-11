#!/usr/bin/env python3
"""
Validador de Lógica SQL (Sin Conexión)
Analiza el código SQL en los scripts para validar lógica correcta
"""

import re
from pathlib import Path
from typing import Dict, List, Any

class SQLLogicValidator:
    """Validador de lógica SQL sin conexión a BD"""
    
    def __init__(self):
        self.project_root = Path(r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling")
        self.scripts_dir = self.project_root / "scripts"
        self.results = []

    def add_result(self, test_name: str, status: str, message: str, details: Dict = None):
        """Agregar resultado de validación"""
        self.results.append({
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {}
        })

    def validate_practice_from_failures_sql(self):
        """Validar SQL en practice_from_failures.py"""
        script_path = self.scripts_dir / "practice_from_failures.py"
        
        if not script_path.exists():
            self.add_result(
                "PRACTICE_SQL_EXISTS",
                "FAIL",
                "Script practice_from_failures.py no encontrado"
            )
            return
        
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patrones SQL críticos que DEBEN existir
        critical_sql_patterns = [
            (r"is_correct\s*=\s*FALSE", "Filtro por respuestas incorrectas"),
            (r"diagnostic_attempts", "Referencia a diagnósticos"),
            (r"WHERE.*is_correct.*FALSE", "Filtrado explícito por fallos"),
            (r"JOIN.*question_responses", "JOIN con respuestas"),
            (r"student_id", "Filtro por estudiante")
        ]
        
        patterns_found = []
        patterns_missing = []
        
        for pattern, description in critical_sql_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                patterns_found.append((pattern, description))
            else:
                patterns_missing.append((pattern, description))
        
        # Verificar que NO hay patrones problemáticos
        problematic_patterns = [
            (r"is_correct\s*=\s*TRUE", "No debe incluir respuestas correctas"),
            (r"SELECT.*\*.*FROM.*questions", "No debe seleccionar todas las preguntas")
        ]
        
        problems_found = []
        for pattern, description in problematic_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                problems_found.append((pattern, description))
        
        # Buscar comentarios explicativos
        has_practice_comments = re.search(r"#.*practice.*fail|#.*solo.*fall|#.*only.*fail", content, re.IGNORECASE)
        
        details = {
            "patterns_found": len(patterns_found),
            "patterns_missing": len(patterns_missing),
            "problems_found": len(problems_found),
            "has_explanatory_comments": bool(has_practice_comments),
            "missing_patterns": [desc for _, desc in patterns_missing],
            "problematic_patterns": [desc for _, desc in problems_found]
        }
        
        if len(patterns_found) >= 4 and len(problems_found) == 0:
            self.add_result(
                "PRACTICE_SQL_LOGIC",
                "PASS",
                f"Lógica SQL correcta: {len(patterns_found)}/5 patrones críticos encontrados",
                details
            )
        elif len(patterns_found) >= 3:
            self.add_result(
                "PRACTICE_SQL_LOGIC",
                "WARNING",
                f"Lógica SQL mayormente correcta, faltan {len(patterns_missing)} patrones",
                details
            )
        else:
            self.add_result(
                "PRACTICE_SQL_LOGIC",
                "FAIL", 
                f"Lógica SQL incorrecta: {len(patterns_missing)} patrones críticos faltantes",
                details
            )

    def validate_irt_engine_sql(self):
        """Validar cálculos IRT en el motor"""
        script_path = self.scripts_dir / "irt_3pl_engine.py"
        
        if not script_path.exists():
            self.add_result(
                "IRT_ENGINE_EXISTS",
                "FAIL",
                "Script irt_3pl_engine.py no encontrado"
            )
            return
        
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patrones IRT 3PL críticos
        irt_patterns = [
            (r"def.*probability.*theta", "Función de probabilidad P(θ)"),
            (r"exp.*a.*theta.*b", "Fórmula 3PL con parámetros a, b"),
            (r"self\.c.*\+.*1.*-.*self\.c", "Parámetro c (guessing)"),
            (r"information.*fisher", "Información de Fisher"),
            (r"likelihood", "Maximum Likelihood Estimation"),
            (r"theta.*estimate", "Estimación de habilidad theta")
        ]
        
        irt_found = []
        irt_missing = []
        
        for pattern, description in irt_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                irt_found.append(description)
            else:
                irt_missing.append(description)
        
        # Validar rangos de parámetros
        has_parameter_validation = bool(re.search(r"0\.5.*2\.0|a.*range|b.*range", content))
        
        details = {
            "irt_patterns_found": len(irt_found),
            "irt_patterns_total": len(irt_patterns),
            "has_parameter_validation": has_parameter_validation,
            "missing_irt_features": irt_missing
        }
        
        if len(irt_found) >= 5:
            self.add_result(
                "IRT_ENGINE_COMPLETENESS",
                "PASS",
                f"Motor IRT completo: {len(irt_found)}/6 características implementadas",
                details
            )
        elif len(irt_found) >= 3:
            self.add_result(
                "IRT_ENGINE_COMPLETENESS",
                "WARNING",
                f"Motor IRT parcial: {len(irt_found)}/6 características",
                details
            )
        else:
            self.add_result(
                "IRT_ENGINE_COMPLETENESS",
                "FAIL",
                f"Motor IRT incompleto: solo {len(irt_found)}/6 características",
                details
            )

    def validate_sql_security(self):
        """Validar medidas de seguridad SQL"""
        sql_files = [
            self.scripts_dir / "final_data_loader.py",
            self.scripts_dir / "offline_sql_generator.py"
        ]
        
        security_patterns = [
            (r"escape_sql_string|quote|sanitize", "Escape de strings SQL"),
            (r"replace.*'.*''", "Escape manual de comillas"),
            (r"\\$[0-9]+", "Parámetros preparados (PostgreSQL)"),
            (r"executemany|execute.*\$", "Prepared statements"),
        ]
        
        total_security_score = 0
        max_security_score = len(security_patterns) * len(sql_files)
        
        file_results = {}
        
        for sql_file in sql_files:
            if not sql_file.exists():
                continue
                
            with open(sql_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_security_score = 0
            found_patterns = []
            
            for pattern, description in security_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    file_security_score += 1
                    found_patterns.append(description)
            
            file_results[sql_file.name] = {
                "score": file_security_score,
                "patterns": found_patterns
            }
            total_security_score += file_security_score
        
        security_percentage = (total_security_score / max_security_score) * 100 if max_security_score > 0 else 0
        
        details = {
            "total_score": total_security_score,
            "max_score": max_security_score,
            "percentage": round(security_percentage, 1),
            "file_results": file_results
        }
        
        if security_percentage >= 75:
            self.add_result(
                "SQL_SECURITY",
                "PASS",
                f"Seguridad SQL adecuada: {security_percentage}% implementada",
                details
            )
        elif security_percentage >= 50:
            self.add_result(
                "SQL_SECURITY",
                "WARNING",
                f"Seguridad SQL parcial: {security_percentage}% implementada",
                details
            )
        else:
            self.add_result(
                "SQL_SECURITY",
                "FAIL",
                f"Seguridad SQL insuficiente: solo {security_percentage}% implementada",
                details
            )

    def validate_sql_load_file(self):
        """Validar el archivo SQL generado"""
        sql_file = self.project_root / "database" / "seed_data" / "complete_questions_load.sql"
        
        if not sql_file.exists():
            self.add_result(
                "SQL_LOAD_FILE",
                "FAIL", 
                "Archivo SQL de carga no encontrado"
            )
            return
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validaciones del archivo SQL
        sql_validations = [
            (r"CREATE TABLE.*questions", "Definición de tabla questions"),
            (r"INSERT INTO questions", "Inserción de datos"),
            (r"irt_difficulty|irt_discrimination|irt_guessing", "Columnas IRT"),
            (r"image_url", "Soporte para imágenes"),
            (r"CREATE INDEX", "Índices para performance"),
            (r"CHECK.*correct_answer.*IN", "Validación de respuesta correcta")
        ]
        
        sql_features = []
        missing_features = []
        
        for pattern, description in sql_validations:
            if re.search(pattern, content, re.IGNORECASE):
                sql_features.append(description)
            else:
                missing_features.append(description)
        
        # Contar número de INSERT statements
        insert_count = len(re.findall(r"INSERT INTO questions|VALUES\s*\(", content, re.IGNORECASE))
        
        file_size_mb = sql_file.stat().st_size / (1024 * 1024)
        
        details = {
            "features_found": len(sql_features),
            "features_total": len(sql_validations),
            "missing_features": missing_features,
            "estimated_inserts": insert_count,
            "file_size_mb": round(file_size_mb, 2)
        }
        
        if len(sql_features) >= 5 and insert_count > 100:
            self.add_result(
                "SQL_LOAD_FILE",
                "PASS",
                f"Archivo SQL completo: {len(sql_features)}/6 características, ~{insert_count} registros",
                details
            )
        elif len(sql_features) >= 4:
            self.add_result(
                "SQL_LOAD_FILE", 
                "WARNING",
                f"Archivo SQL parcial: {len(sql_features)}/6 características",
                details
            )
        else:
            self.add_result(
                "SQL_LOAD_FILE",
                "FAIL",
                f"Archivo SQL incompleto: solo {len(sql_features)}/6 características",
                details
            )

    def run_all_validations(self):
        """Ejecutar todas las validaciones de lógica SQL"""
        self.validate_practice_from_failures_sql()
        self.validate_irt_engine_sql()
        self.validate_sql_security()
        self.validate_sql_load_file()
        
        return self.generate_report()

    def generate_report(self):
        """Generar reporte final"""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        warnings = sum(1 for r in self.results if r["status"] == "WARNING") 
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        
        return {
            "total_tests": total_tests,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "pass_rate": round((passed / total_tests) * 100, 1) if total_tests > 0 else 0,
            "results": self.results
        }

def main():
    """Función principal"""
    validator = SQLLogicValidator()
    report = validator.run_all_validations()
    
    print("\n" + "="*60)
    print("VALIDACION DE LOGICA SQL (SIN CONEXION)")
    print("="*60)
    
    print(f"Tests Totales: {report['total_tests']}")
    print(f"Pasaron: {report['passed']}")
    print(f"Advertencias: {report['warnings']}")
    print(f"Fallaron: {report['failed']}")
    print(f"Tasa de Éxito: {report['pass_rate']}%")
    
    print("\nRESULTADOS DETALLADOS:")
    for result in report["results"]:
        status_symbol = {"PASS": "[OK]", "WARNING": "[WARN]", "FAIL": "[FAIL]"}[result["status"]]
        print(f"{status_symbol} {result['test']}: {result['message']}")
    
    if report["failed"] == 0:
        print("\nLOGICA SQL: VALIDADA CORRECTAMENTE")
        return 0
    else:
        print(f"\nLOGICA SQL: {report['failed']} validaciones fallaron")
        return 1

if __name__ == "__main__":
    exit(main())