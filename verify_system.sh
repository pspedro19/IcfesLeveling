#!/bin/bash

echo "=========================================="
echo "VERIFICACIÓN DEL SISTEMA ICFES LEVELING"
echo "=========================================="

# 1. Verificar subjects en BD
echo -e "\n1. Subjects en base de datos:"
docker exec icfes_postgres psql -U gameplay -d gameplay_db -c "
SELECT id, name, color FROM subjects ORDER BY name;"

# 2. Verificar preguntas totales
echo -e "\n2. Total de preguntas:"
docker exec icfes_postgres psql -U gameplay -d gameplay_db -c "
SELECT COUNT(*) as total_questions FROM questions;"

# 3. Verificar distribución por materia
echo -e "\n3. Distribución de preguntas por materia:"
docker exec icfes_postgres psql -U gameplay -d gameplay_db -c "
SELECT
  s.name as materia,
  COUNT(q.id) as preguntas
FROM subjects s
LEFT JOIN questions q ON s.id = q.subject_id
GROUP BY s.id, s.name
ORDER BY s.name;"

# 4. Verificar archivo Excel
echo -e "\n4. Archivo Excel de preguntas:"
docker exec icfes_backend ls -lh /app/seed_data/questions.xlsx 2>/dev/null && echo "✅ Archivo encontrado" || echo "❌ Archivo NO encontrado"

# 5. Verificar variables de entorno
echo -e "\n5. Variables de entorno del backend:"
docker exec icfes_backend bash -c 'echo "AUTO_IMPORT_QUESTIONS: $AUTO_IMPORT_QUESTIONS"'
docker exec icfes_backend bash -c 'echo "QUESTIONS_EXCEL_PATH: $QUESTIONS_EXCEL_PATH"'

# 6. Probar endpoint
echo -e "\n6. Prueba de endpoint /diagnostic-public/subjects:"
curl -s http://localhost:4000/diagnostic-public/subjects | python3 -m json.tool 2>/dev/null | head -30

echo -e "\n=========================================="
echo "VERIFICACIÓN COMPLETADA"
echo "=========================================="
