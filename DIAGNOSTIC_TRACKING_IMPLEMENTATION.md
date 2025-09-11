# Diagnostic Tracking Implementation

## Overview
This implementation adds comprehensive tracking metrics to the diagnostic test system as requested. The system now tracks and stores the following metrics for each question response:

1. **Response Time per Question** (Tiempo_Estimado as baseline)
2. **Difficulty Level Attempted** (Nivel_Dificultad) 
3. **Performance Level Achieved** (Nivel_Desempeño_Esperado)
4. **XP Earned** (Puntos_XP)

All metrics are stored in the `diagnostic_test_results` table for detailed analytics and reporting.

## Implementation Details

### Database Changes

#### 1. Enhanced DiagnosticTestResult Model
**File**: `apps/backend/app/models/diagnostic_test.py`

Added new tracking columns:
```python
# Tracking metrics as requested
tiempo_estimado_baseline = Column(Integer, nullable=True)  # Baseline response time from question data (seconds)
nivel_dificultad = Column(Integer, nullable=True)  # Difficulty level attempted (1-10 scale)
nivel_desempeno_esperado = Column(String(20), nullable=True)  # Performance level achieved
puntos_xp_earned = Column(Integer, default=0)  # XP points earned for this question
```

#### 2. Enhanced Question Model
**File**: `apps/backend/app/models/question.py`

Added XP points field:
```python
puntos_xp = Column(Integer, default=10, nullable=True)  # XP points for this question
```

#### 3. Database Migrations
**Files**: 
- `database/migrations/033-add-diagnostic-tracking-metrics.sql`
- `database/migrations/034-add-puntos-xp-to-questions.sql`

### Service Layer Updates

#### 1. Adaptive Diagnostic Service
**File**: `apps/backend/app/services/adaptive_diagnostic_service.py`

Enhanced `process_adaptive_answer()` method to:
- Create `DiagnosticTestResult` entries with tracking metrics
- Extract baseline data from question metadata (Tiempo_Estimado, Nivel_Desempeño_Esperado, Puntos_XP)
- Calculate XP earned based on correctness and difficulty
- Track IRT theta progression (theta_before and theta_after)

#### 2. Regular Diagnostic Service  
**File**: `apps/backend/app/services/diagnostic_service.py`

Enhanced `submit_diagnostic_test()` method to:
- Create `DiagnosticTestResult` entries for non-adaptive tests
- Extract and store the same tracking metrics
- Ensure consistency across different test types

### Data Mapping

The implementation maps CSV data fields to tracking metrics:

| CSV Field | Database Field | Description |
|-----------|----------------|-------------|
| `Tiempo_Estimado` (col 13) | `tiempo_estimado_baseline` | Baseline response time in seconds |
| `Nivel_Dificultad` (col 7) | `nivel_dificultad` | Question difficulty (1-10 scale) |
| `Nivel_Desempeño_Esperado` (col 12) | `nivel_desempeno_esperado` | Expected performance level |
| `Puntos_XP` (col 27) | `puntos_xp_earned` | XP points earned |

### Key Features

#### 1. Response Time Tracking
- **Baseline**: Stores the estimated time from question metadata (`Tiempo_Estimado`)
- **Actual**: Records actual response time in milliseconds
- **Analysis**: Enables comparison between expected vs actual response times

#### 2. Difficulty Level Tracking
- **Source**: Maps from question's `difficulty` field (1-10 scale)
- **Usage**: Tracks what difficulty level each student attempted
- **Analytics**: Enables difficulty progression analysis

#### 3. Performance Level Tracking
- **Source**: Maps from question's `nivel_desempeno_esperado` field
- **Values**: "Mínimo", "Satisfactorio", "Avanzado", etc.
- **Usage**: Tracks expected vs achieved performance levels

#### 4. XP Earned Tracking
- **Source**: Maps from question's `puntos_xp` field (default 10 XP)
- **Logic**: 
  - Correct answer: Full XP points
  - Incorrect answer: 1/4 XP points (minimum 1 XP)
- **Usage**: Enables gamification and progress tracking

#### 5. IRT Theta Tracking (Adaptive Only)
- **theta_before**: Student's ability estimate before answering
- **theta_after**: Updated ability estimate after answering
- **Usage**: Enables advanced adaptive testing analytics

## Installation Instructions

### 1. Apply Database Migrations
```bash
python apply_tracking_migrations.py
```

This will:
- Add tracking columns to `diagnostic_test_results` table
- Add `puntos_xp` column to `questions` table
- Create performance indexes

### 2. Verify Implementation
The tracking will automatically work for:
- ✅ New adaptive diagnostic tests
- ✅ New regular diagnostic tests
- ✅ All question types with available metadata

## Analytics Capabilities

With this implementation, you can now analyze:

1. **Response Time Analysis**
   - Compare actual vs baseline response times
   - Identify questions that take longer/shorter than expected
   - Track response time improvement over time

2. **Difficulty Progression** 
   - Track what difficulty levels students attempt
   - Analyze success rates by difficulty level
   - Identify optimal difficulty progression paths

3. **Performance Level Achievement**
   - Compare expected vs achieved performance levels
   - Track performance level distribution
   - Identify areas needing reinforcement

4. **Gamification Analytics**
   - Track XP earned per question/test/student
   - Analyze XP earning patterns
   - Optimize XP rewards based on engagement

5. **Comprehensive Student Profiles**
   - Individual student performance tracking
   - Learning progression analytics
   - Adaptive testing effectiveness

## Example Queries

### Query Response Time Performance
```sql
SELECT 
    q.pregunta_texto,
    dtr.tiempo_estimado_baseline,
    AVG(dtr.response_time) as avg_actual_time,
    dtr.tiempo_estimado_baseline - AVG(dtr.response_time/1000) as time_difference
FROM diagnostic_test_results dtr
JOIN questions q ON dtr.question_id = q.id
WHERE dtr.tiempo_estimado_baseline IS NOT NULL
GROUP BY q.id, q.pregunta_texto, dtr.tiempo_estimado_baseline;
```

### Query Difficulty Success Rates
```sql
SELECT 
    nivel_dificultad,
    COUNT(*) as total_attempts,
    COUNT(*) FILTER (WHERE is_correct = true) as correct_answers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_correct = true) / COUNT(*), 2) as success_rate
FROM diagnostic_test_results
WHERE nivel_dificultad IS NOT NULL
GROUP BY nivel_dificultad
ORDER BY nivel_dificultad;
```

### Query XP Earnings
```sql
SELECT 
    u.email,
    SUM(dtr.puntos_xp_earned) as total_xp_earned,
    COUNT(*) as questions_attempted,
    AVG(dtr.puntos_xp_earned) as avg_xp_per_question
FROM diagnostic_test_results dtr
JOIN users u ON dtr.user_id = u.id
GROUP BY u.id, u.email
ORDER BY total_xp_earned DESC;
```

## Files Modified

### Models
- `apps/backend/app/models/diagnostic_test.py` - Enhanced DiagnosticTestResult model
- `apps/backend/app/models/question.py` - Added puntos_xp field

### Services  
- `apps/backend/app/services/adaptive_diagnostic_service.py` - Added tracking logic
- `apps/backend/app/services/diagnostic_service.py` - Added tracking logic

### Database
- `database/migrations/033-add-diagnostic-tracking-metrics.sql` - DiagnosticTestResult columns
- `database/migrations/034-add-puntos-xp-to-questions.sql` - Questions puntos_xp column

### Scripts
- `apply_tracking_migrations.py` - Migration application script
- `DIAGNOSTIC_TRACKING_IMPLEMENTATION.md` - This documentation

## Future Enhancements

The tracking system is designed to be extensible. Future enhancements could include:

1. **Real-time Analytics Dashboard** - Live tracking of performance metrics
2. **Advanced IRT Analytics** - Deep statistical analysis of student abilities  
3. **Predictive Modeling** - ML models to predict student performance
4. **Adaptive XP System** - Dynamic XP calculation based on performance patterns
5. **Comparative Analytics** - Cohort and demographic performance comparisons

## Support

For questions or issues with this implementation, refer to:
- Model definitions in the respective model files
- Service logic in the diagnostic service files  
- Database schema in the migration files
- This documentation for usage examples