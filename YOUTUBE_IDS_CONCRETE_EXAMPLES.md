# YouTube Video IDs - Concrete Examples

## Quick Reference Guide

This document provides concrete examples of actual YouTube video IDs found in the IcfesLeveling system.

---

## 1. CATALOG VIDEO IDs (Database Files)

### From: `/root/IcfesLeveling/database/init/youtube_catalog_extendido_enriquecido.csv`

#### Ciencias Naturales (Natural Sciences)

| Code | Topic | Video ID | Full URL |
|------|-------|----------|----------|
| CN001 | Estructura celular | **PTrOSGYC6BU** | https://www.youtube.com/watch?v=PTrOSGYC6BU |
| CN002 | Respiración celular | **YefwfJ8IpEI** | https://www.youtube.com/watch?v=YefwfJ8IpEI |
| CN003 | Leyes de Mendel | **mYcznTcpKdU** | https://www.youtube.com/watch?v=mYcznTcpKdU |
| CN004 | Fotosíntesis | **X2Z-0e5maKw** | https://www.youtube.com/watch?v=X2Z-0e5maKw |
| CN005 | Transporte celular | **yzkohlVwaB8** | https://www.youtube.com/watch?v=yzkohlVwaB8 |
| CN006 | Mitosis | **NVvc7cp7pAg** | https://www.youtube.com/watch?v=NVvc7cp7pAg |
| CN007 | Meiosis | **awXSXrnK04s** | https://www.youtube.com/watch?v=awXSXrnK04s |
| CN008 | ADN y proteínas | **uiCrjZ-0eQk** | https://www.youtube.com/watch?v=uiCrjZ-0eQk |
| CN009 | Evolución | **CBAwcRaVzA4** | https://www.youtube.com/watch?v=CBAwcRaVzA4 |
| CN010 | Ecosistemas | **YsfZ8ut9-Eo** | https://www.youtube.com/watch?v=YsfZ8ut9-Eo |

#### Matemáticas (Mathematics)

| Code | Topic | Video ID | Full URL |
|------|-------|----------|----------|
| M001 | Álgebra lineal | (from catalog) | Various |
| - | Ecuaciones | **TeqRLdEnkxQ** | https://www.youtube.com/watch?v=TeqRLdEnkxQ |
| - | Geometría | **2Vv-BfVoq4g** | https://www.youtube.com/watch?v=2Vv-BfVoq4g |
| - | Estadística | **wKJ9KzGQq0w** | https://www.youtube.com/watch?v=wKJ9KzGQq0w |
| - | Cálculo | **WUvTyaaNkzM** | https://www.youtube.com/watch?v=WUvTyaaNkzM |
| - | Trigonometría | **iDulhoQ2pro** | https://www.youtube.com/watch?v=iDulhoQ2pro |

---

## 2. HARDCODED VIDEO IDs (Source Code)

### ⚠️ PLACEHOLDER ID - SHOULD BE REPLACED

**Location:** Multiple files
**Video ID:** `dQw4w9WgXcQ`
**What it is:** Rick Astley - "Never Gonna Give You Up"
**URL:** https://www.youtube.com/watch?v=dQw4w9WgXcQ

**Found in these files:**
```python
# apps/backend/enhanced_app.py (line 259)
"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# apps/backend/app/services/intelligent_video_recommendation_engine.py (line 333)
'watch_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # Temporal

# apps/backend/app/services/video_service.py (lines 249-251)
{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Álgebra Básica"}
{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Geometría"}
{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "title": "Trigonometría"}
```

### Hardcoded in diagnostic_public.py

**Location:** `/root/IcfesLeveling/apps/backend/app/routes/diagnostic_public.py`

#### Mathematics Topic Videos (lines 849-853):
```python
("Álgebra Básica", "...", "https://www.youtube.com/watch?v=keb_HRF7zcY"),
("Geometría", "...", "https://www.youtube.com/watch?v=f2OKFNhGgqs"),
("Estadística", "...", "https://www.youtube.com/watch?v=FwslsWP4C9E"),
("Cálculo", "...", "https://www.youtube.com/watch?v=CfW845LNObM"),
("Trigonometría", "...", "https://www.youtube.com/watch?v=yBw67Fb31Cs"),
```

**Video IDs:**
- keb_HRF7zcY
- f2OKFNhGgqs
- FwslsWP4C9E
- CfW845LNObM
- yBw67Fb31Cs

#### Language Topic Videos (lines 856-860):
```python
("Comprensión Lectora", "...", "https://www.youtube.com/watch?v=6ycOGMOvD5s"),
("Gramática", "...", "https://www.youtube.com/watch?v=HtZ4Qs_AwgU"),
("Literatura", "...", "https://www.youtube.com/watch?v=Ww6OEQptuJM"),
("Redacción", "...", "https://www.youtube.com/watch?v=RFZiRNpKFeg"),
("Comunicación", "...", "https://www.youtube.com/watch?v=wYp92-3LPqg"),
```

**Video IDs:**
- 6ycOGMOvD5s
- HtZ4Qs_AwgU
- Ww6OEQptuJM
- RFZiRNpKFeg
- wYp92-3LPqg

#### Science Topic Videos (lines 863-867):
```python
("Biología", "...", "https://www.youtube.com/watch?v=Hmwvj9X4GNY"),
("Química", "...", "https://www.youtube.com/watch?v=Q_q284W0_ZU"),
("Física", "...", "https://www.youtube.com/watch?v=6QGPBl5E8GQ"),
("Ecología", "...", "https://www.youtube.com/watch?v=8XpO8dMCrbY"),
("Genética", "...", "https://www.youtube.com/watch?v=CBezq1fFUEA"),
```

**Video IDs:**
- Hmwvj9X4GNY
- Q_q284W0_ZU
- 6QGPBl5E8GQ
- 8XpO8dMCrbY
- CBezq1fFUEA

---

## 3. VIDEOS BY SUBJECT ID

### Subject: 550e8400-e29b-41d4-a716-446655440001 (Mathematics)

**Source:** `/root/IcfesLeveling/diagnostico/data/youtube_catalog_export.csv`

**13 Videos assigned to this subject:**

```
1.  TeqRLdEnkxQ - Álgebra Básica - Ecuaciones Lineales
    https://www.youtube.com/watch?v=TeqRLdEnkxQ

2.  2Vv-BfVoq4g - Geometría Euclidiana - Teoremas Básicos
    https://www.youtube.com/watch?v=2Vv-BfVoq4g

3.  wKJ9KzGQq0w - Estadística Descriptiva
    https://www.youtube.com/watch?v=wKJ9KzGQq0w

4.  WUvTyaaNkzM - Cálculo Diferencial - Derivadas
    https://www.youtube.com/watch?v=WUvTyaaNkzM

5.  iDulhoQ2pro - Trigonometría - Funciones Básicas
    https://www.youtube.com/watch?v=iDulhoQ2pro

6.  1xVSKhSLaiE - Funciones y Gráficas
    https://www.youtube.com/watch?v=1xVSKhSLaiE

7.  Zr_xWfThjJ0 - Probabilidad Básica
    https://www.youtube.com/watch?v=Zr_xWfThjJ0

8.  5twFdkhLwh4 - Números Reales y Operaciones
    https://www.youtube.com/watch?v=5twFdkhLwh4

9.  L6tqC6h3k6E - Trigonometría - Funciones Básicas (alt)
    https://www.youtube.com/watch?v=L6tqC6h3k6E

10. S0_qX4VJhMQ - Cálculo Diferencial - Derivadas (alt)
    https://www.youtube.com/watch?v=S0_qX4VJhMQ

11. uzkc-qNVoOk - Probabilidad y Combinatoria
    https://www.youtube.com/watch?v=uzkc-qNVoOk

12. 3M_5oYU-IsU - Funciones Matemáticas
    https://www.youtube.com/watch?v=3M_5oYU-IsU

13. AuX7nPBqDts - Sistemas de Ecuaciones
    https://www.youtube.com/watch?v=AuX7nPBqDts
```

---

## 4. VALIDATION RESULTS

### Format Check: ✅ ALL VALID

All 238 unique video IDs in the system have:
- ✅ Exactly 11 characters
- ✅ Only alphanumeric, dash, and underscore characters
- ✅ Valid YouTube ID format

### Example Format Validation:

```
Video ID: PTrOSGYC6BU
├─ Length: 11 chars ✓
├─ Characters: P,T,r,O,S,G,Y,C,6,B,U ✓
└─ Pattern: ^[a-zA-Z0-9_-]{11}$ ✓

Video ID: 2Vv-BfVoq4g
├─ Length: 11 chars ✓
├─ Characters: 2,V,v,-,B,f,V,o,q,4,g ✓
└─ Pattern: ^[a-zA-Z0-9_-]{11}$ ✓
```

---

## 5. QUICK TEST COMMANDS

### Test a specific video ID:
```bash
# Check if video exists (will redirect if valid)
curl -I "https://www.youtube.com/watch?v=PTrOSGYC6BU"

# Or just open in browser:
open "https://www.youtube.com/watch?v=PTrOSGYC6BU"
```

### Extract all video IDs from main catalog:
```bash
cut -d';' -f5 /root/IcfesLeveling/database/init/youtube_catalog_extendido_enriquecido.csv | \
  grep -oP '(?<=watch\?v=)[a-zA-Z0-9_-]{11}'
```

### Count unique video IDs:
```bash
cut -d';' -f5 /root/IcfesLeveling/database/init/youtube_catalog_extendido_enriquecido.csv | \
  grep -oP '(?<=watch\?v=)[a-zA-Z0-9_-]{11}' | \
  sort -u | wc -l
```

---

## 6. STATISTICS SUMMARY

```
📊 TOTAL VIDEO IDs IN SYSTEM: 257
    ├─ In main catalog CSV: 193 unique
    ├─ In diagnostico CSV: 45 unique
    └─ Hardcoded in code: 19 unique

✅ VALID FORMAT: 100% (all 257 IDs)
❌ INVALID FORMAT: 0
⚠️  PLACEHOLDER/RICKROLL: 1 (dQw4w9WgXcQ - should be replaced)
🔧 HARDCODED IN CODE: 19 (should move to database)

📁 CATALOG FILES:
    ├─ /root/IcfesLeveling/database/init/youtube_catalog_extendido_enriquecido.csv
    └─ /root/IcfesLeveling/diagnostico/data/youtube_catalog_export.csv

💻 CODE FILES WITH HARDCODED IDs:
    ├─ apps/backend/enhanced_app.py
    ├─ apps/backend/app/services/intelligent_video_recommendation_engine.py
    ├─ apps/backend/app/services/video_service.py
    ├─ apps/backend/app/routes/diagnostic_public.py
    └─ apps/frontend/app/video-player/page.tsx
```

---

## 7. ACTION ITEMS

### HIGH PRIORITY
- [ ] Replace `dQw4w9WgXcQ` (Rick Roll) in 4 files with real educational videos

### MEDIUM PRIORITY
- [ ] Move 15 hardcoded videos from `diagnostic_public.py` to database
- [ ] Create unified fallback video service

### LOW PRIORITY
- [ ] Implement periodic YouTube API validation
- [ ] Add monitoring for deleted/private videos
- [ ] Create video recommendation dashboard

---

**Last Updated:** 2025-10-20
**Total Videos Analyzed:** 257
**Validation Status:** ✅ All IDs have valid format
