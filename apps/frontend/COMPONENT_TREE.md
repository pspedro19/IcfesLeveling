# COMPONENT TREE - ICFES LEVELING FRONTEND

## Visual Architecture

```
apps/frontend/app/
├── layout.tsx (Root Layout)
│   ├── ParticleBackground (dynamic)
│   ├── MainNavigation (dynamic - COMMENTED OUT ⚠️)
│   ├── ErrorBoundary
│   ├── QueryProvider
│   ├── AnalyticsProvider
│   └── children (pages)
│
├── page.tsx (Home - minimal)
│
├── providers/
│   ├── QueryProvider.tsx
│   ├── AnalyticsProvider.tsx
│   └── HydrationProvider.tsx
│
├── lib/
│   ├── dynamic-config.ts (API URL detection)
│   ├── axios.ts (API client with interceptors)
│   ├── error-handler.ts
│   ├── error-handler.tsx
│   ├── analytics.ts
│   ├── mobile-utils.ts
│   └── utils.ts
│
├── hooks/
│   ├── useOptimizedDataLoader.tsx (any ⚠️)
│   ├── useRealtimeUpdates.ts (any ⚠️)
│   ├── useARSupport.tsx (any ⚠️)
│   ├── useHapticFeedback.tsx
│   ├── useGameSounds.ts (any ⚠️)
│   ├── useWorker.tsx (any ⚠️)
│   ├── useCache.ts
│   ├── useRealTimeData.tsx
│   ├── useProgressSync.tsx
│   ├── useTextToSpeech.tsx
│   ├── useServiceWorker.tsx
│   ├── useWebSocket.tsx
│   ├── useMediaQuery.tsx
│   ├── useQueries.tsx
│   ├── usePerformanceOptimization.tsx
│   ├── useMobileGestures.tsx
│   ├── useHybridUX.tsx
│   └── useErrorRecovery.tsx
│
├── components/ (137 total)
│   │
│   ├── Navigation/
│   │   └── MainNavigation.tsx (Level-based unlock system)
│   │
│   ├── AI/
│   │   ├── AIBattleTips.tsx
│   │   └── AIExplanation.tsx
│   │
│   ├── AITrainingZone/
│   │   ├── AIProgressDashboard.tsx
│   │   ├── AITutor.tsx
│   │   └── IntelligentTrainingZone.tsx
│   │
│   ├── Analytics/
│   │   ├── AnalyticsDashboard.tsx
│   │   ├── ComprehensiveAnalyticsDashboard.tsx
│   │   ├── EducationalInsightsEngine.tsx
│   │   ├── InteractiveCharts.tsx
│   │   ├── RealTimeAnalytics.tsx
│   │   ├── StudentProgressAnalytics.tsx
│   │   └── TeacherDashboard.tsx
│   │
│   ├── BattleSystem/
│   │   ├── BattleReport.tsx
│   │   ├── ComboChain.tsx
│   │   ├── DamageNumbers.tsx
│   │   └── __tests__/BattleReport.test.tsx (Only test!)
│   │
│   ├── Mobile/
│   │   ├── MobileButton.tsx
│   │   ├── MobileCard.tsx
│   │   ├── MobileCarousel.tsx
│   │   ├── MobileContainer.tsx
│   │   ├── MobileGrid.tsx
│   │   ├── MobileNavigation.tsx
│   │   └── MobileNavigationEnhanced.tsx
│   │
│   ├── PortalLogin/
│   │   ├── LoginPortal.tsx
│   │   ├── BlenderPortal.tsx
│   │   ├── BlenderPortalWrapper.tsx
│   │   ├── PortalAnimation.tsx
│   │   ├── PortalFallback.tsx
│   │   └── AudioEngine.tsx
│   │
│   ├── StudyPlan/
│   │   ├── CourseraGradeStudyPlan.tsx
│   │   ├── StudyPlanRouter.tsx
│   │   ├── PersonalizedYMLRenderer.tsx
│   │   ├── HybridStudyPlanUX.tsx
│   │   └── YouTubeVideoRenderer.tsx
│   │
│   ├── Student/
│   │   ├── AdvancedProgressChart.tsx
│   │   ├── ThetaEvolutionChart.tsx
│   │   ├── RecommendationsPanel.tsx
│   │   ├── RealtimeNotifications.tsx
│   │   ├── RealTimeMetricsPanel.tsx
│   │   ├── RPGProgressBar.tsx
│   │   ├── IRTMetricsPanel.tsx
│   │   ├── ErrorAnalysisCarousel.tsx
│   │   └── AnimatedBackground.tsx
│   │
│   ├── Teacher/
│   │   ├── AdvancedClassAnalytics.tsx
│   │   ├── StudentWeaknessHeatmap.tsx
│   │   ├── StudentRiskAlerts.tsx
│   │   ├── ExportService.tsx
│   │   └── DistractorAnalysis.tsx
│   │
│   ├── Leaderboards/
│   │   └── RealtimeLeaderboard.tsx
│   │
│   ├── Inventory/
│   │   └── InventorySystem.tsx
│   │
│   ├── GuildChat/
│   │   └── GuildChat.tsx
│   │
│   ├── Raids/
│   │   └── MultiplayerRaid.tsx
│   │
│   ├── Premium/
│   │   └── PremiumCheckout.tsx
│   │
│   ├── GuestMode/
│   │   ├── GuestConversionModal.tsx
│   │   ├── GuestDashboard.tsx
│   │   ├── GuestLimitModal.tsx
│   │   └── GuestMiniQuiz.tsx
│   │
│   ├── Accessibility/
│   │   └── AccessibleContent.tsx
│   │
│   ├── AR/
│   │   ├── ARDungeonButton.tsx
│   │   └── DungeonARPreview.tsx
│   │
│   ├── PWA/
│   │   └── PushNotificationManager.tsx
│   │
│   ├── Mentors/
│   │   └── AIMentorSystem.tsx
│   │
│   ├── Performance/
│   │   └── PerformanceMonitor.tsx
│   │
│   ├── Recommendations/
│   │   └── AdaptiveRecommendations.tsx
│   │
│   ├── QuestionEditor/
│   │   └── QuestionEditor.tsx
│   │
│   ├── ErrorBoundary.tsx
│   ├── CelebrationModal.tsx
│   ├── AchievementIcon.tsx
│   ├── SkeletonLoader.tsx
│   ├── SoundManager.tsx
│   ├── ServiceWorkerRegistration.tsx
│   ├── DynamicSubjectIcon.tsx
│   ├── SubjectIcon.tsx (duplicate?)
│   ├── HeroAnimations.tsx
│   ├── HeroIcon.tsx
│   ├── ICFESVideoPlayer.tsx
│   ├── ICFESModularSelector.tsx
│   ├── ICFESCatalogViewer.tsx
│   ├── LearningPathVisualizer.tsx
│   ├── MultimediaQuestion.tsx
│   ├── QuestionNavigation.tsx
│   ├── OnboardingMap.tsx
│   ├── PortalAnimation.tsx
│   ├── AITutorAssistant.tsx
│   ├── MobileNavigation.tsx (duplicate?)
│   └── ... (90+ more components)
│
└── app routes (94 pages)/
    ├── page.tsx (Home - empty ⚠️)
    │
    ├── Gamification Portals:
    │   ├── hub-central/page.tsx ✅
    │   ├── portal-despertar/page.tsx
    │   ├── biblioteca-ancestral/page.tsx
    │   ├── arena-conocimiento/page.tsx
    │   ├── santuario-sabiduria/page.tsx
    │   ├── mazmorra-tiempo/page.tsx
    │   └── torre-monarcas/page.tsx
    │
    ├── Diagnostic System:
    │   ├── diagnostic-test/page.tsx ✅
    │   ├── diagnostic-test/test-flow.tsx
    │   ├── diagnostic-test/results/page.tsx
    │   ├── diagnostic-simple/page.tsx
    │   ├── diagnostic-complete/page.tsx
    │   └── working-diagnostic/page.tsx
    │
    ├── Training System:
    │   ├── training-zone/page.tsx
    │   ├── training-zone/analytics/page.tsx
    │   ├── training-session/[sessionId]/page.tsx
    │   ├── training-session/[sessionId]/results/page.tsx
    │   ├── enhanced-training-zone/page.tsx
    │   └── ai-training-zone/page.tsx ✅
    │
    ├── Study & Learning:
    │   ├── study-plan-view/page.tsx ✅
    │   ├── study-plans/page.tsx
    │   ├── claude-study-plan/page.tsx
    │   ├── recommendations/page.tsx
    │   └── simple-recommendations/page.tsx
    │
    ├── Dashboards:
    │   ├── student-dashboard/page.tsx
    │   ├── teacher-dashboard/page.tsx
    │   ├── analytics-dashboard/page.tsx
    │   ├── analytics/page.tsx
    │   └── progress-dashboard/page.tsx
    │
    ├── Gamification:
    │   ├── leaderboards/page.tsx
    │   ├── inventory/page.tsx
    │   ├── guilds/page.tsx
    │   ├── guild-chat/page.tsx
    │   ├── boss-battles/page.tsx
    │   ├── achievements/page.tsx
    │   ├── rank-reevaluation/page.tsx
    │   ├── monthly-reassessment/page.tsx
    │   └── multiplayer-raid/page.tsx
    │
    ├── Auth:
    │   ├── login/page.tsx ✅
    │   ├── signup/page.tsx
    │   ├── portal-login/page.tsx
    │   └── portal-selector/page.tsx
    │
    ├── Premium:
    │   ├── premium/page.tsx
    │   ├── premium/success/page.tsx
    │   ├── premium/cancel/page.tsx
    │   ├── pricing/page.tsx
    │   └── store/page.tsx
    │
    ├── Onboarding:
    │   ├── onboarding/page.tsx
    │   └── onboarding-map/page.tsx
    │
    ├── Tools:
    │   ├── video-player/page.tsx
    │   ├── multimedia-exam/page.tsx
    │   ├── mentors/page.tsx
    │   ├── unit-quiz/page.tsx
    │   ├── admin-dashboard/page.tsx
    │   └── system-status/page.tsx
    │
    ├── Testing (50+ pages):
    │   ├── test-login/page.tsx
    │   ├── test-portal/page.tsx
    │   ├── test-diagnostic/page.tsx
    │   ├── test-question-types/page.tsx
    │   ├── test-images/page.tsx
    │   ├── test-image-performance/page.tsx
    │   ├── test-multimedia-comprehensive/page.tsx
    │   ├── test-subjects/page.tsx
    │   ├── test-styling/page.tsx
    │   ├── mobile-test-comprehensive/page.tsx
    │   ├── mobile-diagnostic/page.tsx
    │   ├── responsive-test/page.tsx
    │   ├── css-test/page.tsx
    │   ├── demo/page.tsx
    │   ├── test/page.tsx
    │   └── ... (35+ more test pages)
    │
    └── Special:
        ├── offline/page.tsx
        ├── pwa-settings/page.tsx
        ├── landing/page.tsx
        └── mode-toggle/page.tsx
```

## Dependency Graph

```
layout.tsx
├── ErrorBoundary
│   └── Catch component errors
│
├── QueryProvider
│   └── React Query (caching, retries)
│
├── AnalyticsProvider
│   └── Track user events
│
├── ParticleBackground (dynamic)
│   └── Visual effects
│
└── MainNavigation (COMMENTED OUT ⚠️)
    ├── useRouter
    ├── usePathname
    ├── Framer Motion
    ├── Lucide Icons
    └── localStorage access (212+ places)
```

## Data Flow

```
User Login → localStorage
    ↓
Hub Central → MainNavigation (needs user)
    ↓
Level/Rank Check → Unlock Areas
    ↓
Navigate to Portal → Load content
    ↓
API Call → buildApiUrl() → axios interceptors
    ↓
Response → React Query Cache
    ↓
Display → Components render
```

## API Integration

```
Frontend
├── lib/dynamic-config.ts
│   ├── getApiBaseUrl() → Auto-detect
│   └── getWebSocketUrl() → Auto-detect
│
├── lib/axios.ts
│   ├── Request interceptor → Add token
│   └── Response interceptor → Handle errors
│
└── React Query
    ├── Retry logic
    ├── Cache 10 min
    └── Stale time 5 min
```

## File Statistics

- Total TS/TSX files: 304
- Components: 137 (45%)
- Pages/Routes: 94 (31%)
- Hooks: 18 (6%)
- Utils/Lib: 10 (3%)
- Providers: 3 (1%)
- Other: 42 (14%)

## Status Summary

✅ Working:
- diagnostic-test
- hub-central
- ai-training-zone
- study-plan-view
- login

⚠️ Issues:
- MainNavigation (commented)
- 469 console logs
- 50+ any types
- No /profile
- No /settings

❌ Missing:
- Complete tests
- JSDoc documentation
- Error boundaries (full coverage)
- Global context
- Service worker (commented)

