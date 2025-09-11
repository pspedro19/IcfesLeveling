// Comprehensive routing index for all frontend pages
// This file serves as a central reference for all available routes

export const routes = {
  // Authentication & Onboarding
  login: '/login',
  signup: '/signup',
  onboarding: '/onboarding',
  onboardingMap: '/onboarding-map',
  
  // Main Dashboard
  home: '/',
  studentDashboard: '/student-dashboard',
  teacherDashboard: '/teacher-dashboard',
  
  // Diagnostic & Assessment
  diagnosticTest: '/diagnostic-test',
  diagnosticSimple: '/diagnostic-simple',
  diagnosticComplete: '/diagnostic-complete',
  backendDiagnostic: '/backend-diagnostic',
  workingDiagnostic: '/working-diagnostic',
  testDiagnostic: '/test-diagnostic',
  diagnosticResults: '/diagnostic-test/results',
  monthlyReassessment: '/monthly-reassessment',
  
  // Gaming Features
  dungeon: '/dungeon',
  bossBattles: '/boss-battles',
  multiplayerRaid: '/multiplayer-raid',
  battleReport: '/battle-report',
  achievements: '/achievements',
  leaderboards: '/leaderboards',
  inventory: '/inventory',
  store: '/store',
  
  // Social Features
  guilds: '/guilds',
  guildChat: '/guild-chat',
  mentors: '/mentors',
  
  // Study & Learning
  studyPlans: '/study-plans',
  studyPlanView: '/study-plan-view',
  adaptiveStudyPlan: '/adaptive-study-plan',
  unitQuiz: '/unit-quiz',
  icfesSelector: '/icfes-selector',
  
  // Analytics & Progress
  analytics: '/analytics',
  analyticsDashboard: '/analytics-dashboard',
  rankReevaluation: '/rank-reevaluation',
  
  // Premium & Pricing
  premium: '/premium',
  premiumSuccess: '/premium/success',
  premiumCancel: '/premium/cancel',
  pricing: '/pricing',
  
  // Media & Content
  videoPlayer: '/video-player',
  yamlRenderer: '/yaml-renderer',
  multimediaExam: '/multimedia-exam',
  
  // Demo & Testing Pages
  demo: '/demo',
  componentsDemo: '/components-demo',
  arDemo: '/ar-demo',
  hapticDemo: '/haptic-demo',
  mobileDemo: '/mobile-demo',
  performanceDemo: '/performance-demo',
  workersDemo: '/workers-demo',
  tutorialDemo: '/tutorial-demo',
  cacheDemo: '/cache-demo',
  accessibilityDemo: '/accessibility-demo',
  aiTipsDemo: '/ai-tips-demo',
  recommendationsDemo: '/recommendations-demo',
  
  // Test Pages
  test: '/test',
  testImages: '/test-images',
  testPortal: '/test-portal',
  testStyling: '/test-styling',
  testSubjects: '/test-subjects',
  testLogin: '/test-login',
  cssTest: '/css-test',
  
  // Utility Pages
  offline: '/offline',
  landing: '/landing',
  modeToggle: '/mode-toggle',
  portalSelector: '/portal-selector',
  pwaSettings: '/pwa-settings',
};

// Protected routes that require authentication
export const protectedRoutes = [
  routes.studentDashboard,
  routes.teacherDashboard,
  routes.diagnosticTest,
  routes.dungeon,
  routes.achievements,
  routes.leaderboards,
  routes.inventory,
  routes.guilds,
  routes.studyPlans,
  routes.analytics,
  routes.premium,
];

// Public routes accessible without authentication
export const publicRoutes = [
  routes.home,
  routes.login,
  routes.signup,
  routes.landing,
  routes.pricing,
];

// Admin-only routes
export const adminRoutes = [
  routes.analyticsDashboard,
  routes.teacherDashboard,
];

export default routes;