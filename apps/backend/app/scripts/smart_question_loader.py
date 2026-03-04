#!/usr/bin/env python3
"""
Smart Question Loader with Intelligent Mapping
Seamlessly integrates ICFES Excel questions into the database
"""

import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import uuid
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartQuestionMapper:
    """Intelligent mapper for ICFES questions to database structure"""

    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'postgres'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'gameplay_db'),
            'user': os.getenv('DB_USER', 'gameplay'),
            'password': os.getenv('DB_PASSWORD', '')
        }
        self.conn = None
        self.cur = None
        self.subject_map = {}
        self.topic_map = {}
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.cur = self.conn.cursor()
            logger.info("✅ Connected to database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
    
    def load_subjects_and_topics(self):
        """Load existing subjects and topics into memory"""
        try:
            # Load subjects
            self.cur.execute("SELECT id, name FROM subjects")
            for row in self.cur.fetchall():
                self.subject_map[row[1].lower()] = row[0]
            logger.info(f"📚 Loaded {len(self.subject_map)} subjects")
            
            # Load or create topics table
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS topics (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    subject_id UUID REFERENCES subjects(id),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, subject_id)
                )
            """)
            
            # Load existing topics
            self.cur.execute("SELECT id, name, subject_id FROM topics")
            for row in self.cur.fetchall():
                key = f"{row[1].lower()}:{row[2]}"
                self.topic_map[key] = row[0]
            logger.info(f"📖 Loaded {len(self.topic_map)} topics")
            
        except Exception as e:
            logger.error(f"❌ Error loading subjects/topics: {e}")
    
    def get_or_create_topic(self, topic_name, subject_id):
        """Get existing topic or create new one"""
        if not topic_name:
            # Create a default topic for the subject if none specified
            topic_name = "General"
        
        key = f"{topic_name.lower()}:{subject_id}"
        
        if key in self.topic_map:
            return self.topic_map[key]
        
        # Create new topic
        topic_id = str(uuid.uuid4())
        try:
            self.cur.execute("""
                INSERT INTO topics (id, name, subject_id, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name, subject_id) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """, (topic_id, topic_name, subject_id, f"Tema: {topic_name}"))
            
            result = self.cur.fetchone()
            if result:
                topic_id = result[0]
            
            self.topic_map[key] = topic_id
            logger.info(f"  ✨ Created new topic: {topic_name}")
            return topic_id
            
        except Exception as e:
            logger.warning(f"  ⚠️ Error creating topic {topic_name}: {e}")
            # Return a default topic
            return self.get_default_topic(subject_id)
    
    def get_default_topic(self, subject_id):
        """Get or create a default topic for a subject"""
        return self.get_or_create_topic("General", subject_id)
    
    def map_subject(self, area_evaluada):
        """Map Excel subject to database subject_id"""
        if not area_evaluada:
            # Default to Matemáticas
            return self.subject_map.get('matemáticas')
        
        area_lower = area_evaluada.lower()
        
        # Direct mapping
        if area_lower in self.subject_map:
            return self.subject_map[area_lower]
        
        # Fuzzy matching
        for db_subject, subject_id in self.subject_map.items():
            if area_lower in db_subject or db_subject in area_lower:
                return subject_id
        
        # Default to Matemáticas
        logger.warning(f"  ⚠️ Unknown subject '{area_evaluada}', defaulting to Matemáticas")
        return self.subject_map.get('matemáticas')
    
    def map_difficulty(self, nivel_dificultad, nivel_desempeno=None):
        """Map difficulty level intelligently"""
        if pd.notna(nivel_dificultad):
            return int(nivel_dificultad)
        
        # Use performance level as fallback
        if pd.notna(nivel_desempeno):
            nivel_str = str(nivel_desempeno).lower()
            if 'mínimo' in nivel_str:
                return 1
            elif 'satisfactorio' in nivel_str:
                return 2
            elif 'avanzado' in nivel_str:
                return 3
        
        return 2  # Default medium difficulty
    
    def create_options_json(self, row):
        """Create options JSON object"""
        options = {}
        
        # Text options
        for opt in ['A', 'B', 'C', 'D']:
            col_name = f'Opcion_{opt}'
            if col_name in row and pd.notna(row[col_name]):
                options[opt] = str(row[col_name])
        
        return json.dumps(options) if options else None
    
    def create_options_images_json(self, row):
        """Create options images JSON object"""
        images = {}
        
        # Image URLs for options
        for opt in ['A', 'B', 'C', 'D']:
            col_name = f'Imagen_Opcion_{opt}_URL'
            if col_name in row and pd.notna(row[col_name]):
                images[opt] = str(row[col_name])
        
        return json.dumps(images) if images else None
    
    def create_power_stats(self, row):
        """Create power stats based on question attributes"""
        base_xp = int(row.get('Puntos_XP', 20))
        difficulty = self.map_difficulty(row.get('Nivel_Dificultad'))
        
        stats = {
            'xp_reward': base_xp,
            'orbs_reward': base_xp // 5,
            'power_bonus': difficulty * 2,
            'wisdom_bonus': difficulty * 2,
            'speed_bonus': max(1, 4 - difficulty),  # Easier questions = more speed
            'combo_multiplier': 1.0 + (difficulty * 0.1)
        }
        
        return json.dumps(stats)
    
    def create_tags(self, row):
        """Create tags array from various columns"""
        tags = []
        
        # Add competency as tag
        if pd.notna(row.get('Competencia')):
            tags.append(row['Competencia'])
        
        # Add cognitive process
        if pd.notna(row.get('Proceso_Cognitivo')):
            tags.append(row['Proceso_Cognitivo'])
        
        # Add component
        if pd.notna(row.get('Componente')):
            tags.append(row['Componente'])
        
        # Add area
        if pd.notna(row.get('Area_Tematica')):
            tags.append(row['Area_Tematica'])
        
        return tags if tags else None
    
    def combine_hints(self, row):
        """Combine multiple hints into one"""
        hints = []
        
        for i in range(1, 4):
            hint_col = f'Pista_{i}'
            if hint_col in row and pd.notna(row[hint_col]):
                hint_text = str(row[hint_col]).strip()
                if hint_text:
                    hints.append(hint_text)
        
        return " → ".join(hints) if hints else None
    
    def load_questions(self, filepath='/app/ICFES2 (1).xlsx'):
        """Load questions with intelligent mapping"""
        try:
            logger.info(f"📝 Loading questions from {filepath}")
            
            # Read Excel
            df = pd.read_excel(filepath)
            logger.info(f"  Found {len(df)} questions to load")
            
            # Load subjects and topics
            self.load_subjects_and_topics()
            
            # Clear existing questions (optional)
            self.cur.execute("DELETE FROM questions")
            logger.info("  🧹 Cleared existing questions")
            
            # Process each question
            questions_data = []
            for idx, row in df.iterrows():
                try:
                    # Map subject
                    subject_id = self.map_subject(row.get('Área_Evaluada'))
                    
                    # Get or create topic
                    topic_name = row.get('Tema_Específico') or row.get('Area_Tematica') or "General"
                    topic_id = self.get_or_create_topic(topic_name, subject_id)
                    
                    # Prepare question data
                    question_id = str(uuid.uuid4())
                    
                    # Main question text
                    pregunta_texto = str(row.get('Pregunta', ''))
                    
                    # Options as individual columns (Spanish naming)
                    opcion_a_texto = str(row.get('Opcion_A', '')) if pd.notna(row.get('Opcion_A')) else None
                    opcion_b_texto = str(row.get('Opcion_B', '')) if pd.notna(row.get('Opcion_B')) else None
                    opcion_c_texto = str(row.get('Opcion_C', '')) if pd.notna(row.get('Opcion_C')) else None
                    opcion_d_texto = str(row.get('Opcion_D', '')) if pd.notna(row.get('Opcion_D')) else None
                    
                    # Image URLs
                    pregunta_imagen = row.get('Imagen_Pregunta_URL') if pd.notna(row.get('Imagen_Pregunta_URL')) else None
                    opcion_a_imagen = row.get('Imagen_Opcion_A_URL') if pd.notna(row.get('Imagen_Opcion_A_URL')) else None
                    opcion_b_imagen = row.get('Imagen_Opcion_B_URL') if pd.notna(row.get('Imagen_Opcion_B_URL')) else None
                    opcion_c_imagen = row.get('Imagen_Opcion_C_URL') if pd.notna(row.get('Imagen_Opcion_C_URL')) else None
                    opcion_d_imagen = row.get('Imagen_Opcion_D_URL') if pd.notna(row.get('Imagen_Opcion_D_URL')) else None
                    
                    # Correct answer
                    respuesta_correcta = str(row.get('Respuesta_Correcta', 'A')).upper()[0]
                    
                    # Additional fields
                    difficulty = self.map_difficulty(
                        row.get('Nivel_Dificultad'), 
                        row.get('Nivel_Desempeño_Esperado')
                    )
                    
                    # English fields (for compatibility)
                    question_text = pregunta_texto  # Duplicate for English field
                    options_json = self.create_options_json(row)
                    correct_answer = respuesta_correcta
                    
                    # Explanation combining multiple fields
                    explanation_parts = []
                    if pd.notna(row.get('Explicación_Respuesta')):
                        explanation_parts.append(str(row['Explicación_Respuesta']))
                    if pd.notna(row.get('Error_Común')):
                        explanation_parts.append(f"Error común: {row['Error_Común']}")
                    if pd.notna(row.get('Afirmación')):
                        explanation_parts.append(f"Concepto: {row['Afirmación']}")
                    explanation = " | ".join(explanation_parts) if explanation_parts else None
                    
                    # Hint
                    hint = self.combine_hints(row)
                    
                    # Tags
                    tags = self.create_tags(row)
                    
                    # Power stats
                    power_stats = self.create_power_stats(row)
                    
                    # Question type
                    question_type = 'multimedia' if row.get('Requiere_Imagen') == 1 else 'standard'
                    
                    questions_data.append((
                        question_id,
                        topic_id,
                        subject_id,
                        pregunta_texto,
                        pregunta_imagen,
                        opcion_a_texto,
                        opcion_a_imagen,
                        opcion_b_texto,
                        opcion_b_imagen,
                        opcion_c_texto,
                        opcion_c_imagen,
                        opcion_d_texto,
                        opcion_d_imagen,
                        respuesta_correcta,
                        question_text,
                        question_type,
                        difficulty,
                        options_json,
                        correct_answer,
                        explanation,
                        hint,
                        tags,
                        power_stats
                    ))
                    
                except Exception as e:
                    logger.error(f"  ❌ Error processing row {idx}: {e}")
                    continue
            
            # Insert all questions
            if questions_data:
                query = """
                    INSERT INTO questions (
                        id, topic_id, subject_id, pregunta_texto, pregunta_imagen,
                        opcion_a_texto, opcion_a_imagen, opcion_b_texto, opcion_b_imagen,
                        opcion_c_texto, opcion_c_imagen, opcion_d_texto, opcion_d_imagen,
                        respuesta_correcta, question_text, question_type, difficulty,
                        options, correct_answer, explanation, hint, tags, power_stats
                    ) VALUES %s
                """
                
                execute_values(self.cur, query, questions_data)
                self.conn.commit()
                
                logger.info(f"✅ Successfully loaded {len(questions_data)} questions")
                
                # Verify
                self.cur.execute("SELECT COUNT(*) FROM questions")
                count = self.cur.fetchone()[0]
                logger.info(f"📊 Total questions in database: {count}")
                
                # Show distribution
                self.cur.execute("""
                    SELECT s.name, COUNT(q.id) 
                    FROM questions q 
                    JOIN subjects s ON q.subject_id = s.id 
                    GROUP BY s.name
                """)
                
                logger.info("📈 Question distribution by subject:")
                for row in self.cur.fetchall():
                    logger.info(f"  - {row[0]}: {row[1]} questions")
                
                return True
            else:
                logger.warning("⚠️ No questions to load")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error loading questions: {e}")
            self.conn.rollback()
            return False
    
    def run(self):
        """Execute the smart loading process"""
        logger.info("🚀 Starting Smart Question Loader")
        
        if not self.connect():
            return False
        
        try:
            success = self.load_questions()
            
            if success:
                logger.info("✅ Smart Question Loading completed successfully!")
            else:
                logger.warning("⚠️ Question loading completed with issues")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            return False
            
        finally:
            self.close()

if __name__ == "__main__":
    loader = SmartQuestionMapper()
    loader.run()