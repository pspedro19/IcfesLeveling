# ICFES Database Structure Investigation Report

## Executive Summary

This report provides a thorough investigation of the ICFES question database structure, API serialization, and frontend consumption patterns. The investigation reveals both strengths and critical inconsistencies between the database schema, backend serialization, and frontend expectations.

---

## 1. Question Model Attributes

### File: `/root/IcfesLeveling/apps/backend/app/models/question.py`

#### Primary Option Fields (Lines 21-29)
The Question model uses the following standardized fields for options:

```python
opcion_a_texto = Column(Text, nullable=True)   # Option A text
opcion_a_imagen = Column(String(500), nullable=True)  # Option A image
opcion_b_texto = Column(Text, nullable=True)   # Option B text
opcion_b_imagen = Column(String(500), nullable=True)  # Option B image
opcion_c_texto = Column(Text, nullable=True)   # Option C text
opcion_c_imagen = Column(String(500), nullable=True)  # Option C image
opcion_d_texto = Column(Text, nullable=True)   # Option D text
opcion_d_imagen = Column(String(500), nullable=True)  # Option D image
```

#### Question Content Fields (Lines 17-19)
```python
pregunta_texto = Column(Text, nullable=True)      # Main question text
pregunta_imagen = Column(String(500), nullable=True)  # Main question image
```

#### Answer Field (Line 32)
```python
respuesta_correcta = Column(String(1), nullable=False)  # Correct answer letter (a, b, c, d)
```

#### ICFES-Specific Fields (Lines 56-72)
```python
competencia = Column(String(255), nullable=True)      # ICFES competency
componente = Column(String(100), nullable=True)       # ICFES component
proceso_cognitivo = Column(String(50), nullable=True) # Cognitive process
tipo_conocimiento = Column(String(50), nullable=True) # Knowledge type
afirmacion = Column(Text, nullable=True)              # ICFES affirmation
evidencia = Column(Text, nullable=True)               # ICFES evidence
nivel_desempeno_esperado = Column(String(30), nullable=True)  # Expected performance level
tiempo_estimado = Column(Integer, nullable=True)      # Estimated time in seconds
puntos_xp = Column(Integer, default=10, nullable=True)  # XP points
```

#### IRT (Item Response Theory) Parameters (Lines 62-66)
```python
indice_discriminacion = Column(Float, default=0.5)   # Discrimination index
parametro_irt_a = Column(Float, default=1.0)         # IRT A parameter (discrimination)
parametro_irt_b = Column(Float, default=0.0)         # IRT B parameter (difficulty)
parametro_irt_c = Column(Float, default=0.25)        # IRT C parameter (pseudo-guessing)
```

#### Legacy/Compatibility Fields (Lines 35-42)
```python
question_text = Column(Text, nullable=True)           # Legacy field
question_type = Column(String(50), default="multiple_choice")
difficulty = Column(Integer, nullable=False, default=1)
options = Column(JSON, nullable=True)                 # Legacy JSON options
correct_answer = Column(String(10), nullable=True)    # Legacy correct answer
explanation = Column(Text)
hint = Column(Text)
tags = Column(ARRAY(String))
power_stats = Column(JSON, default={"discrimination_index": 0.5, "success_rate": 0.6})
```

---

## 2. Database Field Names (Field Mapping)

### Primary Fields (ICFES Standard)
| Database Field | Type | Purpose | Notes |
|---|---|---|---|
| `opcion_a_texto` | Text | Option A text content | Primary field, preferred for new data |
| `opcion_a_imagen` | String(500) | Option A image URL | Can contain file path or URL |
| `opcion_b_texto` | Text | Option B text content | Primary field |
| `opcion_b_imagen` | String(500) | Option B image URL | Primary field |
| `opcion_c_texto` | Text | Option C text content | Primary field |
| `opcion_c_imagen` | String(500) | Option C image URL | Primary field |
| `opcion_d_texto` | Text | Option D text content | Primary field |
| `opcion_d_imagen` | String(500) | Option D image URL | Primary field |
| `pregunta_texto` | Text | Question text content | Primary field, Spanish naming |
| `pregunta_imagen` | String(500) | Question image URL | Primary field |
| `respuesta_correcta` | String(1) | Correct answer (a/b/c/d) | Single lowercase letter |

### Legacy Fields (Backward Compatibility)
| Database Field | Type | Purpose | Status |
|---|---|---|---|
| `question_text` | Text | Question text (English naming) | Legacy, fallback only |
| `options` | JSON | Serialized options dict | Legacy, fallback only |
| `correct_answer` | String(10) | Correct answer | Legacy fallback |

---

## 3. Backend Routes: Diagnostic API Serialization

### Route 1: `/diagnostic-questions/{subject_id}` (diagnostic_public.py, Line 903)

**Location**: `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_public.py:903-981`

**What it does**: Returns questions formatted for the diagnostic test interface

**Query Field Extraction Logic** (Lines 922-951):
```python
for letter in ['a', 'b', 'c', 'd']:
    option_text = getattr(q, f'opcion_{letter}_texto')
    option_image = getattr(q, f'opcion_{letter}_imagen')
    
    if option_text or option_image:
        options_data[letter.upper()] = option_text or f"Opción {letter.upper()}"
        if option_image and option_image != "No Aplica":
            option_images[letter.upper()] = f"/api/images/{option_image}"
```

**Response Format** (Lines 953-972):
```json
{
  "id": "uuid-string",
  "question_text": "extracted from pregunta_texto or question_text",
  "pregunta_texto": "same as question_text (for compatibility)",
  "image_url": "/api/images/path (if pregunta_imagen exists)",
  "pregunta_imagen": "same as image_url (for compatibility)",
  "options": {
    "A": "Option A text",
    "B": "Option B text",
    "C": "Option C text",
    "D": "Option D text"
  },
  "option_images": {
    "A": "/api/images/path",
    "B": "/api/images/path"
  },
  "correct_answer": "A (uppercase)",
  "difficulty": 1-10,
  "hint": "hint text",
  "topic": {
    "name": "topic_name",
    "description": "topic_description"
  },
  "subject_id": "uuid",
  "explicacion_respuesta": "explanation text",
  "error_comun": null
}
```

### Route 2: `/diagnostic-questions/submit-answer` (diagnostic_public.py, Line 983)

**Location**: `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_public.py:983-1100+`

**What it does**: Accepts submitted answer and validates against `respuesta_correcta`

**Answer Validation** (Lines 1000-1002):
```python
correct_answer = (question.respuesta_correcta or question.correct_answer or "A").upper()
is_correct = user_answer == correct_answer
```

### Route 3: `/tests/{test_id}/questions` (diagnostic.py, Line 62)

**Location**: `/root/IcfesLeveling/apps/backend/app/routes/diagnostic.py:62-226`

**What it does**: Legacy diagnostic route, returns questions in mixed format

**Response Construction** (Lines 140-176):
- Extracts `pregunta_texto` or falls back to `question_text`
- Builds options array from `opcion_[a-d]_texto` fields
- Includes image URLs for question and options
- Returns format compatible with DiagnosticTestQuestion schema

---

## 4. Question Schema Definitions

### File: `/root/IcfesLeveling/apps/backend/app/schemas/question.py`

#### QuestionBase Schema (Lines 7-36)
```python
class QuestionBase(BaseModel):
    # Main question
    pregunta_texto: Optional[str] = None
    pregunta_imagen: Optional[str] = None
    
    # Options - ICFES standard naming
    opcion_a_texto: Optional[str] = None
    opcion_a_imagen: Optional[str] = None
    opcion_b_texto: Optional[str] = None
    opcion_b_imagen: Optional[str] = None
    opcion_c_texto: Optional[str] = None
    opcion_c_imagen: Optional[str] = None
    opcion_d_texto: Optional[str] = None
    opcion_d_imagen: Optional[str] = None
    
    # Answer
    respuesta_correcta: str  # Validated to be a, b, c, or d
    
    # Legacy fields for backward compatibility
    question_text: Optional[str] = None
    image_url: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    options_images: Optional[Dict[str, str]] = None
```

---

## 5. Frontend Question Interface

### File: `/root/IcfesLeveling/apps/frontend/app/diagnostic-test/test-interface.tsx`

#### Frontend Question Type (Lines 21-44)
```typescript
interface Question {
  id: string;
  question_text: string;                  // Backend sends this
  pregunta_texto?: string;                // Also sent for compatibility
  options?: Record<string, string>;       // Backend sends as dict {A, B, C, D}
  option_images?: Record<string, string>; // Backend sends as dict
  opcion_a_texto?: string;                // Fallback fields
  opcion_b_texto?: string;
  opcion_c_texto?: string;
  opcion_d_texto?: string;
  difficulty: number;
  hint?: string;
  topic?: string | { name: string; description?: string; subject_id?: string };
  image_url?: string;                     // Backend sends this
  pregunta_imagen?: string;               // Also sent for compatibility
  opcion_a_imagen?: string;
  opcion_b_imagen?: string;
  opcion_c_imagen?: string;
  opcion_d_imagen?: string;
  correct_answer?: string;                // Used for client-side validation
  subject_id?: string;
  explicacion_respuesta?: string;
  error_comun?: string;
}
```

#### Frontend Loading Endpoint (Lines 89-126)
```typescript
// Uses: /api/v1/diagnostic-public/diagnostic-questions/{subjectId}?limit=20
const endpoint = `${API_URL}/api/v1/diagnostic-public/diagnostic-questions/${subjectId}?limit=20`;
const data = await fetch(endpoint);
setQuestions(data); // Array of Question objects
```

#### Frontend Answer Submission (Lines 229-244)
```typescript
// Validates against: correct_answer field from backend
const correctCount = questions.filter(q => 
  answers[q.id] === (q.correct_answer || 'A').toUpperCase()
).length;
```

---

## 6. Critical Issues and Mismatches

### ISSUE #1: Answer Verification Mismatch
**Severity**: HIGH

**Problem**: 
- Backend stores correct answer in `respuesta_correcta` (lowercase letter)
- Frontend receives `correct_answer` (uppercase letter)
- Frontend validates: `answers[q.id] === (q.correct_answer || 'A').toUpperCase()`
- This works BUT relies on uppercase conversion

**Location**: 
- Database: `Question.respuesta_correcta`
- Backend endpoint: `/diagnostic-questions/{subject_id}` (Line 961 of diagnostic_public.py)
- Frontend: `test-interface.tsx` Line 323

**Impact**: 
- If `respuesta_correcta` is not properly uppercased before sending, frontend validation will fail
- Tests could show incorrect results

---

### ISSUE #2: Dual Field System Causing Confusion
**Severity**: MEDIUM

**Problem**: Questions can have options in multiple formats:
1. Primary: `opcion_[a-d]_texto` + `opcion_[a-d]_imagen`
2. Legacy: `options` JSON field
3. Legacy: Individual `question_text` field

The backend tries all three:
```python
# Try primary ICFES format
for letter in ['a', 'b', 'c', 'd']:
    option_text = getattr(q, f'opcion_{letter}_texto')
    
# Fallback to legacy
if not options_data and q.options:
    if isinstance(q.options, dict):
        options_data = q.options
```

**Location**: diagnostic_public.py Line 936-951

**Impact**: 
- Inconsistent data quality if imported from multiple sources
- Questions might return empty options if primary fields are NULL but legacy JSON has data
- Data migration difficulties

---

### ISSUE #3: Image Path Inconsistency
**Severity**: MEDIUM

**Problem**:
- Database stores raw file paths/URLs in `pregunta_imagen`, `opcion_[a-d]_imagen`
- Backend converts to: `/api/images/{raw_path}`
- No validation that paths are valid or accessible

```python
# Line 930 of diagnostic_public.py
question_image_url = q.pregunta_imagen
if question_image_url and question_image_url != "No Aplica":
    question_image_url = f"/api/images/{question_image_url}"
```

**Location**: diagnostic_public.py Lines 928-943

**Impact**: 
- Frontend receives 404s if images don't exist
- "No Aplica" string handling is fragile
- No backup/fallback for missing images

---

### ISSUE #4: Missing Response Schema Validation
**Severity**: MEDIUM

**Problem**:
- Endpoint `/diagnostic-questions/{subject_id}` has NO Pydantic response model
- Returns raw dict instead of validated schema
- Frontend doesn't know exact structure guaranteed

```python
# Line 903 - No response_model parameter
@router.get("/diagnostic-questions/{subject_id}")
async def get_diagnostic_test_questions(...)
    # Returns: List[Dict] - not validated!
    return formatted_questions
```

**Location**: diagnostic_public.py Line 903

**Recommended Fix**:
```python
# Create schema
class DiagnosticQuestion(BaseModel):
    id: str
    question_text: str
    options: Dict[str, str]
    option_images: Optional[Dict[str, str]] = {}
    correct_answer: str
    difficulty: int
    hint: Optional[str] = None
    topic: Dict[str, str]
    subject_id: str

# Use it
@router.get("/diagnostic-questions/{subject_id}", response_model=List[DiagnosticQuestion])
async def get_diagnostic_test_questions(...):
    ...
```

---

### ISSUE #5: Correct Answer Field Inconsistency
**Severity**: MEDIUM

**Problem**:
- Database field is `respuesta_correcta` (lowercase letter)
- API response field is `correct_answer` (backend converts)
- Frontend expects `correct_answer` in uppercase

**Current Flow**:
```python
# Line 961 of diagnostic_public.py
"correct_answer": (q.respuesta_correcta or q.correct_answer or "A").upper()
```

**Issue**: If `respuesta_correcta` is 'a', it becomes 'A'. But what if data is inconsistent?

**Location**: diagnostic_public.py Line 961

---

### ISSUE #6: Topic Structure Inconsistency
**Severity**: LOW

**Problem**:
- Backend returns: `"topic": {"name": "...", "description": "..."}`
- Frontend interface expects: `topic?: string | { name: string; ...}`
- Sometimes string, sometimes object

**Location**: 
- Backend: diagnostic_public.py Lines 964-967
- Frontend: test-interface.tsx Lines 33

---

## 7. Data Flow Diagram

```
DATABASE (Question Table)
├── opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto
├── opcion_a_imagen, opcion_b_imagen, opcion_c_imagen, opcion_d_imagen
├── pregunta_texto
├── pregunta_imagen
├── respuesta_correcta (stores: 'a', 'b', 'c', or 'd')
└── (legacy: question_text, options JSON, correct_answer)

                          ↓

BACKEND ROUTE: /diagnostic-questions/{subject_id}
├── Reads: opcion_[a-d]_texto, opcion_[a-d]_imagen
├── Reads: pregunta_texto, pregunta_imagen
├── Reads: respuesta_correcta
├── Converts:
│   ├── respuesta_correcta → correct_answer (uppercase)
│   ├── opcion_[a-d]_texto → options {A, B, C, D}
│   ├── opcion_[a-d]_imagen → option_images {A, B, C, D}
│   ├── pregunta_imagen → image_url (/api/images/...)
│   └── pregunta_texto → question_text
└── Returns: JSON with standardized field names

                          ↓

FRONTEND RECEIVES:
{
  question_text: "¿Cuál es...?",
  options: {A: "text", B: "text", ...},
  option_images: {A: "/api/images/...", ...},
  image_url: "/api/images/...",
  correct_answer: "A"  ← UPPERCASE for validation
}

                          ↓

FRONTEND PROCESSING:
├── Display: question_text + image_url
├── Display options from options dict as radio buttons
├── Show images from option_images dict if available
├── On submit: Compare user_answer.toUpperCase() === correct_answer
└── Calculate score based on matches
```

---

## 8. Working Code Examples

### Backend Query Example
```python
# From diagnostic_public.py
question = db.query(Question).filter(
    Question.subject_id == subject_id
).limit(limit).all()

# Process each question
for q in questions:
    # Get text fields
    question_text = q.pregunta_texto or q.question_text
    
    # Get options
    options_data = {}
    for letter in ['a', 'b', 'c', 'd']:
        option_text = getattr(q, f'opcion_{letter}_texto')
        if option_text:
            options_data[letter.upper()] = option_text
    
    # Get correct answer (properly uppercased)
    correct_answer = (q.respuesta_correcta or "A").upper()
```

### Frontend Consumption Example
```typescript
// From test-interface.tsx
const handleAnswer = async (answer: string) => {
  const currentQuestion = questions[currentQuestionIndex];
  
  // Track answer
  setAnswers(prev => ({
    ...prev,
    [currentQuestion.id]: answer
  }));
  
  // Verify (if needed for immediate feedback)
  const isCorrect = answer.toUpperCase() === 
    (currentQuestion.correct_answer || 'A').toUpperCase();
};

// Final scoring
const correctCount = questions.filter(q => 
  answers[q.id] === (q.correct_answer || 'A').toUpperCase()
).length;
```

---

## 9. Summary of Field Name Mappings

### Complete Field Mapping Reference

| Purpose | Database Field | Schema Field | API Response Field | Frontend Receives |
|---------|---|---|---|---|
| **Question Text** | `pregunta_texto` | `pregunta_texto` | `question_text` | `question_text` |
| **Question Image** | `pregunta_imagen` | `pregunta_imagen` | `image_url` | `image_url` |
| **Option A Text** | `opcion_a_texto` | `opcion_a_texto` | `options.A` | `options.A` |
| **Option A Image** | `opcion_a_imagen` | `opcion_a_imagen` | `option_images.A` | `option_images.A` |
| **Option B Text** | `opcion_b_texto` | `opcion_b_texto` | `options.B` | `options.B` |
| **Option B Image** | `opcion_b_imagen` | `opcion_b_imagen` | `option_images.B` | `option_images.B` |
| **Option C Text** | `opcion_c_texto` | `opcion_c_texto` | `options.C` | `options.C` |
| **Option C Image** | `opcion_c_imagen` | `opcion_c_imagen` | `option_images.C` | `option_images.C` |
| **Option D Text** | `opcion_d_texto` | `opcion_d_texto` | `options.D` | `options.D` |
| **Option D Image** | `opcion_d_imagen` | `opcion_d_imagen` | `option_images.D` | `option_images.D` |
| **Correct Answer** | `respuesta_correcta` | `respuesta_correcta` | `correct_answer` (uppercase) | `correct_answer` |

---

## 10. Recommendations

### Priority 1: Critical Issues
1. **Add response model validation** to `/diagnostic-questions/{subject_id}` endpoint
2. **Normalize answer field handling** - ensure consistency between `respuesta_correcta` and `correct_answer`
3. **Add image validation** - verify image paths exist before returning to frontend

### Priority 2: Important
1. **Create migration** - consolidate legacy `options` JSON into primary fields
2. **Add fallback handling** - what to do when primary fields are NULL
3. **Add comprehensive logging** - track which data paths are being used

### Priority 3: Nice to Have
1. **Create separate schema** for serialized vs. database models
2. **Add caching** for frequently accessed questions
3. **Add data quality metrics** - track % of questions with images, etc.

---

## 11. Conclusion

The ICFES database structure for questions is functional but exhibits:
- **Strengths**: Comprehensive ICFES-specific fields, flexible storage for multimedia
- **Weaknesses**: Dual field systems causing confusion, lack of validation layers, inconsistent naming

The backend successfully bridges the database schema to the frontend's expectations, but the lack of Pydantic validation and response models creates brittleness. The frontend correctly handles the current API responses but would benefit from more consistent field naming conventions.

**Overall Assessment**: System works correctly but needs refactoring for maintainability.

