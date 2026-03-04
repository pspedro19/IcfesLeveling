import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

/// Singleton service for Google AdMob rewarded ads.
///
/// Used for:
/// - Heart refill (watch ad → +1 heart)
/// - Streak repair (watch ad → restore streak)
///
/// Test Ad Unit IDs are used by default.
/// Replace with real Ad Unit IDs before production release.
class AdMobService {
  static final AdMobService _instance = AdMobService._internal();
  factory AdMobService() => _instance;
  AdMobService._internal();

  bool _isInitialized = false;
  RewardedAd? _rewardedAd;
  bool _isAdLoading = false;

  /// Test Ad Unit IDs (Google-provided, safe for development)
  static const String _testRewardedAdUnitIdAndroid =
      'ca-app-pub-3940256099942544/5224354917';
  static const String _testRewardedAdUnitIdIos =
      'ca-app-pub-3940256099942544/1712485313';

  /// Production Ad Unit IDs — set via environment or override before release
  static String? productionRewardedAdUnitIdAndroid;
  static String? productionRewardedAdUnitIdIos;

  String get _rewardedAdUnitId {
    if (defaultTargetPlatform == TargetPlatform.android) {
      return productionRewardedAdUnitIdAndroid ?? _testRewardedAdUnitIdAndroid;
    } else {
      return productionRewardedAdUnitIdIos ?? _testRewardedAdUnitIdIos;
    }
  }

  /// Initialize the Mobile Ads SDK. Call once at app startup.
  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      await MobileAds.instance.initialize();
      _isInitialized = true;
      debugPrint('AdMobService: initialized');
      _preloadRewardedAd();
    } catch (e) {
      debugPrint('AdMobService: init failed — $e');
    }
  }

  /// Pre-load a rewarded ad so it's ready when the user needs it.
  void _preloadRewardedAd() {
    if (_rewardedAd != null || _isAdLoading) return;
    _isAdLoading = true;

    RewardedAd.load(
      adUnitId: _rewardedAdUnitId,
      request: const AdRequest(),
      rewardedAdLoadCallback: RewardedAdLoadCallback(
        onAdLoaded: (ad) {
          _rewardedAd = ad;
          _isAdLoading = false;
          debugPrint('AdMobService: rewarded ad loaded');
        },
        onAdFailedToLoad: (error) {
          _rewardedAd = null;
          _isAdLoading = false;
          debugPrint('AdMobService: failed to load — ${error.message}');
        },
      ),
    );
  }

  /// Whether a rewarded ad is ready to show.
  bool get isRewardedAdReady => _rewardedAd != null;

  /// Show a rewarded ad. Returns `true` if the user earned the reward.
  ///
  /// [onRewarded] is called when the user completes watching the ad.
  /// After showing (success or failure), a new ad is pre-loaded automatically.
  Future<bool> showRewardedAd() async {
    if (!_isInitialized) {
      debugPrint('AdMobService: not initialized');
      return false;
    }

    if (_rewardedAd == null) {
      debugPrint('AdMobService: no ad loaded, attempting reload');
      _preloadRewardedAd();
      return false;
    }

    final completer = _RewardCompleter();

    _rewardedAd!.fullScreenContentCallback = FullScreenContentCallback(
      onAdDismissedFullScreenContent: (ad) {
        ad.dispose();
        _rewardedAd = null;
        _preloadRewardedAd(); // Pre-load next ad
        completer.complete();
      },
      onAdFailedToShowFullScreenContent: (ad, error) {
        debugPrint('AdMobService: show failed — ${error.message}');
        ad.dispose();
        _rewardedAd = null;
        _preloadRewardedAd();
        completer.completeWithError();
      },
    );

    _rewardedAd!.show(
      onUserEarnedReward: (ad, reward) {
        debugPrint('AdMobService: reward earned — ${reward.amount} ${reward.type}');
        completer.markRewarded();
      },
    );

    return completer.future;
  }
}

/// Internal helper to track reward completion across callbacks.
class _RewardCompleter {
  bool _rewarded = false;
  final Completer<bool> _completer = Completer<bool>();

  Future<bool> get future => _completer.future;

  void markRewarded() {
    _rewarded = true;
  }

  void complete() {
    if (!_completer.isCompleted) {
      _completer.complete(_rewarded);
    }
  }

  void completeWithError() {
    if (!_completer.isCompleted) {
      _completer.complete(false);
    }
  }
}
