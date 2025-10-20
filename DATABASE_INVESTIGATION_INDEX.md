# ICFES Database Structure Investigation - Complete Index

## Overview

This directory contains comprehensive documentation of the ICFES question database structure, backend API serialization, and frontend consumption patterns.

## Generated Documents

### 1. ICFES_DATABASE_STRUCTURE_INVESTIGATION.md (20KB, 556 lines)
**Comprehensive Technical Report**

The complete investigation with all technical details:
- Section 1: Question Model Attributes
- Section 2: Database Field Names (Field Mapping)
- Section 3: Backend Routes & Serialization
- Section 4: Question Schema Definitions
- Section 5: Frontend Question Interface
- Section 6: Critical Issues & Mismatches (6 identified)
- Section 7: Data Flow Diagram
- Section 8: Working Code Examples
- Section 9: Summary Field Name Mappings
- Section 10: Recommendations (Priority 1-3)
- Section 11: Conclusion

**Best for**: Understanding the complete system architecture, in-depth analysis

### 2. DATABASE_STRUCTURE_QUICK_REFERENCE.md (7.4KB, 238 lines)
**Quick Lookup Guide**

Quick reference for developers:
- TL;DR Field Names
- Critical Field Transformations
- Backend Serialization Process
- Frontend Processing Logic
- The 6 Critical Issues (summary)
- Most Important: The OPTIONS Dict
- Database Schema Locations
- Key Code Snippets
- Quick Debugging Checklist
- File Cross-Reference

**Best for**: Daily development, quick lookups, debugging

## Investigation Coverage

### Database Layer (checked)
- Question model in `/root/IcfesLeveling/apps/backend/app/models/question.py`
- Field definitions (lines 10-100)
- ICFES-specific fields
- IRT parameters
- Legacy compatibility fields

### Backend Layer (checked)
- Schema definitions in `/root/IcfesLeveling/apps/backend/app/schemas/question.py`
- Main endpoint: `/api/v1/diagnostic-public/diagnostic-questions/{subject_id}`
- Location: `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_public.py:903-981`
- Serialization logic (lines 922-972)
- Answer validation (line 961)
- Option extraction (lines 936-943)

### Frontend Layer (checked)
- Question interface in `/root/IcfesLeveling/apps/frontend/app/diagnostic-test/test-interface.tsx`
- API consumption (lines 89-126)
- Answer validation (line 323)
- Data display logic

## Key Findings Summary

### Question Field Names in Database
| Field | Type | Purpose |
|-------|------|---------|
| `opcion_a_texto` | Text | Option A text |
| `opcion_a_imagen` | String(500) | Option A image |
| `opcion_b_texto` | Text | Option B text |
| `opcion_b_imagen` | String(500) | Option B image |
| `opcion_c_texto` | Text | Option C text |
| `opcion_c_imagen` | String(500) | Option C image |
| `opcion_d_texto` | Text | Option D text |
| `opcion_d_imagen` | String(500) | Option D image |
| `pregunta_texto` | Text | Main question text |
| `pregunta_imagen` | String(500) | Main question image |
| `respuesta_correcta` | String(1) | Correct answer (a/b/c/d) |

### Critical Issues Identified

1. **HIGH**: Answer Validation Case Sensitivity
   - Database: lowercase (a, b, c, d)
   - Frontend: uppercase (A, B, C, D)
   - Risk: Broken scoring if .toUpperCase() fails

2. **MEDIUM**: Dual Field System
   - Primary: opcion_[a-d]_texto
   - Legacy: options JSON field
   - Risk: Unpredictable behavior with mixed data

3. **MEDIUM**: Missing Response Validation
   - No Pydantic response_model on endpoint
   - Risk: Invalid data sent to frontend

4. **MEDIUM**: Image Path Validation
   - No validation that images exist
   - Risk: 404 errors in frontend

5. **MEDIUM**: Topic Structure Inconsistency
   - Sometimes string, sometimes object
   - Risk: Frontend type errors

6. **LOW**: Field Name Inconsistency
   - Different names at each layer
   - Risk: Developer confusion

## Quick Reference

### The Main Data Transform

```
Database:    opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto
             respuesta_correcta = "a" (lowercase)
                          ↓
Backend:     Extract fields (lines 936-943)
             Uppercase answer (line 961)
                          ↓
Frontend:    options = {A: "text", B: "text", C: "text", D: "text"}
             correct_answer = "A" (uppercase)
                          ↓
Validation:  answers[q.id] === correct_answer (both uppercase)
```

### Most Critical Code Path

**Location**: `diagnostic_public.py` lines 936-943 and 961

```python
# Extract options
for letter in ['a', 'b', 'c', 'd']:
    option_text = getattr(q, f'opcion_{letter}_texto')
    if option_text:
        options_data[letter.upper()] = option_text  # A, B, C, D

# Ensure answer is uppercase
"correct_answer": (q.respuesta_correcta or q.correct_answer or "A").upper()
```

## Debugging Steps

1. Check if `respuesta_correcta` is lowercase in database
2. Verify `opcion_[a-d]_texto` fields are NOT NULL
3. Ensure backend uppercases answer before sending
4. Verify frontend uppercases user input for comparison
5. Check image paths are valid on server
6. Test with known correct answer

## Files Referenced

### Backend
- `/root/IcfesLeveling/apps/backend/app/models/question.py` - Model definition
- `/root/IcfesLeveling/apps/backend/app/schemas/question.py` - Schema definition
- `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_public.py` - Main endpoint
- `/root/IcfesLeveling/apps/backend/app/routes/diagnostic.py` - Legacy endpoint

### Frontend
- `/root/IcfesLeveling/apps/frontend/app/diagnostic-test/test-interface.tsx` - Question component

## Recommendations

### Priority 1 (Critical)
1. Add Pydantic response_model to /diagnostic-questions endpoint
2. Normalize answer field handling consistently
3. Add image validation before returning to frontend

### Priority 2 (Important)
1. Create migration to consolidate legacy fields
2. Add fallback handling documentation
3. Add comprehensive logging

### Priority 3 (Nice to Have)
1. Create separate serialization schema
2. Add caching for questions
3. Add data quality metrics

## How to Use This Documentation

### For Development
- Use **DATABASE_STRUCTURE_QUICK_REFERENCE.md** for daily work
- Refer to line numbers for exact code locations
- Check "Quick Debugging Checklist" when issues arise

### For Code Review
- Use **ICFES_DATABASE_STRUCTURE_INVESTIGATION.md** for detailed review
- Reference "Critical Issues" section (Section 6)
- Check recommended fixes in Section 10

### For Onboarding
- Read **DATABASE_STRUCTURE_QUICK_REFERENCE.md** first (overview)
- Then read **ICFES_DATABASE_STRUCTURE_INVESTIGATION.md** (deep dive)
- Study the "Working Code Examples" section

### For Debugging
1. Go to **DATABASE_STRUCTURE_QUICK_REFERENCE.md**
2. Find relevant section (Options Dict, Field Transformations, etc.)
3. Check line numbers
4. Use "Quick Debugging Checklist"

## Document Versions

- Created: 2025-10-20
- Investigation Thoroughness: Very Thorough
- Coverage: Database → Backend → Frontend
- Issues Identified: 6 (1 HIGH, 4 MEDIUM, 1 LOW)

## Next Steps

1. Read the appropriate document based on your needs
2. Review the Critical Issues section
3. Check File Locations Reference for exact code
4. Use Code Snippets for implementation reference
5. Follow Debugging Checklist if issues arise

---

**Status**: Complete investigation with comprehensive documentation
**Last Updated**: 2025-10-20
**Prepared by**: Claude Code Investigation System
