# ICFES Diagnostic Test System - Question Data Structure & Flow Investigation

**Investigation Date:** 2025-10-20  
**Scope:** Frontend components, API endpoints, data transformation pipeline  
**Thoroughness Level:** Very Thorough

---

## Executive Summary

The ICFES diagnostic test system has **multiple question display pathways** with a layered architecture:
1. **Frontend (React/Next.js)** - Multiple test interfaces
2. **Backend API (FastAPI)** - Multiple diagnostic endpoints  
3. **Database (PostgreSQL)** - Question model with option text fields

The investigation reveals several **critical issues** in the data flow from DB → Backend → Frontend that likely cause option text display problems.

---

## 1. FRONTEND COMPONENTS ANALYSIS

### 1.1 Main Frontend Files
Location: `/root/IcfesLeveling/apps/frontend/app/diagnostic-test/`

**Files Identified:**
- `page.tsx` - Subject selection interface
- `test-interface.tsx` - Primary test display component
- `test-flow.tsx` - Legacy test flow component
- `results/page.tsx` - Results display

### 1.2 Primary Test Interface: `test-interface.tsx` (MAIN COMPONENT)

**Key Findings:**

```typescript
// Lines 21-44: Question Interface Definition
interface Question {
  id: string;
  question_text: string;
  pregunta_texto?: string;
  options?: Record<string, string>;           // Dict format: {A: text, B: text, ...}
  option_images?: Record<string, string>;     // Dict format for option images
  opcion_a_texto?: string;                    // Direct field names
  opcion_b_texto?: string;
  opcion_c_texto?: string;
  opcion_d_texto?: string;
  opcion_a_imagen?: string;                   // Direct image field names
  opcion_b_imagen?: string;
  opcion_c_imagen?: string;
  opcion_d_imagen?: string;
  correct_answer?: string;
  // ... other fields
}
```

**Option Rendering Logic (Lines 458-487):**

```typescript
// Lines 458-460: Extract options from response
const optionsData = currentQuestion.options || {};
const optionImages = currentQuestion.option_images || {};

// Lines 463-472: Create options array with fallback to direct fields
const options = ['A', 'B', 'C', 'D'].map(key => {
  const imageField = optionImages[key] || currentQuestion[`opcion_${key.toLowerCase()}_imagen`];
  const textField = optionsData[key] || currentQuestion[`opcion_${key.toLowerCase()}_texto`];
  
  return {
    letter: key,
    text: textField || '',
    image: getImageUrl(imageField || '')
  };
});

// Lines 474-487: Validation and fallback to placeholder options
const validOptions = options.filter(option => {
  const hasText = option.text && option.text.trim() !== '' && option.text !== `Opción ${option.letter}`;
  const hasImage = option.image && option.image.trim() !== '';
  return hasText || hasImage;
});

// FALLBACK: If no valid options found, creates placeholder options!
const finalOptions = validOptions.length >= 2 ? validOptions : [
  { letter: 'A', text: 'Opción A', image: '' },
  { letter: 'B', text: 'Opción B', image: '' },
  { letter: 'C', text: 'Opción C', image: '' },
  { letter: 'D', text: 'Opción D', image: '' },
];
```

**CRITICAL ISSUE #1:** The fallback mechanism means if the API returns empty/null option text, the frontend will show generic "Opción A/B/C/D" instead of failing visibly.

**Option Display (Lines 728-782):**
```typescript
{finalOptions.map((option) => {
  const isSelected = answers[currentQuestion.id] === option.letter;
  
  return (
    <motion.button>
      <span>{option.letter}</span>
      <div className="flex-1">
        <span className="text-lg block">{option.text}</span>  // DISPLAYS: option.text
        
        {/* Option Image */}
        {option.image && (
          <div className="mt-3">
            <img 
              src={option.image} 
              alt={`Imagen opción ${option.letter}`}
              // ...
            />
          </div>
        )}
      </div>
    </motion.button>
  );
})}
```

### 1.3 API Endpoint Called: `/diagnostic-public/diagnostic-questions/{subject_id}`

**In test-interface.tsx (Line 97):**
```typescript
const endpoint = `${API_URL}/api/v1/diagnostic-public/diagnostic-questions/${subjectId}?limit=20`;
```

---

## 2. BACKEND API ANALYSIS

### 2.1 Backend File Locations
- `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_public.py` - Main diagnostic API
- `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_images_test.py` - Image test endpoint

### 2.2 Primary Endpoint: `/diagnostic-questions/{subject_id}` 

**Location:** `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_public.py` (Lines 903-981)

```python
@router.get("/diagnostic-questions/{subject_id}")
async def get_diagnostic_test_questions(
    subject_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get properly formatted questions for diagnostic test interface"""
    try:
        questions = db.query(Question).filter(
            Question.subject_id == subject_id
        ).limit(limit).all()
        
        # ... code ...
        
        formatted_questions = []
        for q in questions:
            # Get the question text
            question_text = q.pregunta_texto or q.question_text or ""
            
            # Get question image URL
            question_image_url = q.pregunta_imagen
            if question_image_url and question_image_url != "No Aplica":
                question_image_url = f"/api/images/{question_image_url}"
            
            # FORMAT OPTIONS - CRITICAL SECTION (Lines 932-951)
            options_data = {}
            option_images = {}
            
            for letter in ['a', 'b', 'c', 'd']:
                option_text = getattr(q, f'opcion_{letter}_texto')  # Gets field directly
                option_image = getattr(q, f'opcion_{letter}_imagen')
                
                if option_text or option_image:
                    options_data[letter.upper()] = option_text or f"Opción {letter.upper()}"
                    if option_image and option_image != "No Aplica":
                        option_images[letter.upper()] = f"/api/images/{option_image}"
            
            # Fallback to legacy options
            if not options_data and q.options:
                if isinstance(q.options, dict):
                    options_data = q.options
                elif isinstance(q.options, list):
                    for i, opt in enumerate(q.options):
                        options_data[chr(65 + i)] = opt
            
            formatted_question = {
                "id": str(q.id),
                "question_text": question_text,
                "pregunta_texto": question_text,
                "image_url": question_image_url,
                "pregunta_imagen": question_image_url,
                "options": options_data,                    # KEY FIELD
                "option_images": option_images,             # KEY FIELD
                "correct_answer": (q.respuesta_correcta or q.correct_answer or "A").upper(),
                "difficulty": q.difficulty or 1,
                "hint": q.hint,
                "topic": { ... },
                "subject_id": str(q.subject_id),
                "explicacion_respuesta": getattr(q, 'explanation', None),
                "error_comun": None
            }
            
            formatted_questions.append(formatted_question)
        
        return formatted_questions
```

**CRITICAL ISSUE #2:** If `opcion_a_texto`, `opcion_b_texto`, etc. are NULL in the database, the `options_data` dict will be empty {}, and then the backend falls back to legacy `q.options` field. If that's also empty/missing, the frontend receives `{ "options": {} }` which causes the fallback to generic placeholder text.

### 2.3 Alternative Endpoint: `/diagnostic-images-test/questions/{subject_id}`

**Location:** `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_images_test.py` (Lines 93-192)

This endpoint has a DIFFERENT response format:

```python
question_data = {
    "id": str(q.id),
    "pregunta_texto": q.pregunta_texto,
    "opcion_a": q.opcion_a_texto,        # Direct field - NOT in dict format!
    "opcion_b": q.opcion_b_texto,
    "opcion_c": q.opcion_c_texto,
    "opcion_d": q.opcion_d_texto,
    "respuesta_correcta": q.respuesta_correcta,
    "pregunta_imagen": q.pregunta_imagen if q.pregunta_imagen and q.pregunta_imagen.strip() and q.pregunta_imagen != "No Aplica" else None,
    "opcion_a_imagen": q.opcion_a_imagen if q.opcion_a_imagen and q.opcion_a_imagen.strip() and q.opcion_a_imagen != "No Aplica" else None,
    "opcion_b_imagen": q.opcion_b_imagen if q.opcion_b_imagen and q.opcion_b_imagen.strip() and q.opcion_b_imagen != "No Aplica" else None,
    "opcion_c_imagen": q.opcion_c_imagen if q.opcion_c_imagen and q.opcion_c_imagen.strip() and q.opcion_c_imagen != "No Aplica" else None,
    "opcion_d_imagen": q.opcion_d_imagen if q.opcion_d_imagen and q.opcion_d_imagen.strip() and q.opcion_d_imagen != "No Aplica" else None,
}

response = {
    "subject": { ... },
    "questions": questions_data,
    "test_config": { ... }
}
```

**CRITICAL ISSUE #3:** This endpoint returns questions in a DIFFERENT format with `questions` nested inside a wrapper object, but the frontend test-interface.tsx expects a flat array!

### 2.4 Route Registration in main.py

**Line 413-414:**
```python
app.include_router(diagnostic_public.router)  # Without /api/v1 prefix
app.include_router(diagnostic_public.router, prefix="/api/v1")  # With /api/v1 prefix
```

The routes are registered twice - with and without prefix, causing potential routing conflicts.

---

## 3. DATABASE MODEL ANALYSIS

### 3.1 Question Model: `/root/IcfesLeveling/apps/backend/app/models/question.py`

**Option Text Fields (Lines 17-29):**

```python
class Question(Base):
    __tablename__ = "questions"
    
    # Campos de texto de la pregunta
    pregunta_texto = Column(Text, nullable=True)
    pregunta_imagen = Column(String(500), nullable=True)
    
    # Campos de texto de las opciones
    opcion_a_texto = Column(Text, nullable=True)  # NULLABLE!
    opcion_a_imagen = Column(String(500), nullable=True)
    opcion_b_texto = Column(Text, nullable=True)  # NULLABLE!
    opcion_b_imagen = Column(String(500), nullable=True)
    opcion_c_texto = Column(Text, nullable=True)  # NULLABLE!
    opcion_c_imagen = Column(String(500), nullable=True)
    opcion_d_texto = Column(Text, nullable=True)  # NULLABLE!
    opcion_d_imagen = Column(String(500), nullable=True)
    
    # Respuesta correcta
    respuesta_correcta = Column(String(1), nullable=False)
    
    # Legacy fields for compatibility
    question_text = Column(Text, nullable=True)
    options = Column(JSON, nullable=True)  # Legacy options format
    correct_answer = Column(String(10), nullable=True)
```

**CRITICAL ISSUE #4:** All option text fields are `nullable=True`, meaning they can be NULL in the database. If they're not populated during data import, the entire question lacks option text!

---

## 4. DATA FLOW DIAGRAM

```
DATABASE (PostgreSQL)
  Question table
    ├─ pregunta_texto (nullable)
    ├─ opcion_a_texto (nullable) ❌ OFTEN NULL
    ├─ opcion_b_texto (nullable) ❌ OFTEN NULL
    ├─ opcion_c_texto (nullable) ❌ OFTEN NULL
    ├─ opcion_d_texto (nullable) ❌ OFTEN NULL
    ├─ opcion_a_imagen (nullable)
    ├─ opcion_b_imagen (nullable)
    ├─ options (JSON, legacy)
    └─ correct_answer (legacy)

        ↓↓↓ BACKEND ENDPOINT

API ENDPOINT #1: /diagnostic-public/diagnostic-questions/{subject_id}
  (diagnostic_public.py, lines 903-981)
  
  TRANSFORMATION LOGIC:
  ├─ IF opcion_x_texto IS NOT NULL
  │   └─ options_data[letter] = opcion_x_texto ✓
  ├─ ELSE IF legacy q.options exists
  │   └─ options_data[letter] = q.options[letter] ✓
  └─ ELSE
      └─ options_data = {} ❌ EMPTY!
  
  RESPONSE FORMAT:
  {
    "id": "...",
    "question_text": "...",
    "options": {
      "A": "Option text or NULL missing",
      "B": "...",
      "C": "...",
      "D": "..."
    },
    "option_images": { ... }
  }

        ↓↓↓ FRONTEND RECEIVES

FRONTEND: test-interface.tsx (lines 458-487)
  
  PROCESSING:
  ├─ optionsData = response.options || {} 
  ├─ Create options array from optionsData
  │  └─ IF optionsData is empty
  │     └─ options will have empty text fields ❌
  ├─ VALIDATION: Check if option has text or image
  │  └─ IF neither exists
  │     └─ REMOVE from validOptions
  └─ FALLBACK: IF validOptions.length < 2
      └─ SHOW PLACEHOLDER: "Opción A/B/C/D" 🚨

  RENDERED OUTPUT:
  Display either:
  - Real option text (if API returned it)
  - Placeholder text "Opción A/B/C/D" (if API returned empty)
```

---

## 5. IDENTIFIED ISSUES & ROOT CAUSES

### Issue #1: NULL Option Text Fields in Database
**Root Cause:** Data import process doesn't populate `opcion_x_texto` fields  
**Impact:** Questions lack option text in display  
**Severity:** CRITICAL

### Issue #2: Empty `options_data` Dict When Fields Are NULL
**Root Cause:** Backend fallback to legacy `options` field only works if it exists  
**Impact:** Frontend receives `{"options": {}}` leading to fallback placeholders  
**Severity:** CRITICAL

### Issue #3: API Response Format Mismatch in `diagnostic-images-test`
**Root Cause:** Different endpoint uses different response structure  
**Impact:** If frontend tries to use this endpoint, it will fail parsing  
**Severity:** HIGH

### Issue #4: Frontend Silently Fails with Placeholders
**Root Cause:** Fallback mechanism hides the real problem  
**Impact:** Users see generic "Opción A/B/C/D" without knowing data is missing  
**Severity:** MEDIUM (User Experience)

### Issue #5: Nullable Fields with No Validation
**Root Cause:** Model allows NULL but has no enforcement that either `opcion_x_texto` OR `options` JSON must have data  
**Impact:** Allows invalid questions to be created  
**Severity:** MEDIUM

### Issue #6: Multiple Diagnostic Endpoints with Different Formats
**Root Cause:** Multiple code iterations created incompatible endpoints  
**Impact:** Confusion about which endpoint to use; format inconsistency  
**Severity:** MEDIUM

---

## 6. DETAILED FILE CROSS-REFERENCE

| Component | File Path | Key Lines | Purpose |
|-----------|-----------|-----------|---------|
| Frontend Test UI | apps/frontend/app/diagnostic-test/test-interface.tsx | 21-44 | Question interface definition |
| Option Extraction | apps/frontend/app/diagnostic-test/test-interface.tsx | 458-472 | Extract options from API |
| Option Validation | apps/frontend/app/diagnostic-test/test-interface.tsx | 474-487 | Validate and fallback |
| Option Rendering | apps/frontend/app/diagnostic-test/test-interface.tsx | 728-782 | Display options to user |
| Backend Endpoint | apps/backend/app/routes/diagnostic_public.py | 903-981 | Format questions for API |
| Option Transformation | apps/backend/app/routes/diagnostic_public.py | 932-951 | Convert DB fields to response |
| Image Alternative | apps/backend/app/routes/diagnostic_images_test.py | 93-192 | Alternative endpoint (different format) |
| Database Model | apps/backend/app/models/question.py | 17-42 | Define question structure |
| Route Registration | apps/backend/app/main.py | 413-414, 423 | Register API endpoints |

---

## 7. CALL STACK & DATA TRANSFORMATION

### Request Path:
```
1. User selects subject in diagnostic-test/page.tsx
2. Selected subject passed to DiagnosticTestFlow
3. test-flow.tsx loads from /diagnostic-images-test/questions/{subject_id}
   OR
   test-interface.tsx loads from /diagnostic-public/diagnostic-questions/{subject_id}
4. Backend queries Question table
5. Backend transforms q.opcion_a_texto → options_data["A"]
6. Frontend receives options dict
7. Frontend maps options dict → options array
8. Frontend renders options or falls back to "Opción A/B/C/D"
```

### Data Transformation Points Where Data Can Be Lost:

```
Point 1: Database
  Question.opcion_a_texto = NULL ❌
  
Point 2: Backend Query
  Result: opcion_a_texto = None
  
Point 3: Backend Transformation (Line 937)
  option_text = getattr(q, 'opcion_a_texto')  # Returns None
  
Point 4: Backend Logic (Line 940)
  if option_text or option_image:  # Both None → Skip!
      options_data["A"] = ...  # NOT ADDED
  
Point 5: Backend Response (Line 959)
  "options": {}  # Empty dictionary!
  
Point 6: Frontend Receive (Line 459)
  optionsData = {} or {} # Still empty
  
Point 7: Frontend Mapping (Line 465)
  textField = optionsData[key] or ...  # Gets undefined
  options[i].text = ''  # Empty string
  
Point 8: Frontend Validation (Line 476)
  hasText = '' && ... # Evaluates to false
  option FILTERED OUT
  
Point 9: Frontend Fallback (Line 482)
  validOptions.length >= 2 ? validOptions : [PLACEHOLDERS]
  → Show "Opción A/B/C/D" 🚨
```

---

## 8. SUMMARY TABLE: ENDPOINTS & FORMATS

| Endpoint | Route File | Response Format | Frontend Handler | Status |
|----------|-----------|------------------|------------------|--------|
| `/api/v1/diagnostic-public/diagnostic-questions/{id}` | diagnostic_public.py | `{ "options": {...}, "option_images": {...} }` | test-interface.tsx lines 459-487 | ✓ Correct |
| `/diagnostic-public/diagnostic-questions/{id}` | diagnostic_public.py | Same as above | test-interface.tsx lines 459-487 | ✓ Correct (duplicate route) |
| `/diagnostic-images-test/questions/{id}` | diagnostic_images_test.py | `{ "questions": [...], "subject": {...} }` | test-flow.tsx lines 70-71 | ⚠ Wrapped format |
| `/api/v1/diagnostic-images-test/subjects-with-image-questions` | diagnostic_images_test.py | Subjects list | page.tsx | ✓ Correct |

---

## 9. KEY FINDINGS

✅ **Working Correctly:**
- Frontend properly implements options mapping with fallbacks
- Backend route registration covers multiple URL patterns
- Image URL transformation works as intended
- Difficulty and topic metadata properly passed

⚠️ **Partially Working:**
- Option text rendering relies on database population
- Legacy `options` field used as fallback
- Multiple endpoint format variations cause confusion

❌ **Not Working:**
- Option text display when `opcion_x_texto` fields are NULL
- Validation enforcement for required option text
- User visibility into when data is missing

---

## 10. RECOMMENDATIONS FOR INVESTIGATION CONTINUATION

1. **Verify Database Population:**
   - Check actual question records to see if `opcion_a_texto` etc. are populated
   - Run: `SELECT id, opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto FROM questions LIMIT 5;`

2. **Test Full Data Flow:**
   - Call `/api/v1/diagnostic-public/diagnostic-questions/{subject_id}` with valid ID
   - Check response JSON - are options dict empty?

3. **Check Legacy Field:**
   - If options_data is empty, check if `options` JSON field has data
   - May need to migrate from legacy format

4. **Add Data Validation:**
   - Implement database check ensuring questions have option text
   - Add API logging to track when empty options are returned

5. **Unify Endpoint Format:**
   - Consolidate diagnostic-images-test response format with main endpoint
   - Consider API versioning for breaking changes

---

## Conclusion

The data flow from database to frontend display has **multiple potential failure points**, primarily around **NULL option text fields** in the database. The frontend gracefully falls back to placeholder text, which masks the underlying data quality issue. The backend properly attempts to retrieve and format option text, but cannot create data from NULL values.

**Primary Issue:** Questions likely lack populated `opcion_x_texto` fields in the database.

**Secondary Issue:** No validation prevents questions with missing option text from being served to students.

