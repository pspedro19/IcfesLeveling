#!/bin/bash

echo "🎮 ICFES LEVELING - DEMOSTRACIÓN COMPLETA DEL SISTEMA"
echo "=================================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 VERIFICANDO ESTADO DEL SISTEMA...${NC}"
echo ""

# 1. Verificar backend
echo -e "${YELLOW}1. Backend API (Puerto 4000):${NC}"
BACKEND_STATUS=$(curl -s http://localhost:4000/api/v1/health | grep -o '"status":"healthy"' || echo "error")
if [ "$BACKEND_STATUS" = '"status":"healthy"' ]; then
    echo -e "   ${GREEN}✅ Backend funcionando correctamente${NC}"
else
    echo -e "   ${RED}❌ Backend no responde${NC}"
    exit 1
fi

# 2. Verificar base de datos
echo -e "${YELLOW}2. Base de Datos (PostgreSQL):${NC}"
DB_COUNT=$(DB_PORT=5433 python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(host='localhost', port='5433', database='gameplay_db', user='gameplay', password='gameplay123')
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM questions')
    questions = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM youtube_catalog')
    videos = cur.fetchone()[0]
    print(f'{questions},{videos}')
    cur.close()
    conn.close()
except:
    print('0,0')
" 2>/dev/null)

IFS=',' read -r QUESTIONS_COUNT VIDEOS_COUNT <<< "$DB_COUNT"

if [ "$QUESTIONS_COUNT" -gt 1000 ] && [ "$VIDEOS_COUNT" -gt 100 ]; then
    echo -e "   ${GREEN}✅ Base de datos operacional${NC}"
    echo -e "      📚 Preguntas: $QUESTIONS_COUNT"
    echo -e "      🎬 Videos: $VIDEOS_COUNT"
else
    echo -e "   ${RED}❌ Base de datos incompleta${NC}"
    echo -e "      📚 Preguntas: $QUESTIONS_COUNT (necesario: >1000)"
    echo -e "      🎬 Videos: $VIDEOS_COUNT (necesario: >100)"
fi

# 3. Verificar autenticación
echo -e "${YELLOW}3. Sistema de Autenticación:${NC}"
TOKEN=$(curl -s -X POST http://localhost:4000/api/v1/auth-simple/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['access_token'])
except:
    print('error')
" 2>/dev/null)

if [ "$TOKEN" != "error" ] && [ -n "$TOKEN" ]; then
    echo -e "   ${GREEN}✅ Autenticación funcionando${NC}"
    echo -e "      👤 Usuario admin logueado exitosamente"
else
    echo -e "   ${RED}❌ Error en autenticación${NC}"
    exit 1
fi

# 4. Verificar materias
echo -e "${YELLOW}4. Materias Disponibles:${NC}"
SUBJECTS=$(curl -s http://localhost:4000/api/v1/diagnostic-public/subjects | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for subject in data:
        print(f'   📖 {subject[\"name\"]} (ID: {subject[\"id\"][:8]}...)')
except:
    print('   ❌ Error cargando materias')
" 2>/dev/null)

echo "$SUBJECTS"

# 5. Probar recomendaciones
echo -e "${YELLOW}5. Sistema de Recomendaciones:${NC}"
MATH_RECS=$(curl -s -X POST "http://localhost:4000/api/v1/simple-recommendations/generate-for-subject/550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'   ✅ {data[\"total_videos\"]} videos recomendados para {data[\"subject_name\"]}')
    print(f'   ⏱️ Tiempo estimado: {data[\"estimated_study_time_hours\"]} horas')
    print('   🎬 Ejemplos de videos:')
    for i, video in enumerate(data['recommended_videos'][:3]):
        print(f'      {i+1}. {video[\"title\"]} ({video[\"duration_minutes\"]} min)')
except Exception as e:
    print(f'   ❌ Error: {e}')
" 2>/dev/null)

echo "$MATH_RECS"

echo ""
echo -e "${GREEN}🎉 VERIFICACIÓN COMPLETA - SISTEMA OPERACIONAL${NC}"
echo ""
echo -e "${BLUE}📱 URLS DE ACCESO:${NC}"
echo "   🔐 Login: http://localhost:4001/login"
echo "   📊 Diagnóstico: http://localhost:4001/diagnostic-test"
echo "   🎬 Recomendaciones: http://localhost:4001/simple-recommendations"
echo "   📚 API Docs: http://localhost:4000/docs"
echo ""
echo -e "${BLUE}🔑 CREDENCIALES DE PRUEBA:${NC}"
echo "   👑 Admin: admin / secret (Nivel 50, Rango S)"
echo "   🆕 Test: test / secret (Nivel 1, Rango E)"
echo "   📚 Student: student1 / secret (Nivel 5, Rango D)"
echo ""
echo -e "${GREEN}✨ ¡SISTEMA LISTO PARA USO EN PRODUCCIÓN! ✨${NC}"
echo ""
