import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';
import '../../../../core/network/api_client.dart';

/// Onboarding preferences state (LOGICA_DE_NEGOCIO.md Steps 2-5)
class OnboardingPreferences {
  // Step 2: Goal Setting
  final StudyGoal? goal;
  final DateTime? examDate;

  // Step 3: Current Level
  final StudentLevel? currentLevel;

  // Step 4: Weak Subjects (1-3)
  final List<String> weakSubjects;

  // Step 5: Study Time
  final StudyTimeCommitment? dailyStudyTime;

  // Completion tracking
  final bool isComplete;

  const OnboardingPreferences({
    this.goal,
    this.examDate,
    this.currentLevel,
    this.weakSubjects = const [],
    this.dailyStudyTime,
    this.isComplete = false,
  });

  OnboardingPreferences copyWith({
    StudyGoal? goal,
    DateTime? examDate,
    StudentLevel? currentLevel,
    List<String>? weakSubjects,
    StudyTimeCommitment? dailyStudyTime,
    bool? isComplete,
  }) {
    return OnboardingPreferences(
      goal: goal ?? this.goal,
      examDate: examDate ?? this.examDate,
      currentLevel: currentLevel ?? this.currentLevel,
      weakSubjects: weakSubjects ?? this.weakSubjects,
      dailyStudyTime: dailyStudyTime ?? this.dailyStudyTime,
      isComplete: isComplete ?? this.isComplete,
    );
  }

  Map<String, dynamic> toJson() => {
    'goal': goal?.name,
    'exam_date': examDate?.toIso8601String(),
    'current_level': currentLevel?.name,
    'weak_subjects': weakSubjects,
    'daily_study_time': dailyStudyTime?.name,
    'is_complete': isComplete,
  };

  factory OnboardingPreferences.fromJson(Map<String, dynamic> json) {
    return OnboardingPreferences(
      goal: json['goal'] != null
          ? StudyGoal.values.firstWhere((e) => e.name == json['goal'], orElse: () => StudyGoal.mejorarIcfes)
          : null,
      examDate: json['exam_date'] != null ? DateTime.tryParse(json['exam_date']) : null,
      currentLevel: json['current_level'] != null
          ? StudentLevel.values.firstWhere((e) => e.name == json['current_level'], orElse: () => StudentLevel.basico)
          : null,
      weakSubjects: List<String>.from(json['weak_subjects'] ?? []),
      dailyStudyTime: json['daily_study_time'] != null
          ? StudyTimeCommitment.values.firstWhere((e) => e.name == json['daily_study_time'], orElse: () => StudyTimeCommitment.tenMinutes)
          : null,
      isComplete: json['is_complete'] ?? false,
    );
  }
}

/// Study goals (Step 2)
enum StudyGoal {
  mejorarIcfes,
  aprobarExamen,
  practicar,
}

extension StudyGoalExtension on StudyGoal {
  String get displayName {
    switch (this) {
      case StudyGoal.mejorarIcfes:
        return "Mejorar mi puntaje ICFES";
      case StudyGoal.aprobarExamen:
        return "Aprobar un examen especifico";
      case StudyGoal.practicar:
        return "Solo practicar y aprender";
    }
  }

  String get icon {
    switch (this) {
      case StudyGoal.mejorarIcfes:
        return "trending_up";
      case StudyGoal.aprobarExamen:
        return "school";
      case StudyGoal.practicar:
        return "fitness_center";
    }
  }
}

/// Student level (Step 3)
enum StudentLevel {
  basico,
  intermedio,
  avanzado,
}

extension StudentLevelExtension on StudentLevel {
  String get displayName {
    switch (this) {
      case StudentLevel.basico:
        return "Basico";
      case StudentLevel.intermedio:
        return "Intermedio";
      case StudentLevel.avanzado:
        return "Avanzado";
    }
  }

  String get description {
    switch (this) {
      case StudentLevel.basico:
        return "Estoy empezando o necesito repasar conceptos fundamentales";
      case StudentLevel.intermedio:
        return "Tengo conocimientos pero quiero mejorar en areas especificas";
      case StudentLevel.avanzado:
        return "Domino la mayoria de temas, busco perfeccionar detalles";
    }
  }

  double get initialMastery {
    switch (this) {
      case StudentLevel.basico:
        return 0.2;
      case StudentLevel.intermedio:
        return 0.5;
      case StudentLevel.avanzado:
        return 0.75;
    }
  }
}

/// Study time commitment (Step 5)
enum StudyTimeCommitment {
  tenMinutes,
  twentyMinutes,
  thirtyPlusMinutes,
}

extension StudyTimeCommitmentExtension on StudyTimeCommitment {
  String get displayName {
    switch (this) {
      case StudyTimeCommitment.tenMinutes:
        return "10 minutos";
      case StudyTimeCommitment.twentyMinutes:
        return "20 minutos";
      case StudyTimeCommitment.thirtyPlusMinutes:
        return "30+ minutos";
    }
  }

  int get minutes {
    switch (this) {
      case StudyTimeCommitment.tenMinutes:
        return 10;
      case StudyTimeCommitment.twentyMinutes:
        return 20;
      case StudyTimeCommitment.thirtyPlusMinutes:
        return 30;
    }
  }

  String get description {
    switch (this) {
      case StudyTimeCommitment.tenMinutes:
        return "Perfecto para dias ocupados";
      case StudyTimeCommitment.twentyMinutes:
        return "Balance ideal entre estudio y vida";
      case StudyTimeCommitment.thirtyPlusMinutes:
        return "Progreso acelerado para cazadores dedicados";
    }
  }
}

/// ICFES Subject options (Step 4)
class IcfesSubject {
  final String id;
  final String name;
  final String icon;
  final String color;

  const IcfesSubject({
    required this.id,
    required this.name,
    required this.icon,
    required this.color,
  });

  static const List<IcfesSubject> all = [
    IcfesSubject(id: 'matematicas', name: 'Matematicas', icon: 'calculate', color: '#4CAF50'),
    IcfesSubject(id: 'lectura_critica', name: 'Lectura Critica', icon: 'menu_book', color: '#2196F3'),
    IcfesSubject(id: 'ciencias_naturales', name: 'Ciencias Naturales', icon: 'science', color: '#9C27B0'),
    IcfesSubject(id: 'sociales_ciudadanas', name: 'Sociales y Ciudadanas', icon: 'public', color: '#FF9800'),
    IcfesSubject(id: 'ingles', name: 'Ingles', icon: 'language', color: '#E91E63'),
  ];
}


/// Onboarding Preferences Notifier
class OnboardingPreferencesNotifier extends StateNotifier<OnboardingPreferences> {
  final ApiClient _apiClient;
  static const _boxName = 'onboarding_preferences';

  OnboardingPreferencesNotifier(this._apiClient) : super(const OnboardingPreferences()) {
    _loadFromStorage();
  }

  /// Load preferences from local storage
  Future<void> _loadFromStorage() async {
    try {
      final box = await Hive.openBox(_boxName);
      final data = box.get('preferences');
      if (data != null) {
        state = OnboardingPreferences.fromJson(Map<String, dynamic>.from(data));
      }
    } catch (e) {
      // Ignore load errors
    }
  }

  /// Save preferences to local storage
  Future<void> _saveToStorage() async {
    try {
      final box = await Hive.openBox(_boxName);
      await box.put('preferences', state.toJson());
    } catch (e) {
      // Ignore save errors
    }
  }

  /// Step 2: Set study goal
  void setGoal(StudyGoal goal, {DateTime? examDate}) {
    state = state.copyWith(goal: goal, examDate: examDate);
    _saveToStorage();
  }

  /// Step 3: Set current level
  void setCurrentLevel(StudentLevel level) {
    state = state.copyWith(currentLevel: level);
    _saveToStorage();
  }

  /// Step 4: Set weak subjects (1-3 subjects)
  void setWeakSubjects(List<String> subjects) {
    // Validate: min 1, max 3
    if (subjects.isEmpty || subjects.length > 3) return;
    state = state.copyWith(weakSubjects: subjects);
    _saveToStorage();
  }

  /// Toggle a subject in weak subjects list
  void toggleWeakSubject(String subjectId) {
    final current = List<String>.from(state.weakSubjects);
    if (current.contains(subjectId)) {
      current.remove(subjectId);
    } else if (current.length < 3) {
      current.add(subjectId);
    }
    state = state.copyWith(weakSubjects: current);
    _saveToStorage();
  }

  /// Step 5: Set daily study time
  void setDailyStudyTime(StudyTimeCommitment time) {
    state = state.copyWith(dailyStudyTime: time);
    _saveToStorage();
  }

  /// Complete onboarding and sync to server
  Future<bool> completeOnboarding() async {
    if (!_validatePreferences()) return false;

    try {
      // Sync preferences to backend
      final response = await _apiClient.post(
        '/api/v1/onboarding/preferences',
        data: state.toJson(),
      );

      if (response.statusCode == 200) {
        state = state.copyWith(isComplete: true);
        await _saveToStorage();
        return true;
      }
    } catch (e) {
      // Save locally even if network fails
      state = state.copyWith(isComplete: true);
      await _saveToStorage();
      return true;
    }

    return false;
  }

  /// Validate all required fields are set
  bool _validatePreferences() {
    return state.goal != null &&
           state.currentLevel != null &&
           state.weakSubjects.isNotEmpty &&
           state.dailyStudyTime != null;
  }

  /// Check if step is complete
  bool isStepComplete(int step) {
    switch (step) {
      case 2:
        return state.goal != null;
      case 3:
        return state.currentLevel != null;
      case 4:
        return state.weakSubjects.isNotEmpty;
      case 5:
        return state.dailyStudyTime != null;
      default:
        return false;
    }
  }

  /// Reset all preferences
  void reset() {
    state = const OnboardingPreferences();
    _saveToStorage();
  }
}

/// Provider
final onboardingPreferencesProvider =
    StateNotifierProvider<OnboardingPreferencesNotifier, OnboardingPreferences>((ref) {
  final apiClient = ref.watch(apiClientProvider);
  return OnboardingPreferencesNotifier(apiClient);
});
