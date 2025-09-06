-- Complete Gamification System Database Schema
-- Solo Leveling Themed ICFES Platform

-- Shadow Army System Tables
CREATE TABLE IF NOT EXISTS shadow_soldiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    shadow_type VARCHAR(50) NOT NULL, -- 'knight', 'mage', 'archer', 'assassin', 'beast'
    rank VARCHAR(10) DEFAULT 'E', -- E, D, C, B, A, S, SS
    level INTEGER DEFAULT 1,
    experience INTEGER DEFAULT 0,
    
    -- Combat Stats
    attack_power INTEGER DEFAULT 10,
    defense INTEGER DEFAULT 5,
    magic_power INTEGER DEFAULT 5,
    speed INTEGER DEFAULT 10,
    health INTEGER DEFAULT 100,
    mana INTEGER DEFAULT 50,
    
    -- Shadow Properties
    loyalty INTEGER DEFAULT 100,
    extraction_source VARCHAR(200),
    special_abilities JSONB DEFAULT '[]',
    equipment JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_summoned BOOLEAN DEFAULT FALSE,
    last_battle TIMESTAMP WITH TIME ZONE,
    battles_won INTEGER DEFAULT 0,
    battles_lost INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shadow_formations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    formation_type VARCHAR(50) NOT NULL, -- 'attack', 'defense', 'balanced', 'speed'
    shadow_positions JSONB NOT NULL,
    formation_bonuses JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shadow_battles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    battle_id UUID NOT NULL REFERENCES battles(id) ON DELETE CASCADE,
    shadow_soldier_id UUID NOT NULL REFERENCES shadow_soldiers(id) ON DELETE CASCADE,
    
    -- Battle Performance
    damage_dealt INTEGER DEFAULT 0,
    damage_taken INTEGER DEFAULT 0,
    abilities_used JSONB DEFAULT '[]',
    kills INTEGER DEFAULT 0,
    experience_gained INTEGER DEFAULT 0,
    
    -- Battle Status
    was_summoned BOOLEAN DEFAULT FALSE,
    survived_battle BOOLEAN DEFAULT TRUE,
    performed_special_action BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shadow_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_enemy VARCHAR(200) NOT NULL,
    source_battle_id UUID REFERENCES battles(id) ON DELETE SET NULL,
    extraction_success BOOLEAN DEFAULT FALSE,
    shadow_soldier_id UUID REFERENCES shadow_soldiers(id) ON DELETE SET NULL,
    
    -- Extraction Conditions
    enemy_level INTEGER NOT NULL,
    user_level_at_extraction INTEGER NOT NULL,
    extraction_chance DECIMAL(5,2) NOT NULL,
    
    -- Extraction Results
    extraction_power_used INTEGER DEFAULT 0,
    extraction_attempt_count INTEGER DEFAULT 1,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shadow_abilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    ability_type VARCHAR(50) NOT NULL, -- 'active', 'passive', 'ultimate'
    shadow_type_requirement VARCHAR(50),
    rank_requirement VARCHAR(10) DEFAULT 'E',
    
    -- Ability Effects
    damage_multiplier DECIMAL(5,2) DEFAULT 1.0,
    healing_amount INTEGER DEFAULT 0,
    buff_effects JSONB DEFAULT '{}',
    debuff_effects JSONB DEFAULT '{}',
    
    -- Resource Costs
    mana_cost INTEGER DEFAULT 10,
    cooldown_turns INTEGER DEFAULT 1,
    
    -- Availability
    is_learnable BOOLEAN DEFAULT TRUE,
    is_unique BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_shadow_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    
    -- Shadow Monarch Stats
    monarch_level INTEGER DEFAULT 1,
    monarch_experience INTEGER DEFAULT 0,
    shadow_capacity INTEGER DEFAULT 5,
    extraction_power INTEGER DEFAULT 100,
    
    -- Shadow Army Stats
    total_shadows_extracted INTEGER DEFAULT 0,
    active_shadows INTEGER DEFAULT 0,
    highest_rank_shadow VARCHAR(10) DEFAULT 'E',
    total_shadow_battles INTEGER DEFAULT 0,
    total_shadow_victories INTEGER DEFAULT 0,
    
    -- Special Abilities
    monarch_abilities JSONB DEFAULT '[]',
    can_command_multiple BOOLEAN DEFAULT FALSE,
    can_shadow_exchange BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dungeon System Tables
CREATE TABLE IF NOT EXISTS dungeon_gates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    gate_type VARCHAR(50) NOT NULL, -- 'normal', 'red', 'boss', 'instant'
    difficulty_rank VARCHAR(10) NOT NULL, -- E, D, C, B, A, S
    
    -- Gate Properties
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    topic_focus VARCHAR(200),
    recommended_level INTEGER DEFAULT 1,
    max_participants INTEGER DEFAULT 1,
    
    -- Dungeon Layout
    total_rooms INTEGER DEFAULT 5,
    boss_room INTEGER DEFAULT 5,
    room_configuration JSONB DEFAULT '{}',
    
    -- Gate Mechanics
    time_limit_minutes INTEGER DEFAULT 60,
    entry_cost_orbs INTEGER DEFAULT 0,
    entry_cost_crystals INTEGER DEFAULT 0,
    min_rank_requirement VARCHAR(10) DEFAULT 'E',
    
    -- Rewards
    base_experience_reward INTEGER DEFAULT 100,
    base_orb_reward INTEGER DEFAULT 50,
    base_crystal_reward INTEGER DEFAULT 0,
    possible_item_drops JSONB DEFAULT '[]',
    boss_guaranteed_drops JSONB DEFAULT '[]',
    
    -- Gate Status
    is_active BOOLEAN DEFAULT TRUE,
    is_raid_gate BOOLEAN DEFAULT FALSE,
    is_seasonal BOOLEAN DEFAULT FALSE,
    seasonal_start TIMESTAMP WITH TIME ZONE,
    seasonal_end TIMESTAMP WITH TIME ZONE,
    
    -- Statistics
    times_entered INTEGER DEFAULT 0,
    times_completed INTEGER DEFAULT 0,
    average_completion_time INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dungeon_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gate_id UUID NOT NULL REFERENCES dungeon_gates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Run Status
    status VARCHAR(20) DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed', 'abandoned'
    current_room INTEGER DEFAULT 1,
    
    -- Performance Tracking
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completion_time TIMESTAMP WITH TIME ZONE,
    total_time_seconds INTEGER,
    
    -- Combat Stats
    monsters_defeated INTEGER DEFAULT 0,
    boss_defeated BOOLEAN DEFAULT FALSE,
    total_damage_dealt INTEGER DEFAULT 0,
    total_damage_taken INTEGER DEFAULT 0,
    questions_answered INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    
    -- Resources Used
    hp_potions_used INTEGER DEFAULT 0,
    mp_potions_used INTEGER DEFAULT 0,
    power_ups_used JSONB DEFAULT '[]',
    shadows_summoned INTEGER DEFAULT 0,
    
    -- Rewards Earned
    experience_gained INTEGER DEFAULT 0,
    orbs_gained INTEGER DEFAULT 0,
    crystals_gained INTEGER DEFAULT 0,
    items_dropped JSONB DEFAULT '[]',
    
    -- Special Achievements
    perfect_clear BOOLEAN DEFAULT FALSE,
    speed_clear BOOLEAN DEFAULT FALSE,
    no_items_used BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dungeon_encounters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dungeon_run_id UUID NOT NULL REFERENCES dungeon_runs(id) ON DELETE CASCADE,
    room_number INTEGER NOT NULL,
    
    -- Encounter Type
    encounter_type VARCHAR(50) NOT NULL, -- 'monster', 'boss', 'treasure', 'puzzle'
    enemy_name VARCHAR(200),
    enemy_level INTEGER,
    enemy_type VARCHAR(50),
    
    -- Combat Details
    questions_faced JSONB DEFAULT '[]',
    answers_given JSONB DEFAULT '[]',
    combat_rounds INTEGER DEFAULT 1,
    
    -- Results
    encounter_won BOOLEAN DEFAULT FALSE,
    damage_dealt INTEGER DEFAULT 0,
    damage_taken INTEGER DEFAULT 0,
    experience_gained INTEGER DEFAULT 0,
    
    -- Rewards
    items_dropped JSONB DEFAULT '[]',
    orbs_gained INTEGER DEFAULT 0,
    special_effects JSONB DEFAULT '[]',
    
    -- Shadow Army Interaction
    shadows_used JSONB DEFAULT '[]',
    shadow_extraction_attempted BOOLEAN DEFAULT FALSE,
    shadow_extraction_successful BOOLEAN DEFAULT FALSE,
    
    encounter_time TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dungeon_monsters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    monster_type VARCHAR(50) NOT NULL, -- 'beast', 'undead', 'elemental', 'humanoid'
    rank VARCHAR(10) NOT NULL, -- E, D, C, B, A, S
    
    -- Combat Stats
    level INTEGER DEFAULT 1,
    health INTEGER DEFAULT 100,
    attack INTEGER DEFAULT 10,
    defense INTEGER DEFAULT 5,
    magic_power INTEGER DEFAULT 5,
    speed INTEGER DEFAULT 10,
    
    -- Monster Abilities
    special_abilities JSONB DEFAULT '[]',
    resistances JSONB DEFAULT '[]',
    weaknesses JSONB DEFAULT '[]',
    
    -- Question Generation
    preferred_subjects JSONB DEFAULT '[]',
    question_difficulty VARCHAR(20) DEFAULT 'medium',
    questions_per_encounter INTEGER DEFAULT 3,
    
    -- Loot Table
    drop_rate_common DECIMAL(5,2) DEFAULT 70.0,
    drop_rate_rare DECIMAL(5,2) DEFAULT 20.0,
    drop_rate_epic DECIMAL(5,2) DEFAULT 8.0,
    drop_rate_legendary DECIMAL(5,2) DEFAULT 2.0,
    
    possible_drops JSONB DEFAULT '[]',
    orb_drop_min INTEGER DEFAULT 5,
    orb_drop_max INTEGER DEFAULT 15,
    
    -- Shadow Extraction
    can_be_extracted BOOLEAN DEFAULT TRUE,
    extraction_difficulty DECIMAL(5,2) DEFAULT 30.0,
    shadow_type VARCHAR(50),
    
    -- Monster Behavior
    aggression_level INTEGER DEFAULT 5,
    intelligence INTEGER DEFAULT 5,
    pack_behavior BOOLEAN DEFAULT FALSE,
    
    is_boss BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raid_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dungeon_run_id UUID NOT NULL REFERENCES dungeon_runs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'damage_dealer', -- 'tank', 'healer', 'damage_dealer', 'support'
    
    -- Participation Stats
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    left_at TIMESTAMP WITH TIME ZONE,
    is_leader BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Performance
    damage_dealt INTEGER DEFAULT 0,
    damage_taken INTEGER DEFAULT 0,
    healing_done INTEGER DEFAULT 0,
    questions_answered INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    
    -- Contribution
    contribution_score INTEGER DEFAULT 0,
    mvp_votes INTEGER DEFAULT 0,
    
    -- Rewards
    individual_rewards JSONB DEFAULT '{}'
);

-- Enhanced Quest System Tables
CREATE TABLE IF NOT EXISTS quest_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    quest_type VARCHAR(50) NOT NULL, -- 'daily', 'weekly', 'monthly', 'seasonal', 'special'
    category VARCHAR(50) NOT NULL, -- 'study', 'battle', 'social', 'exploration', 'achievement'
    
    -- Quest Parameters
    target_type VARCHAR(50) NOT NULL,
    target_value INTEGER NOT NULL,
    target_conditions JSONB DEFAULT '{}',
    
    -- Requirements
    min_level INTEGER DEFAULT 1,
    min_rank VARCHAR(10) DEFAULT 'E',
    required_subjects JSONB DEFAULT '[]',
    required_achievements JSONB DEFAULT '[]',
    
    -- Rewards
    base_experience INTEGER DEFAULT 50,
    base_orbs INTEGER DEFAULT 25,
    base_crystals INTEGER DEFAULT 0,
    special_rewards JSONB DEFAULT '[]',
    
    -- Quest Properties
    difficulty VARCHAR(20) DEFAULT 'normal', -- 'easy', 'normal', 'hard', 'extreme'
    rarity VARCHAR(20) DEFAULT 'common', -- 'common', 'rare', 'epic', 'legendary'
    is_repeatable BOOLEAN DEFAULT TRUE,
    max_completions INTEGER DEFAULT -1, -- -1 for unlimited
    
    -- Availability
    is_active BOOLEAN DEFAULT TRUE,
    season_requirement VARCHAR(50),
    event_requirement VARCHAR(50),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Update existing user_quests table to reference quest_templates
ALTER TABLE user_quests ADD COLUMN IF NOT EXISTS quest_template_id UUID REFERENCES quest_templates(id) ON DELETE CASCADE;
ALTER TABLE user_quests ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE user_quests ADD COLUMN IF NOT EXISTS progress_data JSONB DEFAULT '{}';
ALTER TABLE user_quests ADD COLUMN IF NOT EXISTS completion_quality DECIMAL(3,2) DEFAULT 1.0;
ALTER TABLE user_quests ADD COLUMN IF NOT EXISTS rewards_claimed BOOLEAN DEFAULT FALSE;
ALTER TABLE user_quests ADD COLUMN IF NOT EXISTS experience_earned INTEGER DEFAULT 0;
ALTER TABLE user_quests ADD COLUMN IF NOT EXISTS orbs_earned INTEGER DEFAULT 0;
ALTER TABLE user_quests ADD COLUMN IF NOT EXISTS crystals_earned INTEGER DEFAULT 0;
ALTER TABLE user_quests ADD COLUMN IF NOT EXISTS special_rewards_earned JSONB DEFAULT '[]';

CREATE TABLE IF NOT EXISTS quest_chains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    chain_type VARCHAR(50) NOT NULL, -- 'storyline', 'mastery', 'seasonal'
    
    -- Chain Properties
    total_quests INTEGER DEFAULT 1,
    quest_order JSONB NOT NULL,
    unlock_conditions JSONB DEFAULT '{}',
    
    -- Rewards
    completion_rewards JSONB DEFAULT '{}',
    chain_title VARCHAR(100),
    chain_achievement_id UUID REFERENCES achievements(id) ON DELETE SET NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_seasonal BOOLEAN DEFAULT FALSE,
    season_start TIMESTAMP WITH TIME ZONE,
    season_end TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_quest_chains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quest_chain_id UUID NOT NULL REFERENCES quest_chains(id) ON DELETE CASCADE,
    
    -- Progress
    current_quest_index INTEGER DEFAULT 0,
    quests_completed INTEGER DEFAULT 0,
    chain_completed BOOLEAN DEFAULT FALSE,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS special_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    event_type VARCHAR(50) NOT NULL, -- 'seasonal', 'limited', 'holiday', 'anniversary'
    
    -- Event Timing
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Event Properties
    special_rewards JSONB DEFAULT '{}',
    event_quests JSONB DEFAULT '[]',
    event_dungeons JSONB DEFAULT '[]',
    
    -- Event Mechanics
    point_system JSONB DEFAULT '{}',
    leaderboard_enabled BOOLEAN DEFAULT FALSE,
    participation_requirements JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_event_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES special_events(id) ON DELETE CASCADE,
    
    -- Progress
    event_points INTEGER DEFAULT 0,
    quests_completed INTEGER DEFAULT 0,
    special_objectives JSONB DEFAULT '{}',
    
    -- Rewards
    rewards_claimed JSONB DEFAULT '[]',
    final_reward_claimed BOOLEAN DEFAULT FALSE,
    
    -- Rankings
    leaderboard_rank INTEGER,
    
    -- Timing
    first_participation TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_shadow_soldiers_user_id ON shadow_soldiers(user_id);
CREATE INDEX idx_shadow_soldiers_type_rank ON shadow_soldiers(shadow_type, rank);
CREATE INDEX idx_shadow_battles_user_id ON shadow_battles(user_id);
CREATE INDEX idx_shadow_battles_battle_id ON shadow_battles(battle_id);
CREATE INDEX idx_shadow_extractions_user_id ON shadow_extractions(user_id);
CREATE INDEX idx_shadow_extractions_success ON shadow_extractions(extraction_success);

CREATE INDEX idx_dungeon_gates_type_rank ON dungeon_gates(gate_type, difficulty_rank);
CREATE INDEX idx_dungeon_gates_subject ON dungeon_gates(subject_id);
CREATE INDEX idx_dungeon_runs_user_id ON dungeon_runs(user_id);
CREATE INDEX idx_dungeon_runs_gate_id ON dungeon_runs(gate_id);
CREATE INDEX idx_dungeon_runs_status ON dungeon_runs(status);
CREATE INDEX idx_dungeon_encounters_run_id ON dungeon_encounters(dungeon_run_id);
CREATE INDEX idx_dungeon_monsters_type_rank ON dungeon_monsters(monster_type, rank);

CREATE INDEX idx_quest_templates_type_category ON quest_templates(quest_type, category);
CREATE INDEX idx_quest_templates_active ON quest_templates(is_active);
CREATE INDEX idx_user_quests_template_id ON user_quests(quest_template_id);
CREATE INDEX idx_user_quests_status ON user_quests(status);
CREATE INDEX idx_user_quest_chains_user_id ON user_quest_chains(user_id);
CREATE INDEX idx_special_events_active ON special_events(is_active);
CREATE INDEX idx_user_event_progress_user_id ON user_event_progress(user_id);
CREATE INDEX idx_user_event_progress_event_id ON user_event_progress(event_id);