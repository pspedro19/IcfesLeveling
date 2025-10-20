# ICFES Database Structure - Quick Reference Guide

## TL;DR - Key Field Names

### Question Options in Database
- **Primary format**: `opcion_a_texto`, `opcion_b_texto`, `opcion_c_texto`, `opcion_d_texto`
- **Option images**: `opcion_a_imagen`, `opcion_b_imagen`, `opcion_c_imagen`, `opcion_d_imagen`
- **Question text**: `pregunta_texto`
- **Question image**: `pregunta_imagen`
- **Correct answer**: `respuesta_correcta` (stores single letter: a, b, c, or d)

### How Options Get to Frontend

```
Database: opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto
    ↓
Backend transforms: {"A": text_a, "B": text_b, "C": text_c, "D": text_d}
    ↓
Frontend receives: options = {A: "...", B: "...", C: "...", D: "..."}
```

## Critical Field Transformations

| Stage | Field Name | Value Type | Example |
|-------|-----------|-----------|---------|
| **Database** | `respuesta_correcta` | Single char (lowercase) | `"a"` |
| **API Response** | `correct_answer` | Single char (uppercase) | `"A"` |
| **Frontend Input** | User click on radio | Uppercase string | `"A"` |
| **Frontend Comparison** | Validated answer | Uppercase string | `answers[q.id] === "A"` |

## The Backend Serialization Process

### Location: `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_public.py`

**Lines 922-951** - Extract individual option fields and transform to dict:
```python
options_data = {}
for letter in ['a', 'b', 'c', 'd']:
    option_text = getattr(q, f'opcion_{letter}_texto')
    option_image = getattr(q, f'opcion_{letter}_imagen')
    
    if option_text or option_image:
        options_data[letter.upper()] = option_text  # Note: uppercase key
```

**Line 961** - Ensure answer is uppercase:
```python
"correct_answer": (q.respuesta_correcta or q.correct_answer or "A").upper()
```

## What Frontend Actually Receives

When calling `/api/v1/diagnostic-public/diagnostic-questions/{subject_id}`:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "question_text": "¿Cuál es la fórmula...?",
  "options": {
    "A": "Opción A texto",
    "B": "Opción B texto",
    "C": "Opción C texto",
    "D": "Opción D texto"
  },
  "option_images": {
    "A": "/api/images/path/to/imageA.png",
    "B": "/api/images/path/to/imageB.png"
  },
  "image_url": "/api/images/path/to/question.png",
  "correct_answer": "A",
  "difficulty": 5,
  "hint": "Recuerda la...",
  "topic": {"name": "Álgebra", "description": "..."}
}
```

## Frontend Processing

### How Frontend Displays Questions

```typescript
// Get options dict
const optionLabels = ["A", "B", "C", "D"];
optionLabels.forEach(label => {
  const text = currentQuestion.options[label];
  const img = currentQuestion.option_images?.[label];
  // Render as radio button with optional image
});

// Display question
<div>{currentQuestion.image_url && <img src={currentQuestion.image_url} />}</div>
<div>{currentQuestion.question_text}</div>
```

### How Frontend Validates Answers

```typescript
// When user clicks an option, answer is stored as uppercase letter
setAnswers(prev => ({
  ...prev,
  [currentQuestion.id]: "A"  // uppercase
}));

// Final scoring
const correctCount = questions.filter(q => 
  answers[q.id] === (q.correct_answer || 'A').toUpperCase()
).length;
```

## The 6 Critical Issues

### Issue #1: HIGH SEVERITY - Answer Validation Depends on .toUpperCase()
- Database stores lowercase (`a`, `b`, `c`, `d`)
- Backend must uppercase it (line 961 of diagnostic_public.py)
- Frontend must uppercase user input for comparison
- If ANY step fails, scoring is incorrect

### Issue #2: MEDIUM - Dual Option Storage
Options can exist in THREE places:
1. Primary ICFES: `opcion_[a-d]_texto` + `opcion_[a-d]_imagen`
2. Legacy: `options` JSON field
3. Legacy: `question_text` field

Backend tries all three in order. If data is in multiple formats, unpredictable behavior.

### Issue #3: MEDIUM - No Response Schema Validation
Endpoint has NO `response_model` parameter, so Pydantic doesn't validate the structure sent to frontend.

### Issue #4: MEDIUM - Image Path Processing
- Backend just prepends `/api/images/` to stored paths
- No validation that images actually exist
- Frontend gets 404s if images aren't accessible

### Issue #5: MEDIUM - Topic Structure Varies
Backend returns topic as: `{"name": "...", "description": "..."}`
Frontend expects it to sometimes be a string, sometimes an object.

### Issue #6: LOW - Field Name Inconsistency
Database field: `pregunta_texto`
Schema field: `pregunta_texto`
API field: `question_text`
Another copy: `pregunta_texto` (for compatibility)

## Most Important: The OPTIONS Dict

### How to Access Options in Frontend Code

```typescript
// Correct
const optionA = question.options["A"];
const optionB = question.options["B"];

// Also works
const { options } = question;
const allOptions = Object.entries(options).map(([letter, text]) => ({
  letter,
  text,
  image: question.option_images?.[letter]
}));
```

### Structure Guarantee
```typescript
options: {
  "A": "string text for option A",
  "B": "string text for option B",
  "C": "string text for option C",
  "D": "string text for option D"
}
```

Each option is ALWAYS present in the dict (guaranteed by backend logic at line 937-943).

## Database Schema Locations

**Model Definition**: `/root/IcfesLeveling/apps/backend/app/models/question.py`
- Lines 21-29: Primary option fields
- Line 32: `respuesta_correcta` field
- Lines 17-19: Question content fields

**Schema Definition**: `/root/IcfesLeveling/apps/backend/app/schemas/question.py`
- Lines 7-36: QuestionBase with all field names

**API Serialization**: `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_public.py`
- Lines 903-981: The `/diagnostic-questions/{subject_id}` endpoint
- Lines 922-951: Option extraction and transformation
- Line 961: Answer uppercase conversion

**Frontend Type**: `/root/IcfesLeveling/apps/frontend/app/diagnostic-test/test-interface.tsx`
- Lines 21-44: Question interface definition
- Lines 89-126: Loading endpoint call
- Line 323: Answer validation logic

## Key Code Snippets

### Extract Options Like Backend Does
```python
# Backend method
options_data = {}
for letter in ['a', 'b', 'c', 'd']:
    option_text = getattr(question, f'opcion_{letter}_texto')
    if option_text:
        options_data[letter.upper()] = option_text
```

### Validate Answer Like Frontend Does
```typescript
const isCorrect = userAnswer.toUpperCase() === 
  (question.correct_answer || 'A').toUpperCase();
```

### Fallback Chain for Question Text
```python
# What backend does
question_text = q.pregunta_texto or q.question_text or ""
```

## Quick Debugging Checklist

- [ ] Check `respuesta_correcta` is lowercase in database (a, b, c, d)
- [ ] Verify `opcion_[a-d]_texto` fields are NOT NULL
- [ ] Ensure backend line 961 uppercases the answer before sending
- [ ] Verify frontend calls `.toUpperCase()` on user input
- [ ] Check that `/api/images/` paths are valid on server
- [ ] Test with actual questions that have both options dict AND individual fields populated
- [ ] Verify response matches the expected structure in test-interface.tsx

## File Cross-Reference

| Task | File | Lines |
|------|------|-------|
| See database schema | question.py (model) | 10-100 |
| See API response structure | diagnostic_public.py | 922-972 |
| See frontend expectations | test-interface.tsx | 21-44 |
| See answer validation | diagnostic_public.py | 1000-1002 |
| See options extraction | diagnostic_public.py | 936-943 |
| See answer submission | test-interface.tsx | 315-324 |

