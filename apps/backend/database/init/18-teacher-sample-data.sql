-- PASO 18: Datos de ejemplo para el sistema de docentes
-- Poblar con datos realistas para demostración

-- Insertar docente de ejemplo
INSERT INTO teachers (id, user_id, teacher_code, first_name, last_name, email, phone, institution, department, specialization, years_experience, bio, preferences) VALUES
('550e8400-e29b-41d4-a716-446655440001', 
 (SELECT id FROM users WHERE username = 'admin' LIMIT 1),
 'PROF001',
 'María',
 'González',
 'maria.gonzalez@colegio.edu.co',
 '+57 300 123 4567',
 'Colegio San Martín de Porres',
 'Matemáticas y Ciencias',
 'Matemáticas Aplicadas, Física',
 15,
 'Licenciada en Matemáticas con Maestría en Educación. Especialista en metodologías innovadoras para la enseñanza de STEM.',
 '{
   "theme": "academic",
   "notifications": {
     "student_alerts": true,
     "performance_reports": true,
     "weekly_summary": true
   },
   "dashboard_layout": "default",
   "preferred_chart_types": ["bar", "line", "heatmap"],
   "auto_export_schedule": "weekly"
 }');

-- Insertar clases de ejemplo
INSERT INTO classes (id, teacher_id, class_name, class_code, subject_id, grade_level, semester, academic_year, description, max_students, current_students, schedule, classroom, status, start_date, end_date) VALUES
('650e8400-e29b-41d4-a716-446655440001',
 '550e8400-e29b-41d4-a716-446655440001',
 'Matemáticas 11°A',
 'MAT11A',
 (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1),
 '11',
 '2024-1',
 2024,
 'Curso de matemáticas para grado undécimo, enfoque en preparación ICFES',
 30,
 28,
 '{
   "monday": {"start": "08:00", "end": "09:30"},
   "wednesday": {"start": "10:00", "end": "11:30"},
   "friday": {"start": "08:00", "end": "09:30"}
 }',
 'Aula 205',
 'active',
 '2024-01-15',
 '2024-06-30'),

('650e8400-e29b-41d4-a716-446655440002',
 '550e8400-e29b-41d4-a716-446655440001',
 'Física 10°B',
 'FIS10B',
 (SELECT id FROM subjects WHERE name = 'Ciencias Naturales' LIMIT 1),
 '10',
 '2024-1',
 2024,
 'Curso de física para grado décimo, conceptos fundamentales y aplicaciones',
 32,
 30,
 '{
   "tuesday": {"start": "14:00", "end": "15:30"},
   "thursday": {"start": "14:00", "end": "15:30"}
 }',
 'Lab. Física',
 'active',
 '2024-01-15',
 '2024-06-30'),

('650e8400-e29b-41d4-a716-446655440003',
 '550e8400-e29b-41d4-a716-446655440001',
 'Química 11°C',
 'QUI11C',
 (SELECT id FROM subjects WHERE name = 'Ciencias Naturales' LIMIT 1),
 '11',
 '2024-1',
 2024,
 'Curso de química avanzada para grado undécimo',
 28,
 26,
 '{
   "monday": {"start": "14:00", "end": "15:30"},
   "friday": {"start": "10:00", "end": "11:30"}
 }',
 'Lab. Química',
 'active',
 '2024-01-15',
 '2024-06-30');

-- Crear usuarios estudiantes de ejemplo para las clases
INSERT INTO users (id, username, email, hashed_password, level, experience, rank, hp, mp, power, wisdom, speed, orbs, crystals) VALUES
('user001', 'carlos.rodriguez', 'carlos.rodriguez@estudiante.edu', '$2b$10$hashedpassword1', 25, 12500, 'B', 95, 60, 18, 22, 15, 150, 25),
('user002', 'ana.lopez', 'ana.lopez@estudiante.edu', '$2b$10$hashedpassword2', 32, 18400, 'A', 110, 75, 24, 28, 20, 320, 45),
('user003', 'diego.martinez', 'diego.martinez@estudiante.edu', '$2b$10$hashedpassword3', 18, 8200, 'C', 85, 45, 12, 16, 12, 80, 15),
('user004', 'lucia.fernandez', 'lucia.fernandez@estudiante.edu', '$2b$10$hashedpassword4', 41, 28600, 'S', 130, 90, 35, 38, 28, 580, 85),
('user005', 'pablo.garcia', 'pablo.garcia@estudiante.edu', '$2b$10$hashedpassword5', 15, 5800, 'D', 75, 35, 8, 12, 10, 45, 8),
('user006', 'sofia.ruiz', 'sofia.ruiz@estudiante.edu', '$2b$10$hashedpassword6', 28, 15200, 'B', 100, 65, 20, 25, 18, 200, 32),
('user007', 'andres.morales', 'andres.morales@estudiante.edu', '$2b$10$hashedpassword7', 22, 10800, 'C', 90, 50, 15, 19, 14, 120, 20),
('user008', 'camila.torres', 'camila.torres@estudiante.edu', '$2b$10$hashedpassword8', 36, 22100, 'A', 115, 80, 28, 32, 24, 420, 62);

-- Inscribir estudiantes en las clases
INSERT INTO class_enrollments (class_id, user_id, enrollment_date, status, attendance_percentage, last_activity) VALUES
-- Matemáticas 11°A
('650e8400-e29b-41d4-a716-446655440001', 'user001', '2024-01-15', 'active', 95.5, NOW() - INTERVAL '2 days'),
('650e8400-e29b-41d4-a716-446655440001', 'user002', '2024-01-15', 'active', 98.2, NOW() - INTERVAL '1 day'),
('650e8400-e29b-41d4-a716-446655440001', 'user003', '2024-01-15', 'active', 78.5, NOW() - INTERVAL '10 days'),
('650e8400-e29b-41d4-a716-446655440001', 'user004', '2024-01-15', 'active', 99.1, NOW() - INTERVAL '6 hours'),
('650e8400-e29b-41d4-a716-446655440001', 'user005', '2024-01-15', 'active', 65.2, NOW() - INTERVAL '15 days'),
('650e8400-e29b-41d4-a716-446655440001', 'user006', '2024-01-15', 'active', 92.8, NOW() - INTERVAL '1 day'),
('650e8400-e29b-41d4-a716-446655440001', 'user007', '2024-01-15', 'active', 85.4, NOW() - INTERVAL '3 days'),
('650e8400-e29b-41d4-a716-446655440001', 'user008', '2024-01-15', 'active', 96.7, NOW() - INTERVAL '8 hours'),

-- Física 10°B
('650e8400-e29b-41d4-a716-446655440002', 'user001', '2024-01-15', 'active', 88.9, NOW() - INTERVAL '1 day'),
('650e8400-e29b-41d4-a716-446655440002', 'user002', '2024-01-15', 'active', 94.3, NOW() - INTERVAL '12 hours'),
('650e8400-e29b-41d4-a716-446655440002', 'user003', '2024-01-15', 'active', 82.1, NOW() - INTERVAL '4 days'),
('650e8400-e29b-41d4-a716-446655440002', 'user006', '2024-01-15', 'active', 91.5, NOW() - INTERVAL '2 days'),
('650e8400-e29b-41d4-a716-446655440002', 'user007', '2024-01-15', 'active', 79.8, NOW() - INTERVAL '6 days'),

-- Química 11°C
('650e8400-e29b-41d4-a716-446655440003', 'user002', '2024-01-15', 'active', 97.1, NOW() - INTERVAL '10 hours'),
('650e8400-e29b-41d4-a716-446655440003', 'user004', '2024-01-15', 'active', 98.8, NOW() - INTERVAL '4 hours'),
('650e8400-e29b-41d4-a716-446655440003', 'user006', '2024-01-15', 'active', 89.4, NOW() - INTERVAL '2 days'),
('650e8400-e29b-41d4-a716-446655440003', 'user008', '2024-01-15', 'active', 95.2, NOW() - INTERVAL '1 day');

-- Insertar performance de estudiantes por tema (datos realistas)
INSERT INTO student_topic_performance (user_id, class_id, topic_id, subject_id, mastery_level, questions_attempted, questions_correct, avg_response_time_ms, difficulty_progression, last_practice, streak_days, theta_score) VALUES
-- Carlos Rodríguez (user001) - Matemáticas
('user001', '650e8400-e29b-41d4-a716-446655440001', (SELECT id FROM topics WHERE name LIKE '%Álgebra%' LIMIT 1), (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1), 45.2, 45, 20, 12500, 2.1, NOW() - INTERVAL '10 days', 0, -0.85),
('user001', '650e8400-e29b-41d4-a716-446655440001', (SELECT id FROM topics WHERE name LIKE '%Geometría%' LIMIT 1), (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1), 52.8, 38, 20, 11800, 2.3, NOW() - INTERVAL '8 days', 0, -0.42),
('user001', '650e8400-e29b-41d4-a716-446655440001', (SELECT id FROM topics WHERE name LIKE '%Estadística%' LIMIT 1), (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1), 38.1, 42, 16, 13200, 1.9, NOW() - INTERVAL '12 days', 0, -1.12),

-- Ana López (user002) - Matemáticas - Alto rendimiento
('user002', '650e8400-e29b-41d4-a716-446655440001', (SELECT id FROM topics WHERE name LIKE '%Álgebra%' LIMIT 1), (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1), 87.5, 68, 59, 8200, 4.2, NOW() - INTERVAL '1 day', 8, 1.45),
('user002', '650e8400-e29b-41d4-a716-446655440001', (SELECT id FROM topics WHERE name LIKE '%Geometría%' LIMIT 1), (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1), 82.3, 55, 45, 7800, 4.0, NOW() - INTERVAL '2 days', 6, 1.28),
('user002', '650e8400-e29b-41d4-a716-446655440001', (SELECT id FROM topics WHERE name LIKE '%Estadística%' LIMIT 1), (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1), 91.2, 72, 66, 7500, 4.5, NOW() - INTERVAL '1 day', 12, 1.68),

-- Diego Martínez (user003) - Matemáticas - Bajo rendimiento
('user003', '650e8400-e29b-41d4-a716-446655440001', (SELECT id FROM topics WHERE name LIKE '%Álgebra%' LIMIT 1), (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1), 34.8, 32, 11, 15800, 1.8, NOW() - INTERVAL '15 days', 0, -1.42),
('user003', '650e8400-e29b-41d4-a716-446655440001', (SELECT id FROM topics WHERE name LIKE '%Geometría%' LIMIT 1), (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1), 41.2, 28, 12, 14200, 2.0, NOW() - INTERVAL '18 days', 0, -1.08),
('user003', '650e8400-e29b-41d4-a716-446655440001', (SELECT id FROM topics WHERE name LIKE '%Estadística%' LIMIT 1), (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1), 29.5, 35, 10, 16500, 1.6, NOW() - INTERVAL '20 days', 0, -1.65);

-- Insertar KPIs diarios de clase
INSERT INTO class_daily_kpis (class_id, date, total_students, active_students, inactive_students, avg_mastery, avg_mastery_math, avg_mastery_spanish, avg_mastery_science, avg_mastery_social, avg_mastery_english, total_battles, total_questions_answered, total_correct_answers, avg_response_time_ms, rpg_distribution, progress_delta_30d) VALUES
-- Matemáticas 11°A - Últimos 7 días
('650e8400-e29b-41d4-a716-446655440001', CURRENT_DATE, 28, 24, 4, 74.2, 74.2, 0, 0, 0, 0, 342, 2847, 2114, 8500, '{"E": 2, "D": 4, "C": 8, "B": 7, "A": 5, "S": 2, "S+": 0}', 8.7),
('650e8400-e29b-41d4-a716-446655440001', CURRENT_DATE - 1, 28, 25, 3, 72.8, 72.8, 0, 0, 0, 0, 328, 2680, 1950, 8800, '{"E": 2, "D": 5, "C": 8, "B": 6, "A": 5, "S": 2, "S+": 0}', 7.2),
('650e8400-e29b-41d4-a716-446655440001', CURRENT_DATE - 2, 28, 26, 2, 71.5, 71.5, 0, 0, 0, 0, 315, 2520, 1890, 9100, '{"E": 3, "D": 4, "C": 9, "B": 6, "A": 4, "S": 2, "S+": 0}', 6.8),
('650e8400-e29b-41d4-a716-446655440001', CURRENT_DATE - 3, 28, 23, 5, 70.1, 70.1, 0, 0, 0, 0, 298, 2380, 1785, 9400, '{"E": 3, "D": 5, "C": 8, "B": 7, "A": 3, "S": 2, "S+": 0}', 5.9),

-- Física 10°B
('650e8400-e29b-41d4-a716-446655440002', CURRENT_DATE, 30, 27, 3, 68.5, 0, 0, 68.5, 0, 0, 285, 2240, 1532, 9200, '{"E": 3, "D": 6, "C": 12, "B": 6, "A": 3, "S": 0, "S+": 0}', 5.3),
('650e8400-e29b-41d4-a716-446655440002', CURRENT_DATE - 1, 30, 28, 2, 67.2, 0, 0, 67.2, 0, 0, 272, 2180, 1465, 9500, '{"E": 3, "D": 7, "C": 11, "B": 6, "A": 3, "S": 0, "S+": 0}', 4.8),

-- Química 11°C
('650e8400-e29b-41d4-a716-446655440003', CURRENT_DATE, 26, 22, 4, 71.8, 0, 0, 71.8, 0, 0, 198, 1680, 1206, 8900, '{"E": 2, "D": 3, "C": 10, "B": 7, "A": 4, "S": 0, "S+": 0}', -2.1),
('650e8400-e29b-41d4-a716-446655440003', CURRENT_DATE - 1, 26, 24, 2, 73.2, 0, 0, 73.2, 0, 0, 205, 1740, 1274, 8600, '{"E": 1, "D": 3, "C": 10, "B": 8, "A": 4, "S": 0, "S+": 0}', -1.5);

-- Insertar análisis de distractores
INSERT INTO distractor_analysis (question_id, class_id, distractor_option, selection_count, selection_percentage, avg_student_level, common_error_pattern, pedagogical_insight, intervention_suggestion) VALUES
-- Pregunta de álgebra en Matemáticas 11°A
((SELECT id FROM questions WHERE question_text LIKE '%2x + 5 = 13%' LIMIT 1), '650e8400-e29b-41d4-a716-446655440001', 'A', 8, 28.6, 15.2, 'Error de operación básica', 'Estudiantes confunden resta con suma en despeje', 'Reforzar operaciones inversas con ejercicios guiados'),
((SELECT id FROM questions WHERE question_text LIKE '%2x + 5 = 13%' LIMIT 1), '650e8400-e29b-41d4-a716-446655440001', 'B', 15, 53.6, 25.8, 'Respuesta correcta', 'Más de la mitad domina el despeje básico', 'Continuar con problemas de mayor complejidad'),
((SELECT id FROM questions WHERE question_text LIKE '%2x + 5 = 13%' LIMIT 1), '650e8400-e29b-41d4-a716-446655440001', 'C', 3, 10.7, 12.1, 'No realiza operación de despeje', 'Pocos estudiantes suman directamente sin despejar', 'Explicar concepto de ecuación y despeje'),
((SELECT id FROM questions WHERE question_text LIKE '%2x + 5 = 13%' LIMIT 1), '650e8400-e29b-41d4-a716-446655440001', 'D', 2, 7.1, 8.5, 'Multiplica en lugar de dividir', 'Confusión conceptual sobre operaciones inversas', 'Práctica intensiva con manipulativos algebraicos');

-- Insertar alertas de estudiantes en riesgo
INSERT INTO student_risk_alerts (id, user_id, class_id, teacher_id, risk_level, alert_type, description, risk_factors, suggested_actions, priority, is_resolved, created_at) VALUES
('alert001', 'user001', '650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'critical', 'academic', 'Bajo rendimiento académico crítico en Matemáticas', 
'{"lowMastery": true, "noRecentActivity": true, "poorAttendance": false, "longAbsence": true, "decreasingPerformance": true, "socialIssues": false}',
'["Contactar inmediatamente al estudiante y padres", "Programar reunión individual urgente", "Evaluar necesidad de plan de recuperación", "Considerar tutoría personalizada"]',
10, false, NOW() - INTERVAL '2 days'),

('alert002', 'user003', '650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'high', 'attendance', 'Asistencia irregular que afecta rendimiento',
'{"lowMastery": true, "noRecentActivity": true, "poorAttendance": true, "longAbsence": false, "decreasingPerformance": true, "socialIssues": false}',
'["Contactar a padres de familia", "Investigar causas de las ausencias", "Proporcionar material de recuperación", "Establecer plan de seguimiento"]',
8, false, NOW() - INTERVAL '5 days'),

('alert003', 'user005', '650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'medium', 'engagement', 'Baja participación y compromiso en clase',
'{"lowMastery": false, "noRecentActivity": true, "poorAttendance": false, "longAbsence": false, "decreasingPerformance": false, "socialIssues": true}',
'["Conversación personal con el estudiante", "Revisar dinámicas grupales", "Implementar actividades más interactivas", "Seguimiento semanal"]',
5, false, NOW() - INTERVAL '3 days');

-- Insertar intervenciones pedagógicas
INSERT INTO pedagogical_interventions (id, class_id, teacher_id, intervention_type, target_students, target_topics, title, description, intervention_data, scheduled_date, effectiveness_score, status) VALUES
('int001', '650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'group', '{"user001", "user003", "user005"}', 
ARRAY[(SELECT id FROM topics WHERE name LIKE '%Álgebra%' LIMIT 1)],
'Refuerzo de Álgebra Básica',
'Sesión grupal para reforzar operaciones de despeje y conceptos de álgebra lineal',
'{
  "duration_minutes": 45,
  "materials": ["Manipulativos algebraicos", "Ejercicios guiados", "Videos explicativos"],
  "assessment_method": "Evaluación práctica post-intervención",
  "follow_up_date": "2024-02-15"
}',
NOW() + INTERVAL '2 days',
0.78,
'planned'),

('int002', '650e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'individual', '{"user001"}',
ARRAY[(SELECT id FROM topics WHERE name LIKE '%Álgebra%' LIMIT 1), (SELECT id FROM topics WHERE name LIKE '%Estadística%' LIMIT 1)],
'Tutoría Individual Carlos R.',
'Sesión individual intensiva para abordar dificultades específicas en álgebra y estadística',
'{
  "duration_minutes": 60,
  "focus_areas": ["Despeje de ecuaciones", "Interpretación de gráficos estadísticos"],
  "parent_contact": true,
  "recovery_plan": true
}',
NOW() + INTERVAL '1 day',
0.85,
'active');

-- Función para generar datos históricos de KPIs (ejecutar después de la inserción)
DO $$
DECLARE
    class_record RECORD;
    day_offset INTEGER;
    base_mastery DECIMAL;
    daily_variation DECIMAL;
BEGIN
    -- Generar datos históricos para los últimos 30 días
    FOR class_record IN SELECT id, class_name FROM classes LOOP
        base_mastery := 70.0 + (RANDOM() * 20); -- Base entre 70-90%
        
        FOR day_offset IN 1..30 LOOP
            daily_variation := (RANDOM() - 0.5) * 5; -- Variación de ±2.5%
            
            INSERT INTO class_daily_kpis (
                class_id, 
                date, 
                total_students, 
                active_students, 
                inactive_students,
                avg_mastery,
                total_battles,
                total_questions_answered,
                total_correct_answers,
                avg_response_time_ms,
                rpg_distribution,
                progress_delta_30d
            ) VALUES (
                class_record.id,
                CURRENT_DATE - day_offset,
                28 + ROUND(RANDOM() * 4), -- 28-32 estudiantes
                24 + ROUND(RANDOM() * 4), -- 24-28 activos
                2 + ROUND(RANDOM() * 3),  -- 2-5 inactivos
                GREATEST(30, LEAST(95, base_mastery + daily_variation)),
                200 + ROUND(RANDOM() * 100), -- 200-300 batallas
                1500 + ROUND(RANDOM() * 800), -- 1500-2300 preguntas
                1000 + ROUND(RANDOM() * 600), -- 1000-1600 correctas
                8000 + ROUND(RANDOM() * 2000), -- 8-10 segundos
                FORMAT('{"E": %s, "D": %s, "C": %s, "B": %s, "A": %s, "S": %s, "S+": %s}',
                    ROUND(RANDOM() * 3),
                    ROUND(RANDOM() * 6),
                    ROUND(RANDOM() * 10),
                    ROUND(RANDOM() * 8),
                    ROUND(RANDOM() * 5),
                    ROUND(RANDOM() * 3),
                    ROUND(RANDOM() * 1)
                )::jsonb,
                (RANDOM() - 0.5) * 20 -- Delta entre -10% y +10%
            )
            ON CONFLICT (class_id, date) DO NOTHING;
        END LOOP;
    END LOOP;
END $$;