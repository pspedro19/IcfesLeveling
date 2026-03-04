/// Global animation configuration for test-mode bypass.
///
/// Set [infiniteAnimationsEnabled] to `false` in test setUp() to prevent
/// flutter_animate infinite repeat animations from creating pending timers
/// that break FakeAsync assertions.
class AnimationConfig {
  /// When false, widgets should pass `onPlay: null` instead of
  /// `onPlay: (c) => c.repeat(...)`, allowing the animation to run once
  /// and stop without spawning infinite Timer(Duration.zero) callbacks.
  static bool infiniteAnimationsEnabled = true;
}
