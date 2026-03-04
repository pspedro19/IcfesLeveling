# Dopamine Engine

## Overview

The Dopamine Engine is a comprehensive feedback system designed to create satisfying, gamified interactions in the ICFES Leveling mobile app. It orchestrates visual animations, haptic feedback, and audio cues to reward users and create a compelling learning experience.

## Components

### 1. DopamineEngine (`dopamine_engine.dart`)

The main orchestrator that coordinates all feedback components.

**Key Methods:**
- `playCorrectAnswerSequence()` - 600ms sequence for correct answers
- `playIncorrectAnswerSequence()` - 800ms sequence for incorrect answers
- `playLessonCompleteSequence()` - 3000ms celebration for lesson completion

### 2. AppHaptics (`app_haptics.dart`)

Enhanced haptic feedback patterns.

**New Patterns:**
- `successPattern()` - Double pulse for correct answers
- `errorPattern()` - Heavy impact for wrong answers
- `celebrationPattern()` - Triple pulse for achievements
- `comboPattern(level)` - Escalating intensity based on combo
- `streakPattern()` - Special pattern for streak milestones
- `levelUpPattern()` - Big celebration for level ups
- `heartLostPattern()` - Negative feedback for heart loss
- `goldPattern()` - Coin-like feel for gold earned
- `xpTickPattern()` - Subtle tick for count-up animations
- `starPattern()` - Light impact for star appearance

### 3. SoundService (`sound_service.dart`)

Audio feedback management with preloading.

**Sound Types:**
- `ding` - Correct answer
- `wrong` - Incorrect answer
- `fanfare` - Lesson complete
- `tick` - XP count-up
- `levelUp` - Level up celebration
- `combo` - Combo milestone
- `coin` - Gold earned
- `click` - Button click
- `whoosh` - Transitions

### 4. Animated Feedback Widgets

Located in `lib/shared/widgets/animated_feedback/`:

#### CorrectAnswerOverlay
- Green glow expanding from center
- Bouncing checkmark icon
- Floating XP indicator
- Particle explosion for combos >= 3

#### IncorrectAnswerOverlay
- Red pulse background
- Shaking X mark (3 cycles, 5px amplitude)
- Heart crack animation
- Correct answer hint

#### LessonCompleteOverlay
- Dark fade overlay
- Confetti particle system
- Trophy icon with glow
- Bouncing title text
- Stars appearing one by one
- XP counter with count-up animation
- Gold earned indicator
- Continue button with shimmer

#### XPCounter
- Smooth count-up animation
- Optional tick sounds
- Haptic feedback at milestones
- Glow intensity based on progress

## Timeline Specifications

### Correct Answer (600ms)
```
0ms   - Green glow starts expanding
50ms  - Success haptic (double pulse)
100ms - "Ding" sound plays
150ms - Checkmark bounces in
300ms - "+XP" floats upward
400ms - Particles if combo >= 3
600ms - Sequence complete
```

### Incorrect Answer (800ms)
```
0ms   - Shake animation starts
50ms  - Heavy impact haptic
100ms - "Wrong" sound plays
200ms - X mark fades in
400ms - Heart "crack" animation
600ms - Correct answer illuminates
800ms - Sequence complete
```

### Lesson Complete (3000ms)
```
0ms    - Fade to dark overlay
200ms  - Confetti explosion starts
400ms  - Triple haptic pulse
500ms  - Title bounces in
600ms  - Fanfare sound
1000ms - XP counter starts
1500ms - Stars appear (500ms each)
2500ms - Gold counter appears
3000ms - Ready for interaction
```

## Integration

### In Practice Session Page

```dart
import '../../core/services/dopamine_engine.dart';

// Initialize in initState
DopamineEngine().initialize();

// Listen for answer checks
ref.listen<PracticeState>(practiceProvider, (previous, next) {
  if (previous != null && !previous.isAnswerChecked && next.isAnswerChecked) {
    _triggerDopamineFeedback(
      next.isCurrentCorrect,
      next.xpAwarded,
      next.comboCount,
    );
  }
});

// Add overlays to Stack
if (_showDopamineOverlay && _lastAnswerCorrect)
  CorrectAnswerOverlay(xpEarned: xpEarned, combo: combo),

if (_showDopamineOverlay && !_lastAnswerCorrect)
  IncorrectAnswerOverlay(correctAnswer: correctAnswer),
```

## Sound Assets Required

Place the following files in `assets/sounds/`:
- `ding.mp3` - Short, pleasant chime
- `wrong.mp3` - Brief error tone
- `fanfare.mp3` - Celebratory music (2-3 seconds)
- `tick.mp3` - Quick tick sound
- `levelup.mp3` - Level up jingle
- `combo.mp3` - Combo achievement sound
- `coin.mp3` - Coin/gold sound
- `click.mp3` - UI click
- `whoosh.mp3` - Transition swoosh

## Performance Considerations

1. **Sound Preloading**: Essential sounds (ding, wrong, tick) are preloaded on init
2. **Lazy Loading**: Less common sounds are loaded on first use
3. **Animation Efficiency**: Using flutter_animate for GPU-accelerated animations
4. **Memory Management**: Overlay widgets are removed after animations complete

## Accessibility

- Haptics can be disabled via `AppHaptics.setEnabled(false)`
- Sounds can be disabled via `SoundService().setEnabled(false)`
- Volume control via `SoundService().setVolume(0.0-1.0)`
- Visual feedback remains visible even when audio/haptics are off
