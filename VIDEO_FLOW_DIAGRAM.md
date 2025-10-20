# VIDEO FLOW DIAGRAM - Visual Trace

## 🎯 High-Level Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│   POSTGRESQL    │◄────────│  FASTAPI        │◄────────│   NEXT.JS       │
│   DATABASE      │         │  BACKEND        │         │   FRONTEND      │
│                 │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
      │                            │                            │
      │ youtube_catalog            │ diagnostic_public.py       │ claude-study-plan/
      │ diagnostic_tests           │ claude_study_plan.py       │ page.tsx
      │ questions                  │                            │
      │ diagnostic_test_answers    │                            │
      │                            │                            │
      └────────────────────────────┴────────────────────────────┘
               YouTube IDs flow through entire stack
```

---

## 📱 DETAILED USER JOURNEY

```
╔════════════════════════════════════════════════════════════════════════╗
║                          START: USER ARRIVES                            ║
╚════════════════════════════════════════════════════════════════════════╝
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  /diagnostic-test       │
                    │  Select Subject:        │
                    │  • Matemáticas          │
                    │  • Ciencias Naturales ✓ │
                    │  • Lectura Crítica      │
                    └─────────────────────────┘
                                  │
                                  ▼
╔════════════════════════════════════════════════════════════════════════╗
║                    PHASE 1: DIAGNOSTIC TEST                             ║
╚════════════════════════════════════════════════════════════════════════╝
                                  │
            ┌─────────────────────┴─────────────────────┐
            │  GET /api/v1/diagnostic-public/           │
            │      subjects/{subject_id}/questions      │
            │                                            │
            │  Returns: 25 random questions             │
            └─────────────────────┬─────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  User answers Q1-Q25    │
                    │  Each answer triggers:  │
                    │                         │
                    │  POST submit-answer     │
                    │  {                      │
                    │    question_id: uuid    │
                    │    user_answer: "B"     │
                    │    is_correct: true     │
                    │  }                      │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  DATABASE WRITES:       │
                    │                         │
                    │  diagnostic_tests       │
                    │    ├─ id: test_uuid     │
                    │    ├─ subject_id        │
                    │    └─ status: progress  │
                    │                         │
                    │  diagnostic_test_answers│
                    │    ├─ question_id       │
                    │    ├─ user_answer       │
                    │    └─ is_correct ✓/✗    │
                    └─────────────────────────┘
                                  │
                                  ▼
╔════════════════════════════════════════════════════════════════════════╗
║                    PHASE 2: RESULTS DISPLAY                             ║
╚════════════════════════════════════════════════════════════════════════╝
                                  │
                    ┌─────────────────────────┐
                    │ /diagnostic-test/results│
                    │                         │
                    │ ┌─────────────────────┐ │
                    │ │   Score: 16/25      │ │
                    │ │   Percentage: 65%   │ │
                    │ │   Rank: C           │ │
                    │ └─────────────────────┘ │
                    │                         │
                    │ Strengths:              │
                    │ ✓ Respiración celular   │
                    │ ✓ Fotosíntesis         │
                    │                         │
                    │ Weaknesses:             │
                    │ ✗ Genética             │
                    │ ✗ Transporte celular   │
                    └─────────────────────────┘
                                  │
                                  │
                         [User Clicks Button]
                                  │
                    ┌─────────────────────────┐
                    │ 📚 Crear Plan de       │
                    │    Estudio             │
                    │    Personalizado       │
                    └─────────────────────────┘
                                  │
                                  ▼
╔════════════════════════════════════════════════════════════════════════╗
║            PHASE 3: STUDY PLAN GENERATION (BACKEND)                     ║
╚════════════════════════════════════════════════════════════════════════╝
                                  │
            ┌─────────────────────┴─────────────────────┐
            │  POST /api/v1/claude-study-plan/generate  │
            │  {                                         │
            │    test_id: "diagnostic-test-...",        │
            │    subject_id: "550e8400-..."             │
            │  }                                         │
            └─────────────────────┬─────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  STEP 1: GET TEST DATA  │
                    │                         │
                    │  SELECT score_percentage│
                    │         weaknesses      │
                    │  FROM diagnostic_tests  │
                    │  WHERE id = test_id     │
                    │                         │
                    │  Result: 65% score      │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ STEP 2: GET INCORRECT   │
                    │         QUESTIONS       │
                    │                         │
                    │ SELECT q.id,            │
                    │        q.pregunta_texto,│
                    │        q.competencia,   │
                    │        q.componente     │
                    │ FROM diagnostic_test_   │
                    │      answers dta        │
                    │ JOIN questions q        │
                    │ WHERE is_correct = false│
                    │                         │
                    │ Found: 9 incorrect      │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ STEP 3: AGGREGATE       │
                    │         WEAK TOPICS     │
                    │                         │
                    │ Topics with errors:     │
                    │ • Genética (3 errors)   │
                    │ • Transporte (2 errors) │
                    │ • Ecología (2 errors)   │
                    │ • Evolución (2 errors)  │
                    └─────────────────────────┘
                                  │
                                  ▼
╔════════════════════════════════════════════════════════════════════════╗
║        ⭐ CRITICAL: VIDEO RETRIEVAL FROM DATABASE ⭐                   ║
╚════════════════════════════════════════════════════════════════════════╝
                                  │
            ┌─────────────────────┴─────────────────────┐
            │ STEP 4: GET AVAILABLE VIDEOS              │
            │                                            │
            │ SELECT                                     │
            │   id,              ← UUID                  │
            │   youtube_id,      ← 🎬 CRITICAL FIELD    │
            │   title,           ← Video title           │
            │   youtube_url,     ← Full URL              │
            │   channel_name,    ← Channel               │
            │   duration_minutes,← Length                │
            │   quality_score,   ← Rating                │
            │   icfes_competence,← ICFES metadata        │
            │   icfes_component  ← ICFES metadata        │
            │ FROM youtube_catalog                       │
            │ WHERE subject_id = :subject_id             │
            │   AND is_active = true                     │
            │   AND quality_score >= 0.8                 │
            │ ORDER BY quality_score DESC                │
            │ LIMIT 30                                   │
            └─────────────────────┬─────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ QUERY RESULT:           │
                    │                         │
                    │ Row 1:                  │
                    │  [0] = "0b442cd2-..."   │
                    │  [1] = "PTrOSGYC6BU" ⭐ │
                    │  [2] = "Estructura..."  │
                    │  [3] = "https://you..." │
                    │  [4] = "unProfesor"     │
                    │  [5] = 12               │
                    │  [6] = 0.95             │
                    │  ...                    │
                    │                         │
                    │ Found: 30 videos        │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ STEP 5: BUILD DICT      │
                    │                         │
                    │ available_videos = [    │
                    │   {                     │
                    │     "id": row[0],       │
                    │     "youtube_id": row[1]│← EXTRACTED │
                    │     "title": row[2],    │
                    │     "url": row[3],      │
                    │     "channel": row[4],  │
                    │     "duration": row[5]  │
                    │   },                    │
                    │   ...                   │
                    │ ]                       │
                    └─────────────────────────┘
                                  │
                                  ▼
╔════════════════════════════════════════════════════════════════════════╗
║               STEP 6: CLAUDE AI INTELLIGENT MATCHING                    ║
╚════════════════════════════════════════════════════════════════════════╝
                                  │
            ┌─────────────────────┴─────────────────────┐
            │  Call Anthropic Claude API                 │
            │                                            │
            │  INPUT:                                    │
            │  • Failed topics: [Genética, Transporte]  │
            │  • Available videos: 30 videos             │
            │  • Subject: Ciencias Naturales             │
            │  • Score: 65%                              │
            │                                            │
            │  CLAUDE ANALYZES:                          │
            │  • Matches video competencias to errors   │
            │  • Matches video componentes to weakness  │
            │  • Creates learning path                   │
            │  • Prioritizes critical topics             │
            └─────────────────────┬─────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ CLAUDE RETURNS:         │
                    │                         │
                    │ {                       │
                    │   "units": [            │
                    │     {                   │
                    │       "unit_number": 1, │
                    │       "title": "Gen...",│
                    │       "priority": "alta"│
                    │       "videos": [       │
                    │         {               │
                    │           "video_id":   │
                    │             "776aeb5c"  │
                    │           "covers":     │
                    │             "Genética"  │
                    │           "justif...":  │
                    │             "Cubre..." │
                    │         }               │
                    │       ]                 │
                    │     }                   │
                    │   ]                     │
                    │ }                       │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ STEP 7: BUILD UNITS     │
                    │                         │
                    │ For each Claude video:  │
                    │   vid_id = "776aeb5c"   │
                    │   video = video_map[id] │
                    │                         │
                    │   unit_videos.append({  │
                    │     "id": video['id'],  │
                    │     "youtube_id":       │← CRITICAL │
                    │       video['youtube_id']│
                    │     "title": video[...],│
                    │     "url": video['url'],│
                    │     "channel": ...,     │
                    │     "xp": 100 + dur*2,  │
                    │     "recommendation_...:│
                    │       "Covers Genética" │
                    │   })                    │
                    └─────────────────────────┘
                                  │
                                  ▼
╔════════════════════════════════════════════════════════════════════════╗
║                 PHASE 4: JSON RESPONSE TO FRONTEND                      ║
╚════════════════════════════════════════════════════════════════════════╝
                                  │
            ┌─────────────────────┴─────────────────────┐
            │  FastAPI Serializes to JSON               │
            │                                            │
            │  {                                         │
            │    "success": true,                        │
            │    "plan_id": "abc-123",                   │
            │    "plan_data": {                          │
            │      "metadata": {                         │
            │        "ai_generated": true,               │
            │        "total_videos": 12                  │
            │      },                                    │
            │      "units": [                            │
            │        {                                   │
            │          "unit_number": 1,                 │
            │          "title": "Genética Básica",       │
            │          "videos": [                       │
            │            {                               │
            │              "id": "776aeb5c-...",         │
            │              "youtube_id": "mYcznTcpKdU", ⭐│
            │              "title": "Leyes de Mendel",   │
            │              "url": "https://...",         │
            │              "channel": "Es Ciencia",      │
            │              "duration_minutes": 15,       │
            │              "xp": 130                     │
            │            }                               │
            │          ]                                 │
            │        }                                   │
            │      ]                                     │
            │    }                                       │
            │  }                                         │
            └─────────────────────┬─────────────────────┘
                                  │
                                  ▼
╔════════════════════════════════════════════════════════════════════════╗
║                   PHASE 5: FRONTEND RENDERS PLAN                        ║
╚════════════════════════════════════════════════════════════════════════╝
                                  │
            ┌─────────────────────┴─────────────────────┐
            │  /claude-study-plan receives response     │
            │  setStudyPlan(data)                       │
            └─────────────────────┬─────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ RENDERS UI:             │
                    │                         │
                    │ ╔═══════════════════╗   │
                    │ ║ Unidad 1          ║   │
                    │ ║ Genética Básica   ║   │
                    │ ║ Prioridad: 🔥 Alta║   │
                    │ ╠═══════════════════╣   │
                    │ ║                   ║   │
                    │ ║ 📹 Leyes de Mendel║   │
                    │ ║ Es Ciencia        ║   │
                    │ ║ 15 min | 130 XP   ║   │
                    │ ║ [▶️ Ver Video]    ║   │
                    │ ║                   ║   │
                    │ ║ 💡 Covers Genética║   │
                    │ ║    errors         ║   │
                    │ ╚═══════════════════╝   │
                    └─────────────────────────┘
                                  │
                         [User Clicks ▶️]
                                  │
                                  ▼
╔════════════════════════════════════════════════════════════════════════╗
║              PHASE 6: VIDEO MODAL & YOUTUBE PLAYER                      ║
╚════════════════════════════════════════════════════════════════════════╝
                                  │
            ┌─────────────────────┴─────────────────────┐
            │  openVideoModal(video)                    │
            │  setSelectedVideo(video)                  │
            └─────────────────────┬─────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ SafeYouTubePlayer       │
                    │ receives video object:  │
                    │                         │
                    │ {                       │
                    │   id: "776aeb5c...",    │
                    │   youtube_id:           │← CRITICAL │
                    │     "mYcznTcpKdU",      │
                    │   title: "Leyes...",    │
                    │   url: "https://..."    │
                    │ }                       │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ EXTRACT YOUTUBE ID:     │
                    │                         │
                    │ const getYouTubeId = () │
                    │   if (video.youtube_id) │← PRIORITY 1│
                    │     return video.       │
                    │            youtube_id;  │
                    │   else                  │
                    │     return extractFrom  │← FALLBACK │
                    │            Url(...);    │
                    │                         │
                    │ Result: "mYcznTcpKdU"   │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ BUILD EMBED URL:        │
                    │                         │
                    │ const embedUrl =        │
                    │   `https://youtube.com/ │
                    │    embed/mYcznTcpKdU    │
                    │    ?rel=0               │
                    │    &modestbranding=1    │
                    │    &fs=1                │
                    │    &cc_load_policy=1`   │
                    └─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ RENDER IFRAME:          │
                    │                         │
                    │ <iframe                 │
                    │   src={embedUrl}        │
                    │   title="Leyes Mendel"  │
                    │   allowFullScreen       │
                    │ />                      │
                    └─────────────────────────┘
                                  │
                                  ▼
╔════════════════════════════════════════════════════════════════════════╗
║                     ✅ SUCCESS: VIDEO PLAYS                            ║
╚════════════════════════════════════════════════════════════════════════╝
                                  │
                    ┌─────────────────────────┐
                    │ YouTube iframe loads    │
                    │ and plays video:        │
                    │                         │
                    │ ┌─────────────────────┐ │
                    │ │ ▶️ Leyes de Mendel │ │
                    │ │                     │ │
                    │ │  [Video playing]    │ │
                    │ │                     │ │
                    │ │  Es Ciencia         │ │
                    │ │  15:23              │ │
                    │ └─────────────────────┘ │
                    │                         │
                    │ [✓ Mark Completed]      │
                    │ +130 XP                 │
                    └─────────────────────────┘
```

---

## 🔴 BREAK POINTS - Where Issues Could Occur

```
❌ BREAK POINT #1: SQL Query Missing Field
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Location: apps/backend/app/routes/diagnostic_public.py:813-820

SELECT id, title, url          ← Missing youtube_id!
FROM youtube_catalog

Result: youtube_id never reaches frontend → iframe fails


✅ FIXED VERSION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SELECT id, youtube_id, title, youtube_url
FROM youtube_catalog
```

```
❌ BREAK POINT #2: Fake Video in Database
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Database contains:
  youtube_id: "dQw4w9WgXcQ"
  title: "Estadística"
  is_active: TRUE

But this is actually Rick Astley's "Never Gonna Give You Up"
Not an educational statistics video!

Result: Wrong video plays or "Video unavailable"


✅ FIXED VERSION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

UPDATE youtube_catalog
SET is_active = FALSE
WHERE youtube_id = 'dQw4w9WgXcQ';

Only 193 verified educational videos remain active
```

```
❌ BREAK POINT #3: Frontend URL Parsing Failure
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

video = {
  title: "Leyes de Mendel",
  url: "https://youtube.com/watch?v=mYcznTcpKdU"
  // NO youtube_id field
}

const videoId = url.split('v=')[1]?.split('&')[0]
// If URL format changes, this breaks!

Result: iframe src becomes invalid → "Video unavailable"


✅ FIXED VERSION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

video = {
  title: "Leyes de Mendel",
  youtube_id: "mYcznTcpKdU",  ← Direct field
  url: "https://youtube.com/watch?v=mYcznTcpKdU"
}

const getYouTubeId = (video) => {
  if (video.youtube_id) return video.youtube_id;  // Reliable
  return extractFromUrl(video.url);  // Fallback
}
```

```
❌ BREAK POINT #4: Response Data Mapping Missing Field
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Backend Python code
video_data = {
    "id": str(row[0]),
    "title": row[2],
    "url": row[3],
    # youtube_id NOT INCLUDED ❌
}

Result: Frontend receives no youtube_id → has to parse URL


✅ FIXED VERSION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

video_data = {
    "id": str(row[0]),
    "youtube_id": row[1] or "",  ✅
    "title": row[2],
    "url": row[3],
}
```

---

## 📊 DATA VALIDATION FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER                                 │
│                                                                  │
│  youtube_catalog table:                                          │
│  • youtube_id VARCHAR(11) NOT NULL                               │
│  • CHECK (LENGTH(youtube_id) = 11)                               │
│  • is_active BOOLEAN DEFAULT TRUE                                │
│                                                                  │
│  Ensures:                                                        │
│  ✓ All YouTube IDs are exactly 11 characters                    │
│  ✓ Inactive videos are excluded from queries                    │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND LAYER                                  │
│                                                                  │
│  SQL Query validation:                                           │
│  • Always SELECT youtube_id                                      │
│  • WHERE is_active = TRUE                                        │
│  • WHERE quality_score >= 0.8                                    │
│                                                                  │
│  Ensures:                                                        │
│  ✓ Only high-quality videos are retrieved                       │
│  ✓ youtube_id is always in response                             │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   API RESPONSE                                   │
│                                                                  │
│  JSON structure:                                                 │
│  {                                                               │
│    "id": "uuid",                                                 │
│    "youtube_id": "PTrOSGYC6BU",  ← MANDATORY                    │
│    "title": "...",                                               │
│    "url": "..."                                                  │
│  }                                                               │
│                                                                  │
│  Ensures:                                                        │
│  ✓ youtube_id is present in every video object                  │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   FRONTEND LAYER                                 │
│                                                                  │
│  SafeYouTubePlayer component:                                    │
│  • Prioritizes video.youtube_id                                  │
│  • Falls back to URL parsing                                     │
│  • Error handling for unavailable videos                         │
│  • Auto-reports broken videos                                    │
│                                                                  │
│  Ensures:                                                        │
│  ✓ Reliable video ID extraction                                 │
│  ✓ Graceful error handling                                      │
│  ✓ User feedback on failures                                    │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   YOUTUBE IFRAME                                 │
│                                                                  │
│  src="https://www.youtube.com/embed/PTrOSGYC6BU"                │
│                                                                  │
│  ✅ Video plays successfully                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 SUMMARY: Where YouTube IDs Live

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                      YOUTUBE ID JOURNEY                         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

1. DATABASE (Source of Truth)
   └─ youtube_catalog.youtube_id: "PTrOSGYC6BU"

2. SQL QUERY (Retrieval)
   └─ SELECT youtube_id FROM youtube_catalog

3. PYTHON DICT (Backend Processing)
   └─ video = {"youtube_id": "PTrOSGYC6BU"}

4. JSON RESPONSE (API)
   └─ {"youtube_id": "PTrOSGYC6BU"}

5. TYPESCRIPT STATE (Frontend)
   └─ video.youtube_id = "PTrOSGYC6BU"

6. REACT COMPONENT (SafeYouTubePlayer)
   └─ const youtubeId = video.youtube_id

7. IFRAME SRC (Rendering)
   └─ src="https://youtube.com/embed/PTrOSGYC6BU"

8. YOUTUBE PLAYER (Display)
   └─ 🎬 Video plays successfully!
```

---

**Document Created**: October 20, 2025
**Purpose**: Visual trace of complete video flow
**Status**: All break points identified and fixed
**Current State**: Production-ready with 193 verified videos
