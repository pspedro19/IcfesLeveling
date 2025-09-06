-- Expanded Achievement System with 50+ Achievements
-- Solo Leveling Themed Achievements for ICFES

-- Additional Achievement Categories and Expanded System

-- Shadow Army Achievements (Solo Leveling Theme)
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Shadow Arise', 'Unlock your first shadow soldier', 'shadow_army', 'single', '/icons/achievements/shadow-arise.png', 'rare', 50, '{"shadows_unlocked": 1}'),
('Shadow General', 'Command 5 shadow soldiers', 'shadow_army', 'progressive', '/icons/achievements/shadow-general.png', 'epic', 100, '{"shadows_unlocked": 5}'),
('Shadow Monarch', 'Command 10 shadow soldiers', 'shadow_army', 'progressive', '/icons/achievements/shadow-monarch.png', 'legendary', 200, '{"shadows_unlocked": 10}'),
('Elite Shadow', 'Upgrade a shadow to elite rank', 'shadow_army', 'single', '/icons/achievements/elite-shadow.png', 'epic', 75, '{"elite_shadows": 1}'),
('Shadow Legion', 'Have 20 active shadow soldiers', 'shadow_army', 'milestone', '/icons/achievements/shadow-legion.png', 'legendary', 300, '{"shadows_unlocked": 20}');

-- Hunter Rank Progression (Solo Leveling Theme)
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('E-Rank Hunter', 'Start your hunter journey', 'hunter_rank', 'single', '/icons/achievements/e-rank.png', 'common', 10, '{"rank": "E"}'),
('D-Rank Hunter', 'Advance to D-Rank', 'hunter_rank', 'progressive', '/icons/achievements/d-rank.png', 'common', 25, '{"rank": "D"}'),
('C-Rank Hunter', 'Achieve C-Rank status', 'hunter_rank', 'progressive', '/icons/achievements/c-rank.png', 'rare', 50, '{"rank": "C"}'),
('B-Rank Hunter', 'Reach B-Rank level', 'hunter_rank', 'progressive', '/icons/achievements/b-rank.png', 'epic', 100, '{"rank": "B"}'),
('A-Rank Hunter', 'Attain A-Rank mastery', 'hunter_rank', 'progressive', '/icons/achievements/a-rank.png', 'epic', 200, '{"rank": "A"}'),
('S-Rank Hunter', 'Join the elite S-Rank hunters', 'hunter_rank', 'progressive', '/icons/achievements/s-rank.png', 'legendary', 400, '{"rank": "S"}'),
('National Level Hunter', 'Become a legendary hunter', 'hunter_rank', 'milestone', '/icons/achievements/national-hunter.png', 'legendary', 1000, '{"rank": "S+"}');

-- Gate and Dungeon Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Gate Opener', 'Enter your first dungeon gate', 'dungeon', 'single', '/icons/achievements/gate-opener.png', 'common', 20, '{"dungeons_entered": 1}'),
('Dungeon Explorer', 'Clear 5 different dungeons', 'dungeon', 'progressive', '/icons/achievements/dungeon-explorer.png', 'rare', 50, '{"dungeons_cleared": 5}'),
('Gate Closer', 'Successfully close 10 dungeon gates', 'dungeon', 'progressive', '/icons/achievements/gate-closer.png', 'epic', 100, '{"dungeons_cleared": 10}'),
('Raid Captain', 'Lead 3 successful dungeon raids', 'dungeon', 'single', '/icons/achievements/raid-captain.png', 'epic', 125, '{"raids_led": 3}'),
('Solo Dungeon Master', 'Clear a dungeon solo without taking damage', 'dungeon', 'single', '/icons/achievements/solo-master.png', 'legendary', 200, '{"perfect_solo_clear": true}'),
('Speed Clearer', 'Clear a dungeon in under 5 minutes', 'dungeon', 'single', '/icons/achievements/speed-clearer.png', 'rare', 75, '{"speed_clear": true}'),
('Red Gate Survivor', 'Survive a high-difficulty red gate', 'dungeon', 'single', '/icons/achievements/red-gate.png', 'legendary', 300, '{"red_gate_cleared": true}');

-- Boss Battle Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Boss Slayer', 'Defeat your first unit boss', 'boss_battle', 'single', '/icons/achievements/boss-slayer.png', 'rare', 50, '{"bosses_defeated": 1}'),
('Giant Killer', 'Defeat 5 unit bosses', 'boss_battle', 'progressive', '/icons/achievements/giant-killer.png', 'epic', 150, '{"bosses_defeated": 5}'),
('Monarch Slayer', 'Defeat all subject bosses', 'boss_battle', 'milestone', '/icons/achievements/monarch-slayer.png', 'legendary', 500, '{"all_subject_bosses": true}'),
('Perfect Victory', 'Defeat a boss without losing any HP', 'boss_battle', 'single', '/icons/achievements/perfect-victory.png', 'epic', 100, '{"perfect_boss_kill": true}'),
('Speed Demon', 'Defeat a boss in under 3 minutes', 'boss_battle', 'single', '/icons/achievements/speed-demon.png', 'rare', 75, '{"speed_boss_kill": true}'),
('Combo Master', 'Achieve a 50-hit combo in boss battle', 'boss_battle', 'single', '/icons/achievements/combo-master.png', 'epic', 125, '{"max_combo": 50}');

-- Study and Learning Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Knowledge Seeker', 'Watch 10 educational videos', 'learning', 'progressive', '/icons/achievements/knowledge-seeker.png', 'common', 25, '{"videos_watched": 10}'),
('Video Marathon', 'Watch 50 educational videos', 'learning', 'progressive', '/icons/achievements/video-marathon.png', 'rare', 75, '{"videos_watched": 50}'),
('Study Beast', 'Study for 100 total hours', 'learning', 'milestone', '/icons/achievements/study-beast.png', 'epic', 200, '{"study_hours": 100}'),
('Night Scholar', 'Study after midnight 5 times', 'learning', 'single', '/icons/achievements/night-scholar.png', 'rare', 50, '{"night_study_sessions": 5}'),
('Early Bird', 'Study before 6 AM for 7 days', 'learning', 'single', '/icons/achievements/early-bird.png', 'epic', 100, '{"early_study_streak": 7}'),
('Weekend Warrior', 'Study on 10 weekends', 'learning', 'progressive', '/icons/achievements/weekend-warrior.png', 'rare', 75, '{"weekend_study_days": 10}'),
('Subject Master', 'Achieve 90%+ average in all subjects', 'learning', 'milestone', '/icons/achievements/subject-master-all.png', 'legendary', 400, '{"all_subjects_mastery": true}');

-- Social and Guild Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Guild Founder', 'Create a new guild', 'social', 'single', '/icons/achievements/guild-founder.png', 'rare', 75, '{"guild_created": true}'),
('Loyal Member', 'Stay in the same guild for 30 days', 'social', 'single', '/icons/achievements/loyal-member.png', 'rare', 50, '{"guild_loyalty_days": 30}'),
('Social Butterfly', 'Help 10 guild members with questions', 'social', 'progressive', '/icons/achievements/social-butterfly.png', 'epic', 100, '{"members_helped": 10}'),
('Tournament Victor', 'Win a guild tournament', 'social', 'single', '/icons/achievements/tournament-victor.png', 'legendary', 200, '{"tournaments_won": 1}'),
('Champion of Champions', 'Win 5 guild tournaments', 'social', 'milestone', '/icons/achievements/champion-champions.png', 'legendary', 500, '{"tournaments_won": 5}'),
('Mentor', 'Help 5 new students improve their ranks', 'social', 'progressive', '/icons/achievements/mentor.png', 'epic', 150, '{"students_mentored": 5}');

-- Special Combat Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Critical Master', 'Land 100 critical hits', 'combat', 'progressive', '/icons/achievements/critical-master.png', 'rare', 75, '{"critical_hits": 100}'),
('Combo King', 'Achieve a 100-hit combo', 'combat', 'single', '/icons/achievements/combo-king.png', 'epic', 150, '{"max_combo": 100}'),
('Untouchable', 'Win 10 battles without taking damage', 'combat', 'progressive', '/icons/achievements/untouchable.png', 'legendary', 200, '{"perfect_battles": 10}'),
('Berserker', 'Win a battle with 1 HP remaining', 'combat', 'single', '/icons/achievements/berserker.png', 'epic', 100, '{"clutch_victory": true}'),
('Efficient Fighter', 'Win 20 battles in under 2 minutes each', 'combat', 'progressive', '/icons/achievements/efficient-fighter.png', 'rare', 100, '{"quick_battles": 20}'),
('Damage Dealer', 'Deal 10,000 total damage in battles', 'combat', 'milestone', '/icons/achievements/damage-dealer.png', 'epic', 125, '{"total_damage": 10000}');

-- Skill and Mastery Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Mathematics Prodigy', 'Score 95%+ on 10 math assessments', 'mastery', 'progressive', '/icons/achievements/math-prodigy.png', 'epic', 150, '{"math_high_scores": 10}'),
('Science Genius', 'Master all natural sciences topics', 'mastery', 'milestone', '/icons/achievements/science-genius.png', 'legendary', 300, '{"science_mastery": true}'),
('Language Master', 'Achieve perfect scores in reading comprehension', 'mastery', 'progressive', '/icons/achievements/language-master.png', 'epic', 150, '{"reading_perfect_scores": 5}'),
('Logic Lord', 'Solve 100 logic puzzles correctly', 'mastery', 'progressive', '/icons/achievements/logic-lord.png', 'rare', 100, '{"logic_puzzles": 100}'),
('Speed Solver', 'Answer 50 questions in under 30 seconds each', 'mastery', 'progressive', '/icons/achievements/speed-solver.png', 'epic', 125, '{"speed_answers": 50}'),
('Perfectionist Pro', 'Achieve 100% on 5 different assessments', 'mastery', 'progressive', '/icons/achievements/perfectionist-pro.png', 'legendary', 250, '{"perfect_assessments": 5}');

-- Discovery and Exploration Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements, is_secret) VALUES
('Secret Hunter', 'Find your first hidden achievement', 'secret', 'single', '/icons/achievements/secret-hunter.png', 'rare', 100, '{"hidden_found": 1}', TRUE),
('Easter Egg', 'Discover a hidden game feature', 'secret', 'single', '/icons/achievements/easter-egg.png', 'epic', 150, '{"hidden_feature": true}', TRUE),
('Code Breaker', 'Solve a hidden puzzle in the interface', 'secret', 'single', '/icons/achievements/code-breaker.png', 'legendary', 200, '{"puzzle_solved": true}', TRUE),
('Time Traveler', 'Study during every hour of the day', 'secret', 'single', '/icons/achievements/time-traveler.png', 'legendary', 300, '{"all_hours_studied": true}', TRUE),
('Phoenix', 'Come back from a 30-day study break', 'secret', 'single', '/icons/achievements/phoenix.png', 'epic', 150, '{"comeback_story": true}', TRUE);

-- Economic and Collection Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Wealthy Hunter', 'Accumulate 10,000 orbs', 'economy', 'milestone', '/icons/achievements/wealthy-hunter.png', 'rare', 75, '{"orbs_accumulated": 10000}'),
('Crystal Collector', 'Collect 1,000 crystals', 'economy', 'milestone', '/icons/achievements/crystal-collector.png', 'epic', 125, '{"crystals_accumulated": 1000}'),
('Shop Owner', 'Purchase 20 different items', 'economy', 'progressive', '/icons/achievements/shop-owner.png', 'rare', 100, '{"items_purchased": 20}'),
('Treasure Hunter', 'Find 50 rare item drops', 'economy', 'progressive', '/icons/achievements/treasure-hunter.png', 'epic', 150, '{"rare_drops_found": 50}'),
('Generous Soul', 'Give away 1,000 orbs to guild members', 'economy', 'single', '/icons/achievements/generous-soul.png', 'epic', 125, '{"orbs_donated": 1000}');

-- Time-based and Seasonal Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('New Year Scholar', 'Study on New Year\'s Day', 'seasonal', 'single', '/icons/achievements/new-year-scholar.png', 'rare', 100, '{"new_year_study": true}'),
('Valentine Learner', 'Study with a friend on Valentine\'s Day', 'seasonal', 'single', '/icons/achievements/valentine-learner.png', 'rare', 75, '{"valentine_study": true}'),
('Halloween Hunter', 'Complete special Halloween challenges', 'seasonal', 'single', '/icons/achievements/halloween-hunter.png', 'epic', 150, '{"halloween_event": true}'),
('Christmas Champion', 'Participate in Christmas learning event', 'seasonal', 'single', '/icons/achievements/christmas-champion.png', 'epic', 150, '{"christmas_event": true}'),
('Birthday Boss', 'Study on your birthday', 'seasonal', 'single', '/icons/achievements/birthday-boss.png', 'rare', 100, '{"birthday_study": true}');

-- Create indexes for the new achievement categories
CREATE INDEX idx_achievements_shadow_army ON achievements(category) WHERE category = 'shadow_army';
CREATE INDEX idx_achievements_hunter_rank ON achievements(category) WHERE category = 'hunter_rank';
CREATE INDEX idx_achievements_dungeon ON achievements(category) WHERE category = 'dungeon';
CREATE INDEX idx_achievements_boss_battle ON achievements(category) WHERE category = 'boss_battle';
CREATE INDEX idx_achievements_learning ON achievements(category) WHERE category = 'learning';
CREATE INDEX idx_achievements_social ON achievements(category) WHERE category = 'social';
CREATE INDEX idx_achievements_combat ON achievements(category) WHERE category = 'combat';
CREATE INDEX idx_achievements_mastery ON achievements(category) WHERE category = 'mastery';
CREATE INDEX idx_achievements_economy ON achievements(category) WHERE category = 'economy';
CREATE INDEX idx_achievements_seasonal ON achievements(category) WHERE category = 'seasonal';