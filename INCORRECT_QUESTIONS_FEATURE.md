# Nueva Funcionalidad: Visualización de Preguntas Incorrectas ✅

## Descripción

Se ha implementado una funcionalidad visual que muestra las preguntas que el estudiante falló en el diagnóstico, directamente en cada unidad del plan de estudio. Esto permite al estudiante:

1. **Ver exactamente qué preguntas falló**
2. **Entender por qué esos videos le ayudarán**
3. **Hacer la conexión directa**: Pregunta fallada → Competencia/Componente → Video recomendado

## Cambios Implementados

### Backend (`claude_study_plan_generator.py`)

#### 1. Nueva Query para Obtener Preguntas Incorrectas (Línea 207-222)

```python
incorrect_questions_query = text("""
    SELECT
        q.id as question_id,
        q.pregunta_texto,
        q.competencia,
        q.componente,
        t.name as topic_name,
        q.explanation
    FROM diagnostic_test_answers dta
    JOIN questions q ON dta.question_id = q.id
    LEFT JOIN topics t ON q.topic_id = t.id
    WHERE dta.diagnostic_test_id = :test_id
    AND dta.is_correct = false
    ORDER BY q.competencia, q.componente
    LIMIT 20
""")
```

**Features**:
- Obtiene el texto completo de la pregunta
- Incluye competencia y componente ICFES
- Limita a 20 preguntas para no sobrecargar la UI
- Incluye el nombre del tema (topic)

#### 2. Asociación de Preguntas a Unidades (Línea 385-393)

```python
"incorrect_questions": [
    q for q in incorrect_questions
    if any(
        (q['competencia'] and q['competencia'] in video.get('competence_match', '')) or
        (q['componente'] and q['componente'] in video.get('component_match', '')) or
        (q['topic_name'] in unit_rec.get('failed_topics_covered', []))
        for video in unit_videos
    )
][:3]  # Limit to 3 questions per unit for display
```

**Lógica de Matching**:
- Busca preguntas cuya competencia coincida con los videos de la unidad
- Busca preguntas cuyo componente coincida con los videos de la unidad
- Busca preguntas cuyo tema esté cubierto por la unidad
- **Limita a 3 preguntas por unidad** para mantener la UI limpia

#### 3. Truncamiento del Texto (Línea 230)

```python
"pregunta_texto": (row[1] or "Pregunta sin texto")[:150] + ("..." if len(row[1] or "") > 150 else ""),
```

Trunca el texto a 150 caracteres para evitar bloques de texto muy largos en la UI.

### Frontend (`claude-study-plan/page.tsx`)

#### 1. Nueva Interfaz TypeScript (Línea 24-32)

```typescript
interface IncorrectQuestion {
  id: string;
  pregunta_texto: string;
  competencia: string;
  componente: string;
  topic_name: string;
  difficulty_level: number;
  explanation: string;
}
```

#### 2. Actualización de ClaudeUnit Interface (Línea 42)

```typescript
interface ClaudeUnit {
  // ... otros campos
  incorrect_questions?: IncorrectQuestion[];  // Nuevo campo opcional
}
```

#### 3. Componente Visual de Preguntas (Línea 381-435)

```tsx
{/* Preguntas Incorrectas */}
{unit.incorrect_questions && unit.incorrect_questions.length > 0 && (
  <div className="mb-6 bg-gradient-to-br from-red-900/20 to-orange-900/20 border border-red-500/30 rounded-lg p-4">
    <h4 className="font-semibold text-red-400 mb-3 flex items-center">
      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        {/* Warning icon */}
      </svg>
      Preguntas que Fallaste en el Diagnóstico
    </h4>

    {/* Grid de preguntas */}
    <div className="space-y-3">
      {unit.incorrect_questions.map((question, qIdx) => (
        <div key={question.id} className="bg-black/40 rounded-lg p-3 border-l-4 border-red-500">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-red-500/20 rounded-full flex items-center justify-center">
              <span className="text-red-400 font-bold text-sm">{qIdx + 1}</span>
            </div>
            <div className="flex-1">
              <p className="text-sm text-white mb-2">{question.pregunta_texto}</p>

              {/* Badges de competencia, componente y tema */}
              <div className="flex flex-wrap gap-2 text-xs">
                {question.competencia && (
                  <span className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded">
                    📚 {question.competencia}
                  </span>
                )}
                {question.componente && (
                  <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded">
                    🎯 {question.componente}
                  </span>
                )}
                {question.topic_name && (
                  <span className="px-2 py-1 bg-orange-500/20 text-orange-300 rounded">
                    📖 {question.topic_name}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>

    {/* Explicación de cómo ayudan los videos */}
    <div className="mt-3 flex items-start gap-2 bg-green-500/10 border border-green-500/30 rounded p-3">
      <svg className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        {/* Check circle icon */}
      </svg>
      <p className="text-xs text-green-300">
        <strong>¿Cómo te ayudan estos videos?</strong> Los videos recomendados cubren exactamente
        las competencias y componentes donde tuviste dificultades. Al verlos y practicar,
        mejorarás en estas áreas específicas.
      </p>
    </div>
  </div>
)}
```

## Diseño Visual

### Elementos de Diseño

1. **Contenedor Principal**
   - Fondo gradiente: `from-red-900/20 to-orange-900/20`
   - Border rojo: `border-red-500/30`
   - Indica visualmente que son errores

2. **Cabecera con Ícono**
   - Ícono de advertencia (triángulo)
   - Texto: "Preguntas que Fallaste en el Diagnóstico"
   - Color rojo para llamar la atención

3. **Tarjetas de Preguntas**
   - Numeradas (1, 2, 3...)
   - Texto de la pregunta truncado
   - Border izquierdo rojo (`border-l-4 border-red-500`)
   - Badges de colores:
     - 📚 Competencia (azul)
     - 🎯 Componente (morado)
     - 📖 Tema (naranja)

4. **Mensaje de Ayuda**
   - Fondo verde claro
   - Ícono de check
   - Explica cómo los videos ayudarán

## Ejemplo de Uso

### Caso de Uso: Estudiante de Ciencias Naturales

```
Unidad 1: Procesos Celulares
├── Preguntas que Fallaste en el Diagnóstico
│   ├── 1. ¿Cuál es la función principal de la mitocondria?
│   │   📚 Uso comprensivo del conocimiento científico
│   │   🎯 Entorno vivo
│   │   📖 Biología celular
│   │
│   ├── 2. Explique el proceso de fotosíntesis...
│   │   📚 Explicación de fenómenos
│   │   🎯 Entorno vivo
│   │   📖 Fotosíntesis
│   │
│   └── 3. ¿Qué es la respiración celular?
│       📚 Uso comprensivo del conocimiento científico
│       🎯 Entorno vivo
│       📖 Respiración celular
│
├── ¿Cómo te ayudan estos videos?
│   Los videos cubren exactamente las competencias donde tuviste dificultades...
│
└── Videos Recomendados
    ├── 📺 Procesos vitales - Respiracion celular (Crash Course)
    ├── 📺 Fotosíntesis (Es Ciencia)
    └── 📺 Estructura celular (unProfesor)
```

## Beneficios para el Usuario

1. **Transparencia Total**
   - El estudiante ve exactamente qué preguntas falló
   - Entiende la conexión con los videos recomendados

2. **Motivación**
   - Ver preguntas específicas motiva a estudiar
   - Hace el aprendizaje más concreto

3. **Aprendizaje Dirigido**
   - Enfoque en áreas específicas de debilidad
   - Conexión clara entre problema → solución

4. **Feedback Visual**
   - Colores ayudan a identificar rápidamente:
     - Rojo = Errores
     - Azul = Competencias
     - Morado = Componentes
     - Naranja = Temas
     - Verde = Solución

## Testing

### Verificación Funcional

```bash
# Test con Ciencias Naturales
curl -X POST http://localhost:4000/api/v1/claude-study-plan/generate \
  -H "Content-Type: application/json" \
  -d '{"test_id": "60803ee4-6fcd-88c3-6bd9-55eef63ecaf2", "subject_id": "550e8400-e29b-41d4-a716-446655440003"}'
```

**Resultado Esperado**:
- `success: true`
- 4 unidades generadas
- Primera unidad tiene 3 preguntas incorrectas
- Cada pregunta incluye: texto, competencia, componente, tema

### Resultado de Testing

```json
{
  "success": true,
  "units": 4,
  "first_unit_has_questions": 3
}
```

✅ **Verificado**: La funcionalidad está operativa y funcionando correctamente.

## Archivos Modificados

### Backend
- `/root/IcfesLeveling/apps/backend/app/routes/claude_study_plan_generator.py`
  - Líneas 206-238: Nueva query y procesamiento de preguntas incorrectas
  - Líneas 385-395: Asociación de preguntas a unidades

### Frontend
- `/root/IcfesLeveling/apps/frontend/app/claude-study-plan/page.tsx`
  - Líneas 24-32: Nueva interfaz TypeScript
  - Líneas 381-435: Componente visual de preguntas incorrectas

## Próximas Mejoras Sugeridas

1. **Expandir/Colapsar Preguntas**
   - Permitir al usuario colapsar la sección de preguntas
   - Útil si hay muchas preguntas

2. **Link a Explicación**
   - Mostrar la explicación de por qué la respuesta era incorrecta
   - Requiere que el campo `explanation` esté poblado en la DB

3. **Filtro por Dificultad**
   - Agregar indicador de dificultad de la pregunta
   - Requiere usar el campo `difficulty` de la tabla

4. **Estadísticas**
   - Mostrar % de error por competencia/componente
   - Gráfico de radar de fortalezas/debilidades

## Conclusión

Esta funcionalidad transforma el plan de estudio de una lista genérica de videos a una **herramienta de aprendizaje personalizada y justificada**. El estudiante ahora puede:

1. ✅ Ver qué preguntas falló
2. ✅ Entender por qué falló (competencia/componente)
3. ✅ Conectar directamente con los videos que lo ayudarán
4. ✅ Visualizar el progreso de manera más significativa

---

**Fecha de Implementación**: 2025-10-20
**Desarrollado por**: Claude Code Assistant
**Estado**: ✅ COMPLETADO Y VERIFICADO
