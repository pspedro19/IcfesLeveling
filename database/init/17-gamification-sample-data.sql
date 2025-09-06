-- Sample Data for Complete Gamification System
-- Solo Leveling Themed ICFES Platform

-- Sample Dungeon Gates
INSERT INTO dungeon_gates (name, description, gate_type, difficulty_rank, subject_id, recommended_level, total_rooms, time_limit_minutes, base_experience_reward, base_orb_reward, base_crystal_reward) VALUES
-- E-Rank Gates (Beginner)
('Gate of Basic Mathematics', 'A beginner dungeon focusing on fundamental math concepts', 'normal', 'E', (SELECT id FROM subjects WHERE name ILIKE '%matemática%' LIMIT 1), 1, 3, 30, 50, 25, 0),
('Apprentice Science Lab', 'Simple experiments and basic scientific principles', 'normal', 'E', (SELECT id FROM subjects WHERE name ILIKE '%ciencias%' LIMIT 1), 1, 3, 30, 50, 25, 0),
('Reading Comprehension Cavern', 'Basic reading skills and text understanding', 'normal', 'E', (SELECT id FROM subjects WHERE name ILIKE '%lectura%' LIMIT 1), 1, 3, 30, 50, 25, 0),

-- D-Rank Gates (Intermediate)
('Algebraic Fortress', 'Advanced algebra and equation solving', 'normal', 'D', (SELECT id FROM subjects WHERE name ILIKE '%matemática%' LIMIT 1), 5, 4, 45, 100, 50, 1),
('Chemistry Laboratory', 'Chemical reactions and molecular structures', 'normal', 'D', (SELECT id FROM subjects WHERE name ILIKE '%ciencias%' LIMIT 1), 5, 4, 45, 100, 50, 1),
('Grammar Citadel', 'Complex grammar rules and text analysis', 'normal', 'D', (SELECT id FROM subjects WHERE name ILIKE '%lectura%' LIMIT 1), 5, 4, 45, 100, 50, 1),

-- C-Rank Gates (Advanced)
('Calculus Colosseum', 'Derivatives, integrals, and advanced calculus', 'normal', 'C', (SELECT id FROM subjects WHERE name ILIKE '%matemática%' LIMIT 1), 10, 5, 60, 200, 100, 3),
('Physics Arena', 'Complex physics problems and theories', 'normal', 'C', (SELECT id FROM subjects WHERE name ILIKE '%ciencias%' LIMIT 1), 10, 5, 60, 200, 100, 3),
('Literature Labyrinth', 'Advanced literary analysis and interpretation', 'normal', 'C', (SELECT id FROM subjects WHERE name ILIKE '%lectura%' LIMIT 1), 10, 5, 60, 200, 100, 3),

-- Boss Gates
('Monarch of Mathematics', 'Face the ultimate math challenges', 'boss', 'B', (SELECT id FROM subjects WHERE name ILIKE '%matemática%' LIMIT 1), 15, 6, 90, 500, 300, 10),
('Science Sovereign', 'Battle against the lord of all sciences', 'boss', 'B', (SELECT id FROM subjects WHERE name ILIKE '%ciencias%' LIMIT 1), 15, 6, 90, 500, 300, 10),

-- Red Gates (High Difficulty)
('Crimson Gate: Mathematical Chaos', 'A dangerous gate where math becomes deadly', 'red', 'A', (SELECT id FROM subjects WHERE name ILIKE '%matemática%' LIMIT 1), 20, 8, 120, 1000, 500, 25),
('Scarlet Portal: Scientific Anomaly', 'Reality bends to unnatural scientific laws', 'red', 'A', (SELECT id FROM subjects WHERE name ILIKE '%ciencias%' LIMIT 1), 20, 8, 120, 1000, 500, 25);

-- Sample Dungeon Monsters
INSERT INTO dungeon_monsters (name, description, monster_type, rank, level, health, attack, defense, magic_power, speed, shadow_type, can_be_extracted, extraction_difficulty, preferred_subjects, questions_per_encounter) VALUES
-- E-Rank Monsters
('Math Goblin', 'A small creature that hurls basic arithmetic problems', 'humanoid', 'E', 1, 50, 8, 3, 2, 12, 'beast', TRUE, 35.0, '[]', 2),
('Formula Imp', 'Mischievous imp that loves simple equations', 'humanoid', 'E', 2, 60, 10, 4, 3, 10, 'mage', TRUE, 30.0, '[]', 2),
('Reading Rat', 'Quick rodent that tests basic comprehension', 'beast', 'E', 1, 40, 6, 2, 1, 15, 'assassin', TRUE, 40.0, '[]', 1),

-- D-Rank Monsters
('Algebra Knight', 'Armored warrior wielding quadratic equations', 'humanoid', 'D', 5, 150, 20, 15, 8, 8, 'knight', TRUE, 25.0, '[]', 3),
('Chemistry Wraith', 'Ghostly figure surrounded by molecular bonds', 'undead', 'D', 6, 120, 15, 8, 25, 12, 'mage', TRUE, 20.0, '[]', 3),
('Grammar Guardian', 'Protector of proper sentence structure', 'humanoid', 'D', 5, 140, 18, 12, 15, 10, 'knight', TRUE, 25.0, '[]', 3),

-- C-Rank Monsters  
('Calculus Demon', 'Fearsome demon master of derivatives', 'humanoid', 'C', 10, 300, 35, 20, 40, 15, 'mage', TRUE, 15.0, '[]', 4),
('Physics Phantom', 'Ethereal being that controls natural laws', 'undead', 'C', 11, 280, 30, 18, 45, 18, 'mage', TRUE, 18.0, '[]', 4),
('Literature Lich', 'Undead scholar of ancient texts', 'undead', 'C', 12, 350, 25, 25, 50, 8, 'mage', TRUE, 12.0, '[]', 5),

-- Boss Monsters
('The Mathematical Overlord', 'Supreme ruler of all mathematical domains', 'humanoid', 'B', 15, 800, 60, 40, 80, 12, 'knight', TRUE, 5.0, '[]', 6),
('Grand Scientist', 'Master of all scientific knowledge', 'humanoid', 'B', 16, 850, 55, 35, 90, 15, 'mage', TRUE, 5.0, '[]', 6),

-- A-Rank Red Gate Monsters
('Chaos Mathematician', 'Reality-bending entity of pure mathematics', 'elemental', 'A', 20, 1200, 80, 60, 100, 20, 'mage', TRUE, 2.0, '[]', 8),
('Quantum Anomaly', 'Being that exists in multiple states simultaneously', 'elemental', 'A', 22, 1500, 90, 50, 120, 25, 'beast', TRUE, 1.0, '[]', 10);

-- Sample Quest Templates
INSERT INTO quest_templates (name, description, quest_type, category, target_type, target_value, difficulty, rarity, base_experience, base_orbs, base_crystals) VALUES
-- Daily Quests
('Daily Study Session', 'Complete a study session today', 'daily', 'study', 'study_sessions', 1, 'easy', 'common', 25, 15, 0),
('Answer the Call', 'Answer 10 questions correctly', 'daily', 'study', 'correct_answers', 10, 'normal', 'common', 50, 25, 0),
('Battle Ready', 'Win 3 battles against any enemy', 'daily', 'battle', 'battles_won', 3, 'normal', 'common', 75, 35, 1),
('Shadow Commander', 'Use shadow soldiers in battle 2 times', 'daily', 'battle', 'shadow_summons', 2, 'normal', 'rare', 100, 50, 2),

-- Weekly Quests
('Weekly Warrior', 'Win 15 battles this week', 'weekly', 'battle', 'battles_won', 15, 'normal', 'rare', 200, 100, 5),
('Knowledge Seeker', 'Study for 5 hours this week', 'weekly', 'study', 'study_hours', 5, 'normal', 'rare', 250, 120, 5),
('Gate Clearer', 'Complete 3 different dungeon gates', 'weekly', 'exploration', 'gates_cleared', 3, 'hard', 'epic', 400, 200, 10),
('Shadow Master', 'Extract 2 new shadow soldiers', 'weekly', 'battle', 'shadows_extracted', 2, 'hard', 'epic', 500, 250, 15),

-- Monthly Quests
('Monthly Champion', 'Reach the top 10 on any leaderboard', 'monthly', 'social', 'leaderboard_rank', 10, 'extreme', 'legendary', 1000, 500, 50),
('Dungeon Conqueror', 'Complete 20 dungeon runs', 'monthly', 'exploration', 'dungeon_runs', 20, 'hard', 'epic', 800, 400, 25),
('Perfect Scholar', 'Achieve 90%+ accuracy on 50 questions', 'monthly', 'study', 'high_accuracy_questions', 50, 'extreme', 'legendary', 1200, 600, 75);

-- Sample Quest Chains
INSERT INTO quest_chains (name, description, chain_type, quest_order, total_quests, completion_rewards, chain_title) VALUES
('Hunter Awakening', 'Your journey from E-Rank to true power begins', 'storyline', 
 '["first_battle", "first_gate", "first_shadow", "rank_advancement"]', 4,
 '{"experience": 1000, "orbs": 500, "crystals": 50, "special_item": "Awakening Crystal"}',
 'Awakened Hunter'),

('Mathematics Mastery', 'Master all aspects of mathematical knowledge', 'mastery',
 '["basic_math", "algebra_expert", "calculus_master", "math_overlord"]', 4,
 '{"experience": 2000, "orbs": 1000, "crystals": 100, "special_item": "Crown of Mathematics"}',
 'Mathematical Sage'),

('Shadow Army Commander', 'Build and command the ultimate shadow army', 'mastery',
 '["first_extraction", "shadow_formation", "elite_shadows", "shadow_monarch"]', 4,
 '{"experience": 3000, "orbs": 1500, "crystals": 200, "special_ability": "Shadow Domain"}',
 'Shadow Monarch');

-- Sample Special Events
INSERT INTO special_events (name, description, event_type, start_date, end_date, is_recurring, special_rewards, point_system) VALUES
('Halloween Horror Gates', 'Spooky themed dungeons with special monsters', 'holiday', 
 '2024-10-20 00:00:00', '2024-11-05 23:59:59', TRUE,
 '{"halloween_costume": "Phantom Scholar", "special_pet": "Ghost Companion", "crystals": 200}',
 '{"monster_kills": 10, "gate_completions": 50, "perfect_clears": 100}'),

('Winter Study Festival', 'Special winter-themed learning challenges', 'seasonal',
 '2024-12-15 00:00:00', '2025-01-15 23:59:59', TRUE,
 '{"winter_title": "Frost Scholar", "special_shadow": "Ice Knight", "orbs": 5000}',
 '{"study_hours": 20, "perfect_scores": 30, "streak_days": 50}'),

('Spring Awakening Tournament', 'Guild vs Guild combat tournament', 'seasonal',
 '2024-03-20 00:00:00', '2024-04-20 23:59:59', TRUE,
 '{"champion_crown": "Spring Victor", "guild_rewards": "Territory Expansion", "crystals": 1000}',
 '{"tournament_wins": 100, "guild_contribution": 50, "mvp_votes": 200}');

-- Initialize Shadow Abilities
INSERT INTO shadow_abilities (name, description, ability_type, shadow_type_requirement, rank_requirement, damage_multiplier, mana_cost, cooldown_turns) VALUES
-- Knight Abilities
('Shield Bash', 'Stuns enemy for 1 turn while dealing damage', 'active', 'knight', 'E', 1.2, 15, 2),
('Taunt', 'Forces enemy to attack only this shadow', 'active', 'knight', 'E', 0.8, 10, 3),
('Guardian Stance', 'Reduces damage taken by 50% for 3 turns', 'active', 'knight', 'D', 0.0, 25, 4),
('Righteous Strike', 'Powerful attack that deals extra damage to evil enemies', 'active', 'knight', 'C', 2.0, 30, 3),

-- Mage Abilities
('Magic Missile', 'Ranged attack that never misses', 'active', 'mage', 'E', 1.5, 20, 1),
('Mana Shield', 'Uses mana to absorb damage', 'passive', 'mage', 'E', 0.0, 0, 0),
('Fireball', 'Area attack that hits multiple enemies', 'active', 'mage', 'D', 1.8, 35, 2),
('Arcane Mastery', 'All spells cost 50% less mana', 'passive', 'mage', 'B', 0.0, 0, 0),

-- Archer Abilities
('Precise Shot', 'High accuracy attack with critical chance', 'active', 'archer', 'E', 1.3, 12, 1),
('Eagle Eye', 'Increases accuracy and range for 5 turns', 'active', 'archer', 'E', 0.0, 15, 4),
('Multi-Shot', 'Attacks up to 3 enemies simultaneously', 'active', 'archer', 'D', 0.9, 25, 3),
('Hunter''s Mark', 'Marks enemy, all attacks deal double damage', 'active', 'archer', 'C', 0.0, 20, 5),

-- Assassin Abilities
('Stealth Strike', 'Attack from stealth for massive damage', 'active', 'assassin', 'E', 2.5, 20, 3),
('Poison Blade', 'Attacks apply poison damage over time', 'passive', 'assassin', 'E', 1.1, 0, 0),
('Shadow Step', 'Teleport behind enemy, next attack always crits', 'active', 'assassin', 'D', 0.0, 30, 4),
('Assassination', 'Instant kill chance on critically wounded enemies', 'active', 'assassin', 'A', 3.0, 50, 6),

-- Beast Abilities
('Savage Bite', 'Ferocious attack that causes bleeding', 'active', 'beast', 'E', 1.4, 10, 2),
('Pack Mentality', 'Damage increases with more beast shadows present', 'passive', 'beast', 'E', 1.0, 0, 0),
('Howl', 'Intimidates enemies, reducing their attack for 3 turns', 'active', 'beast', 'D', 0.0, 20, 4),
('Apex Predator', 'Each kill increases damage by 25%', 'passive', 'beast', 'B', 0.0, 0, 0);

-- Sample room configurations for dungeon gates
UPDATE dungeon_gates SET room_configuration = 
'[
  {"room": 1, "type": "monster", "enemies": [{"name": "Math Goblin", "count": 2}], "treasure_chance": 0.3},
  {"room": 2, "type": "monster", "enemies": [{"name": "Formula Imp", "count": 1}], "treasure_chance": 0.2},
  {"room": 3, "type": "boss", "enemies": [{"name": "Algebra Knight", "count": 1}], "treasure_chance": 1.0}
]'::jsonb
WHERE name = 'Gate of Basic Mathematics';

UPDATE dungeon_gates SET room_configuration = 
'[
  {"room": 1, "type": "monster", "enemies": [{"name": "Reading Rat", "count": 3}], "treasure_chance": 0.2},
  {"room": 2, "type": "puzzle", "puzzle_type": "comprehension", "treasure_chance": 0.4},
  {"room": 3, "type": "boss", "enemies": [{"name": "Grammar Guardian", "count": 1}], "treasure_chance": 1.0}
]'::jsonb
WHERE name = 'Reading Comprehension Cavern';

-- Sample loot tables
UPDATE dungeon_monsters SET possible_drops = 
'[
  {"rarity": "common", "items": ["Health Potion", "Mana Potion", "Study Notes"]},
  {"rarity": "rare", "items": ["Power Crystal", "Wisdom Scroll", "Experience Boost"]},
  {"rarity": "epic", "items": ["Shadow Fragment", "Rare Equipment", "Skill Book"]},
  {"rarity": "legendary", "items": ["Monarch''s Blessing", "Ultimate Scroll", "Divine Equipment"]}
]'::jsonb
WHERE rank IN ('D', 'C', 'B', 'A');

-- Add some seasonal gates for events
INSERT INTO dungeon_gates (name, description, gate_type, difficulty_rank, recommended_level, is_seasonal, seasonal_start, seasonal_end, base_experience_reward, base_orb_reward, base_crystal_reward) VALUES
('Haunted Mathematics Manor', 'Spooky math problems lurk in every corner', 'normal', 'C', 8, TRUE, '2024-10-20', '2024-11-05', 300, 150, 8),
('Winter Wonderland of Science', 'Frozen experiments and crystallized knowledge', 'normal', 'B', 12, TRUE, '2024-12-15', '2025-01-15', 400, 200, 12),
('Spring Festival of Learning', 'Blooming knowledge and fresh perspectives', 'normal', 'A', 16, TRUE, '2024-03-20', '2024-04-20', 600, 300, 20);