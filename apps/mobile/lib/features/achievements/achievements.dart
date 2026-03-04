/// Achievements Feature Module
/// Provides achievement/badge system for gamification

// Models
export 'data/models/achievement_model.dart';

// Datasources
export 'data/datasources/achievements_remote_datasource.dart';

// Repositories
export 'domain/repositories/achievements_repository.dart';
export 'data/repositories/achievements_repository_impl.dart';

// Providers
export 'presentation/providers/achievements_provider.dart';

// Pages
export 'presentation/pages/achievements_page.dart';

// Widgets
export 'presentation/widgets/achievement_badge.dart';
export 'presentation/widgets/achievement_detail_modal.dart';
export 'presentation/widgets/achievement_unlock_animation.dart';
