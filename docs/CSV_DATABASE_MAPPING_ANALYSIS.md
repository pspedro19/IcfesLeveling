# 🔍 CSV TO DATABASE MAPPING ANALYSIS

## 📋 **CSV FILES ANALYZED**

### 1. **questions.csv** (MAIN DATA SOURCE)
- **Records**: 4 sample questions shown
- **Fields**: 67 columns including rich ICFES metadata
- **Key Data**: Full question bank with IRT parameters, cognitive levels, etc.

### 2. **topics_catalog.csv** (TOPIC HIERARCHY)
- **Records**: Topic catalog with learning metadata  
- **Fields**: 21 columns including competencies, prerequisites, resources
- **Key Data**: Detailed topic structure with learning paths

### 3. **study_plan_templates.csv** (TEMPLATES)
- **Records**: Study plan templates by subject
- **Fields**: 13 columns including priorities and focus areas
- **Key Data**: Pre-defined study plans structure

### 4. **youtube_catalog_extendido_enriquecido.csv** (VIDEO RESOURCES)
- **Records**: YouTube video catalog with metadata
- **Fields**: 24 columns including effectiveness and pedagogical data
- **Key Data**: Validated video resources for topics

---

## ❌ **CRITICAL MAPPING GAPS IDENTIFIED**

### **🚨 PROBLEM 1: QUESTIONS TABLE FIELD MISMATCH**

**CSV Fields vs Database Fields:**

| CSV Field | Database Field | Status | Issue |
|-----------|----------------|--------|-------|
| `id_pregunta` | `id` | ❌ **MISMATCH** | CSV uses string, DB uses UUID |
| `pregunta` | `question_text` | ✅ **OK** | Matches |
| `respuesta_correcta` | `correct_answer` | ✅ **OK** | Matches |
| `opcion_a/b/c/d` | `options` (JSON) | ❌ **MISMATCH** | CSV has separate fields, DB uses JSON |
| `nivel_dificultad` | `difficulty` | ✅ **OK** | Matches |
| `area_evaluada` | No mapping | ❌ **MISSING** | Need subject_id resolution |
| `tema_especifico` | No mapping | ❌ **MISSING** | Need topic_id resolution |
| `parametro_irt_a/b/c` | `power_stats` (JSON) | ⚠️ **PARTIAL** | Need JSON structure mapping |

### **🚨 PROBLEM 2: MISSING INTERMEDIATE TABLES**

**Required for CSV → DB mapping:**

#### **A. `icfes_areas` Table - MISSING ❌**
```sql
-- NEEDED TO RESOLVE area_evaluada → subject_id
CREATE TABLE icfes_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    area_code VARCHAR(10) UNIQUE NOT NULL,
    area_name VARCHAR(100) NOT NULL,
    subject_id UUID REFERENCES subjects(id),
    icfes_official_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **B. `icfes_topics_extended` Table - MISSING ❌**
```sql
-- NEEDED TO RESOLVE tema_especifico + codigo_tema → topic_id
CREATE TABLE icfes_topics_extended (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_tema VARCHAR(20) UNIQUE NOT NULL,
    tema_principal VARCHAR(200) NOT NULL,
    subtema VARCHAR(200),
    tema_especifico VARCHAR(200),
    topic_id UUID REFERENCES topics(id),
    area_evaluada VARCHAR(50),
    competencia_icfes VARCHAR(200),
    componente VARCHAR(200),
    grado_introduccion INTEGER,
    prerequisitos JSONB DEFAULT '[]',
    orden_secuencial INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **C. `youtube_videos_enriched` Table - MISSING ❌**  
```sql
-- NEEDED FOR ENRICHED VIDEO DATA
CREATE TABLE youtube_videos_enriched (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_tema VARCHAR(20) REFERENCES icfes_topics_extended(codigo_tema),
    youtube_video_id VARCHAR(50) NOT NULL,
    youtube_url VARCHAR(500) NOT NULL,
    titulo_video VARCHAR(500),
    descripcion TEXT,
    duracion_segundos INTEGER,
    nivel_dificultad INTEGER,
    calidad_pedagogica DECIMAL(3,2),
    efectividad_historica DECIMAL(5,2),
    estado_disponibilidad VARCHAR(20) DEFAULT 'activo',
    fecha_verificacion DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **D. `study_plan_templates_icfes` Table - MISSING ❌**
```sql
-- NEEDED FOR TEMPLATE MANAGEMENT
CREATE TABLE study_plan_templates_icfes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID REFERENCES subjects(id),
    unit_number INTEGER NOT NULL,
    unit_name VARCHAR(200) NOT NULL,
    unit_description TEXT,
    topics_list TEXT[], -- Array of topic names
    recommendations_priority VARCHAR(20),
    weak_areas TEXT[],
    focus_topics TEXT[],
    study_time VARCHAR(20),
    difficulty_level INTEGER,
    icfes_weight DECIMAL(3,2),
    estimated_hours INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🛠️ **DETAILED MAPPING SOLUTIONS**

### **SOLUTION 1: Field Mapping for questions.csv**

```python
# CSV → Database Field Mapping
def map_question_csv_to_db(csv_row):
    return {
        # Basic fields
        'id': str(uuid.uuid4()),  # Generate new UUID
        'question_text': csv_row['pregunta'],
        'correct_answer': csv_row['respuesta_correcta'],
        'difficulty': int(csv_row['nivel_dificultad']),
        'explanation': csv_row['explicacion_respuesta'],
        'hint': csv_row['pista_1'],  # Use first hint
        
        # Options as JSON
        'options': {
            'A': csv_row['opcion_a'],
            'B': csv_row['opcion_b'], 
            'C': csv_row['opcion_c'],
            'D': csv_row['opcion_d']
        },
        
        # Power stats as JSON (IRT parameters)
        'power_stats': {
            'discrimination_index': float(csv_row['parametro_irt_a']),
            'difficulty_parameter': float(csv_row['parametro_irt_b']),
            'guessing_parameter': float(csv_row['parametro_irt_c']),
            'p_value': float(csv_row['p_value']),
            'point_biserial': float(csv_row['point_biserial']),
            'optimal_time_seconds': int(csv_row['optimal_time_seconds'])
        },
        
        # Tags array
        'tags': [
            csv_row['area_evaluada'],
            csv_row['competencia'],
            csv_row['tema_especifico'],
            csv_row['tipo_razonamiento']
        ],
        
        # Foreign keys (require resolution)
        'subject_id': resolve_subject_from_area(csv_row['area_evaluada']),
        'topic_id': resolve_topic_from_tema(csv_row['tema_especifico'])
    }
```

### **SOLUTION 2: Resolution Functions Needed**

```python
# Function to resolve area_evaluada → subject_id
def resolve_subject_from_area(area_evaluada):
    area_mapping = {
        'Matematicas': 'math_subject_uuid',
        'Lectura Crítica': 'reading_subject_uuid', 
        'Ciencias Naturales': 'science_subject_uuid',
        'Sociales y Ciudadanas': 'social_subject_uuid',
        'Inglés': 'english_subject_uuid'
    }
    return area_mapping.get(area_evaluada)

# Function to resolve tema_especifico → topic_id  
def resolve_topic_from_tema(tema_especifico):
    # This requires the icfes_topics_extended table
    # Query: SELECT topic_id FROM icfes_topics_extended 
    #        WHERE tema_especifico = tema_especifico
    pass
```

---

## 📊 **COMPLETE IMPLEMENTATION PLAN**

### **PHASE 1: CREATE MISSING TABLES (30 minutes)**

1. ✅ Create `icfes_areas` table
2. ✅ Create `icfes_topics_extended` table  
3. ✅ Create `youtube_videos_enriched` table
4. ✅ Create `study_plan_templates_icfes` table

### **PHASE 2: POPULATE REFERENCE DATA (45 minutes)**

1. ✅ Insert ICFES areas → subjects mapping
2. ✅ Process topics_catalog.csv → icfes_topics_extended
3. ✅ Create topics if they don't exist
4. ✅ Map tema_especifico → topic_id relationships

### **PHASE 3: DATA LOADING WITH MAPPING (60 minutes)**

1. ✅ Load questions.csv with field mapping
2. ✅ Load youtube_catalog with enriched data
3. ✅ Load study_plan_templates with proper structure
4. ✅ Validate all foreign key relationships

### **PHASE 4: VALIDATION AND TESTING (30 minutes)**

1. ✅ Verify all data loaded correctly
2. ✅ Test foreign key integrity
3. ✅ Validate question → topic → subject relationships
4. ✅ Test enhanced study plans with new data

---

## 🎯 **IMMEDIATE ACTION REQUIRED**

### **CRITICAL MISSING TABLES TO CREATE:**

1. **`icfes_areas`** - Maps CSV areas to database subjects
2. **`icfes_topics_extended`** - Extended topic metadata from CSV
3. **`youtube_videos_enriched`** - Rich video data with effectiveness metrics
4. **`study_plan_templates_icfes`** - Template management system

### **FIELD MAPPING ISSUES TO RESOLVE:**

1. **UUID Generation**: CSV uses string IDs, DB needs UUIDs
2. **JSON Structure**: Options and power_stats need JSON conversion
3. **Foreign Key Resolution**: area_evaluada → subject_id, tema_especifico → topic_id
4. **Array Fields**: Tags, prerequisites, topics_list need proper array handling

---

## ✅ **NEXT STEPS**

1. **Create the 4 missing tables** with proper structure
2. **Populate reference data** from topics_catalog.csv
3. **Create mapping functions** for field conversion
4. **Update load_all_data.py** with seamless mapping
5. **Test complete data loading** with validation

**ESTIMATED TIME**: 2.5 hours for complete seamless CSV → Database mapping

**PRIORITY**: 🚨 **CRITICAL** - Without these tables, CSV data cannot be properly loaded into the database structure.