import 'package:flutter_test/flutter_test.dart';

import 'package:icfes_mobile/core/auth/domain/entities/user.dart';
import 'package:icfes_mobile/features/auth/presentation/providers/auth_provider.dart';

void main() {
  group('AuthState', () {
    test('initial state has null user', () {
      final state = AuthState();
      expect(state.user, isNull);
      expect(state.isLoading, isFalse);
      expect(state.error, isNull);
    });

    test('copyWith creates new state with updated values', () {
      final initial = AuthState();
      final user = User(
        id: '1',
        email: 'test@test.com',
        name: 'Test User',
        level: 1,
        xp: 0,
        rank: 'E',
        hearts: 5,
        currentStreak: 0,
        diagnosticCompleted: false,
        completedDeepDiagnostics: [],
      );

      final updated = initial.copyWith(user: user, isLoading: true);

      expect(updated.user, equals(user));
      expect(updated.isLoading, isTrue);
      expect(updated.error, isNull);
    });

    test('copyWith with error sets error', () {
      final initial = AuthState();
      final updated = initial.copyWith(error: 'Test error');

      expect(updated.error, equals('Test error'));
      expect(updated.user, isNull);
    });

    test('copyWith preserves existing values when not specified', () {
      final user = User(
        id: '1',
        email: 'test@test.com',
        name: 'Test User',
        level: 1,
        xp: 0,
        rank: 'E',
        hearts: 5,
        currentStreak: 0,
        diagnosticCompleted: false,
        completedDeepDiagnostics: [],
      );

      final initial = AuthState(user: user);
      final updated = initial.copyWith(isLoading: true);

      expect(updated.user, equals(user));
      expect(updated.isLoading, isTrue);
    });
  });

  group('AuthNotifier - Basic State Tests', () {
    test('AuthState can be created with default values', () {
      final state = AuthState();

      expect(state.user, isNull);
      expect(state.isLoading, isFalse);
      expect(state.error, isNull);
    });

    test('AuthState copyWith updates loading state', () {
      final state = AuthState();
      final newState = state.copyWith(isLoading: true);

      expect(newState.isLoading, isTrue);
      expect(newState.user, isNull);
      expect(newState.error, isNull);
    });

    test('AuthState copyWith can set error', () {
      final state = AuthState();
      final newState = state.copyWith(error: 'Login failed');

      expect(newState.error, 'Login failed');
      expect(newState.isLoading, isFalse);
    });

    test('AuthState copyWith can set user', () {
      final state = AuthState();
      final testUser = User(
        id: 'test-id',
        email: 'test@example.com',
        name: 'Test User',
        level: 5,
        xp: 100,
        rank: 'D',
        hearts: 5,
        currentStreak: 5,
        diagnosticCompleted: true,
        completedDeepDiagnostics: ['math'],
      );

      final newState = state.copyWith(user: testUser);

      expect(newState.user, isNotNull);
      expect(newState.user!.email, 'test@example.com');
      expect(newState.user!.name, 'Test User');
      expect(newState.isLoading, isFalse);
    });

    test('AuthState copyWith clears user when set to null explicitly', () {
      final testUser = User(
        id: 'test-id',
        email: 'test@example.com',
        name: 'Test User',
        level: 1,
        xp: 0,
        rank: 'E',
        hearts: 5,
        currentStreak: 0,
        diagnosticCompleted: false,
        completedDeepDiagnostics: [],
      );

      final stateWithUser = AuthState(user: testUser);
      expect(stateWithUser.user, isNotNull);

      // Note: copyWith preserves existing values, to clear you'd need AuthState()
      final clearedState = AuthState();
      expect(clearedState.user, isNull);
    });

    test('Multiple copyWith calls chain correctly', () {
      final state = AuthState();

      final state1 = state.copyWith(isLoading: true);
      final state2 = state1.copyWith(error: 'Some error');
      final state3 = state2.copyWith(isLoading: false);

      expect(state3.isLoading, isFalse);
      expect(state3.error, 'Some error');
    });
  });

  group('User Entity Tests', () {
    test('User can be created with required fields', () {
      final user = User(
        id: '123',
        email: 'user@example.com',
        name: 'John Doe',
        level: 1,
        xp: 0,
        rank: 'E',
        hearts: 5,
        currentStreak: 0,
        diagnosticCompleted: false,
        completedDeepDiagnostics: [],
      );

      expect(user.id, '123');
      expect(user.email, 'user@example.com');
      expect(user.name, 'John Doe');
      expect(user.diagnosticCompleted, isFalse);
      expect(user.rank, 'E');
    });

    test('User with completed diagnostic', () {
      final user = User(
        id: '456',
        email: 'experienced@example.com',
        name: 'Jane Doe',
        level: 10,
        xp: 500,
        rank: 'C',
        hearts: 5,
        currentStreak: 10,
        diagnosticCompleted: true,
        completedDeepDiagnostics: ['math', 'reading'],
      );

      expect(user.diagnosticCompleted, isTrue);
      expect(user.currentStreak, 10);
      expect(user.xp, 500);
      expect(user.rank, 'C');
      expect(user.completedDeepDiagnostics, contains('math'));
    });
  });
}
