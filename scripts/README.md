# Scripts Directory

Este directorio contiene scripts de utilidad para el proyecto ICFES Leveling.

## Estructura

```
scripts/
├── README.md                          # Este archivo
├── analysis/                          # Scripts de análisis de datos
│   ├── analyze_excel_structure.py
│   ├── analyze_file_optimization.py
│   └── analyze_icfes_excel.py
├── import/                            # Scripts de importación de datos
│   ├── generate_fixed_import_sql.py
│   ├── generate_import_sql.py
│   ├── import_questions.py
│   ├── import_questions_complete.py
│   ├── load_all_icfes_questions.py
│   └── load_questions_direct.py
├── migrations/                        # Scripts de migración de base de datos
│   ├── apply_hints_migration.py
│   ├── apply_migration_sqlalchemy.py
│   └── apply_tracking_migrations.py
├── tests/                             # Scripts de testing y validación
│   └── (scripts de testing)
├── utils/                             # Scripts de utilidad y validación
│   └── (scripts de verificación y validación)
└── *.py                               # Scripts principales
```

## Scripts Principales

### Importación y Datos
- `complete_import.py` - Importación completa de datos ICFES
- `final_data_loader.py` - Cargador final de datos
- `import_complete_excel_data.py` - Importación de datos desde Excel
- `load_youtube_catalog.py` - Carga del catálogo de videos de YouTube
- `seed_questions.py` - Seed de preguntas para testing
- `simple_seed_questions.py` - Seed simple de preguntas

### Sistemas y Motores
- `advanced_dashboard_system.py` - Sistema de dashboard avanzado
- `ai_study_system.py` - Sistema de estudio con IA
- `recommendation_engine.py` - Motor de recomendaciones
- `irt_3pl_engine.py` - Motor IRT 3PL para análisis de preguntas
- `diagnostic_flow_optimizer.py` - Optimizador de flujo diagnóstico

### Procesamiento de Imágenes
- `add_image_urls_to_questions.py` - Agregar URLs de imágenes a preguntas
- `update_questions_with_images.py` - Actualizar preguntas con imágenes
- `update_requiere_imagen_field.py` - Actualizar campo requiere_imagen
- `path_transformer.py` - Transformador de rutas de archivos

### Otros
- `icfes_subject_database_specialist.py` - Especialista en base de datos de materias
- `init_minio_buckets.py` - Inicializar buckets de MinIO
- `offline_sql_generator.py` - Generador de SQL offline
- `pdf_report_system.py` - Sistema de reportes PDF
- `practice_from_failures.py` - Sistema de práctica basado en errores
- `run_youtube_embeddings_pipeline.py` - Pipeline de embeddings de YouTube
- `analyze_questions_database.py` - Análisis de base de datos de preguntas

## Shell Scripts

- `backup_postgres.sh` - Backup de PostgreSQL
- `backup-system.sh` - Backup del sistema completo
- `generate-secrets.sh` - Generar secrets para producción
- `init-production.sh` - Inicializar producción
- `load-all-icfes-data.sh` - Cargar todos los datos ICFES
- `production-setup.sh` - Setup de producción
- `restore_postgres.sh` - Restaurar PostgreSQL
- `setup-complete-system.sh` - Setup del sistema completo

## Uso

### Testing
```bash
# Correr tests
cd scripts/tests
python test_complete_flow.py
```

### Validación
```bash
# Validar preguntas
cd scripts/utils
python validate_questions_comprehensive.py
```

### Importación
```bash
# Importar datos
cd scripts/import
python load_all_icfes_questions.py
```

## Notas

- Los scripts en `analysis/` son para análisis de datos y no deben ejecutarse en producción
- Los scripts en `tests/` son para testing y desarrollo
- Los scripts en `utils/` contienen validaciones y utilidades
- Los scripts principales en la raíz son los que se usan regularmente en operaciones
