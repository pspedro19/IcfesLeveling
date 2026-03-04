import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/app_theme.dart';
import '../../../../shared/providers/balance_provider.dart';
import '../../../engagement/presentation/providers/engagement_provider.dart';
import '../../data/models/millionaire_models.dart';
import '../providers/millionaire_provider.dart';
import '../widgets/lifeline_button.dart';
import '../widgets/prize_ladder.dart';
import '../widgets/millionaire_question_card.dart';

class MillionairePage extends ConsumerStatefulWidget {
  const MillionairePage({super.key});

  @override
  ConsumerState<MillionairePage> createState() => _MillionairePageState();
}

class _MillionairePageState extends ConsumerState<MillionairePage> {
  bool _isPrizeLadderExpanded = false;
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    final gameState = ref.watch(millionaireProvider);
    final engagement = ref.watch(engagementProvider);
    final userGold = ref.watch(goldProvider);

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              const Color(0xFF1a1a2e),
              const Color(0xFF16213e),
              AppTheme.bgDark,
            ],
          ),
        ),
        child: SafeArea(
          child: _buildContent(gameState, engagement, userGold),
        ),
      ),
    );
  }

  Widget _buildContent(MillionaireGameState gameState, EngagementState engagement, int userGold) {
    switch (gameState.status) {
      case MillionaireGameStatus.notStarted:
        return _buildStartScreen(gameState);
      case MillionaireGameStatus.playing:
        return _buildGameScreen(gameState, userGold);
      case MillionaireGameStatus.won:
      case MillionaireGameStatus.lost:
      case MillionaireGameStatus.walkingAway:
        return _buildResultScreen(gameState);
    }
  }

  Widget _buildStartScreen(MillionaireGameState gameState) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // Back button
          Align(
            alignment: Alignment.topLeft,
            child: IconButton(
              onPressed: () => context.pop(),
              icon: const Icon(Icons.arrow_back, color: AppTheme.textPrimary),
            ),
          ),

          const SizedBox(height: 20),

          // Title with glow effect
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  AppTheme.secondaryGold.withOpacity(0.2),
                  Colors.transparent,
                ],
              ),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(
              children: [
                const Icon(
                  Icons.diamond_rounded,
                  size: 64,
                  color: AppTheme.secondaryGold,
                )
                    .animate(onPlay: (c) => c.repeat(reverse: true))
                    .shimmer(duration: 2000.ms),
                const SizedBox(height: 16),
                const Text(
                  'MODO MILLONARIO',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.secondaryGold,
                    letterSpacing: 3,
                  ),
                ).animate().fadeIn(duration: 500.ms),
                const SizedBox(height: 8),
                Text(
                  'Quien quiere ser millonario?',
                  style: TextStyle(
                    fontSize: 16,
                    color: AppTheme.textSecondary,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 32),

          // Rules card
          _buildRulesCard(),

          const SizedBox(height: 24),

          // Checkpoints info
          _buildCheckpointsCard(),

          const SizedBox(height: 24),

          // Lifelines info
          _buildLifelinesCard(),

          const SizedBox(height: 32),

          // Games remaining
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.bgCard,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: gameState.canPlay
                    ? AppTheme.successGreen.withOpacity(0.5)
                    : AppTheme.dangerRed.withOpacity(0.5),
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  gameState.canPlay ? Icons.play_circle : Icons.timer,
                  color: gameState.canPlay
                      ? AppTheme.successGreen
                      : AppTheme.dangerRed,
                  size: 28,
                ),
                const SizedBox(width: 12),
                Text(
                  gameState.canPlay
                      ? 'Partidas disponibles: ${gameState.remainingGames}/3'
                      : 'Sin partidas hoy. Vuelve manana!',
                  style: TextStyle(
                    color: gameState.canPlay
                        ? AppTheme.textPrimary
                        : AppTheme.dangerRed,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 32),

          // Start button
          if (gameState.canPlay)
            SizedBox(
              width: double.infinity,
              height: 60,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _startGame,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.secondaryGold,
                  foregroundColor: Colors.black,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.black)
                    : const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.play_arrow_rounded, size: 28),
                          SizedBox(width: 8),
                          Text(
                            'INICIAR JUEGO',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 2,
                            ),
                          ),
                        ],
                      ),
              ),
            )
                .animate()
                .fadeIn(delay: 300.ms)
                .scale(begin: const Offset(0.9, 0.9)),
        ],
      ),
    );
  }

  Widget _buildRulesCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.primaryPurple.withOpacity(0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.rule, color: AppTheme.primaryPurple),
              const SizedBox(width: 8),
              const Text(
                'Reglas del Juego',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildRuleItem(Icons.help_outline, '15 preguntas de dificultad progresiva'),
          _buildRuleItem(Icons.trending_up, 'Dificultad: Facil -> Media -> Dificil'),
          _buildRuleItem(Icons.shield, 'Checkpoints aseguran recompensas minimas'),
          _buildRuleItem(Icons.close, 'Si fallas, ganas lo del ultimo checkpoint'),
          _buildRuleItem(Icons.calendar_today, 'Limite: 3 partidas por dia'),
        ],
      ),
    ).animate().fadeIn(delay: 100.ms).slideY(begin: 0.1, end: 0);
  }

  Widget _buildRuleItem(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppTheme.textSecondary, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCheckpointsCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.secondaryGold.withOpacity(0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.emoji_events, color: AppTheme.secondaryGold),
              const SizedBox(width: 8),
              const Text(
                'Checkpoints (Seguros)',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          for (final checkpoint in Checkpoint.all)
            _buildCheckpointRow(checkpoint),
        ],
      ),
    ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.1, end: 0);
  }

  Widget _buildCheckpointRow(Checkpoint checkpoint) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppTheme.bgElevated,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              const Icon(Icons.shield, color: AppTheme.secondaryGold, size: 20),
              const SizedBox(width: 8),
              Text(
                'Pregunta ${checkpoint.questionNumber}',
                style: const TextStyle(
                  color: AppTheme.textPrimary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          Row(
            children: [
              Text(
                '${checkpoint.guaranteedXp} XP',
                style: const TextStyle(
                  color: AppTheme.accentCyan,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                '${checkpoint.guaranteedGold}',
                style: const TextStyle(
                  color: AppTheme.secondaryGold,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const Icon(Icons.monetization_on,
                  color: AppTheme.secondaryGold, size: 16),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLifelinesCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.bgCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.accentCyan.withOpacity(0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.help, color: AppTheme.accentCyan),
              const SizedBox(width: 8),
              const Text(
                'Comodines',
                style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildLifelineInfo(
            Icons.exposure_minus_2,
            '50:50',
            'Elimina 2 opciones incorrectas',
            'Gratis',
            AppTheme.accentCyan,
          ),
          _buildLifelineInfo(
            Icons.psychology,
            'Pista IA',
            'Muestra una pista (no la respuesta)',
            '50 Oro',
            AppTheme.secondaryGold,
          ),
          _buildLifelineInfo(
            Icons.skip_next,
            'Saltar',
            'Salta la pregunta sin penalizacion',
            'Gratis',
            AppTheme.successGreen,
          ),
        ],
      ),
    ).animate().fadeIn(delay: 300.ms).slideY(begin: 0.1, end: 0);
  }

  Widget _buildLifelineInfo(
    IconData icon,
    String name,
    String description,
    String cost,
    Color color,
  ) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      name,
                      style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        cost,
                        style: TextStyle(
                          color: color,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  description,
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGameScreen(MillionaireGameState gameState, int userGold) {
    final currentQuestion = gameState.currentQuestion;
    if (currentQuestion == null) {
      return const Center(child: CircularProgressIndicator());
    }

    return Stack(
      children: [
        // Main content
        Column(
          children: [
            // Top bar
            _buildTopBar(gameState, userGold),

            // Question area
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    // Prize info
                    _buildPrizeInfo(currentQuestion),
                    const SizedBox(height: 16),

                    // Question card
                    MillionaireQuestionCard(
                      question: currentQuestion,
                      selectedAnswer: gameState.selectedAnswer,
                      isAnswerRevealed: gameState.isAnswerRevealed,
                      isEnabled: !gameState.isAnswerRevealed,
                      onOptionSelected: _onOptionSelected,
                    ),

                    const SizedBox(height: 100), // Space for bottom bar
                  ],
                ),
              ),
            ),
          ],
        ),

        // Floating prize ladder
        Positioned(
          top: 70,
          right: 8,
          child: GestureDetector(
            onTap: () =>
                setState(() => _isPrizeLadderExpanded = !_isPrizeLadderExpanded),
            child: PrizeLadder(
              currentQuestionIndex: gameState.currentQuestionIndex,
              isExpanded: _isPrizeLadderExpanded,
              onToggle: () =>
                  setState(() => _isPrizeLadderExpanded = !_isPrizeLadderExpanded),
            ),
          ),
        ),

        // Bottom lifelines bar
        Positioned(
          bottom: 0,
          left: 0,
          right: 0,
          child: Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.transparent,
                  AppTheme.bgDark.withOpacity(0.95),
                  AppTheme.bgDark,
                ],
              ),
            ),
            padding: const EdgeInsets.fromLTRB(16, 20, 16, 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Lifelines
                LifelineRow(
                  lifelines: gameState.lifelines,
                  isEnabled: !gameState.isAnswerRevealed,
                  userGold: userGold,
                  isLoadingHint: gameState.isLoadingHint,
                  onLifelineUsed: _onLifelineUsed,
                ),
                const SizedBox(height: 12),

                // Walk away button
                if (!gameState.isAnswerRevealed && gameState.currentQuestionIndex > 0)
                  TextButton.icon(
                    onPressed: _showWalkAwayDialog,
                    icon: const Icon(Icons.exit_to_app, size: 18),
                    label: const Text('Retirarse con ${0} XP'),
                    style: TextButton.styleFrom(
                      foregroundColor: AppTheme.textSecondary,
                    ),
                  ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildTopBar(MillionaireGameState gameState, int userGold) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: AppTheme.bgCard.withOpacity(0.9),
        border: Border(
          bottom: BorderSide(
            color: AppTheme.primaryPurple.withOpacity(0.3),
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Back/Exit button
          IconButton(
            onPressed: () => _showExitDialog(),
            icon: const Icon(Icons.close, color: AppTheme.textPrimary),
          ),

          // Current earnings
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: AppTheme.accentCyan.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.bolt, color: AppTheme.accentCyan, size: 18),
                    const SizedBox(width: 4),
                    Text(
                      '${gameState.earnedXp} XP',
                      style: const TextStyle(
                        color: AppTheme.accentCyan,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: AppTheme.secondaryGold.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.monetization_on,
                        color: AppTheme.secondaryGold, size: 18),
                    const SizedBox(width: 4),
                    Text(
                      '$userGold',
                      style: const TextStyle(
                        color: AppTheme.secondaryGold,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildPrizeInfo(MillionaireQuestion question) {
    final tier = question.prizeTier;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.secondaryGold.withOpacity(0.1),
            Colors.transparent,
          ],
        ),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.secondaryGold.withOpacity(0.3),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text(
            'Premio: ',
            style: TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 14,
            ),
          ),
          Text(
            '+${tier.xpReward} XP',
            style: const TextStyle(
              color: AppTheme.accentCyan,
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
          const SizedBox(width: 12),
          Text(
            '+${tier.goldReward}',
            style: const TextStyle(
              color: AppTheme.secondaryGold,
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
          const Icon(Icons.monetization_on,
              color: AppTheme.secondaryGold, size: 18),
          if (tier.isCheckpoint) ...[
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: AppTheme.secondaryGold.withOpacity(0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: const [
                  Icon(Icons.shield, color: AppTheme.secondaryGold, size: 14),
                  SizedBox(width: 4),
                  Text(
                    'CHECKPOINT',
                    style: TextStyle(
                      color: AppTheme.secondaryGold,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    ).animate().fadeIn(duration: 300.ms);
  }

  Widget _buildResultScreen(MillionaireGameState gameState) {
    final result = ref.read(millionaireProvider.notifier).getResult();
    final isWin = gameState.status == MillionaireGameStatus.won;
    final isWalkAway = gameState.status == MillionaireGameStatus.walkingAway;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const SizedBox(height: 40),

          // Result icon
          Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: isWin
                    ? [AppTheme.secondaryGold, Colors.orange]
                    : isWalkAway
                        ? [AppTheme.accentCyan, AppTheme.primaryPurple]
                        : [AppTheme.dangerRed, Colors.orange.shade900],
              ),
              boxShadow: [
                BoxShadow(
                  color: (isWin
                          ? AppTheme.secondaryGold
                          : isWalkAway
                              ? AppTheme.accentCyan
                              : AppTheme.dangerRed)
                      .withOpacity(0.4),
                  blurRadius: 30,
                  spreadRadius: 5,
                ),
              ],
            ),
            child: Icon(
              isWin
                  ? Icons.emoji_events
                  : isWalkAway
                      ? Icons.savings
                      : Icons.sentiment_dissatisfied,
              size: 60,
              color: Colors.white,
            ),
          )
              .animate()
              .scale(begin: const Offset(0, 0), duration: 500.ms, curve: Curves.elasticOut),

          const SizedBox(height: 32),

          // Result title
          Text(
            isWin
                ? 'FELICIDADES!'
                : isWalkAway
                    ? 'Te Retiraste'
                    : 'Fin del Juego',
            style: TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: isWin
                  ? AppTheme.secondaryGold
                  : isWalkAway
                      ? AppTheme.accentCyan
                      : AppTheme.textPrimary,
            ),
          ).animate().fadeIn(delay: 200.ms),

          const SizedBox(height: 8),

          Text(
            isWin
                ? 'Completaste las 15 preguntas!'
                : isWalkAway
                    ? 'Deciscion sabia, te llevas tus ganancias'
                    : 'Llegaste hasta la pregunta ${result.questionsAnswered}',
            style: const TextStyle(
              fontSize: 16,
              color: AppTheme.textSecondary,
            ),
            textAlign: TextAlign.center,
          ).animate().fadeIn(delay: 300.ms),

          const SizedBox(height: 40),

          // Rewards card
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: AppTheme.bgCard,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: AppTheme.primaryPurple.withOpacity(0.3),
              ),
            ),
            child: Column(
              children: [
                const Text(
                  'RECOMPENSAS',
                  style: TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 12,
                    letterSpacing: 2,
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildRewardItem(
                      Icons.bolt,
                      '${result.totalXp}',
                      'XP',
                      AppTheme.accentCyan,
                    ),
                    _buildRewardItem(
                      Icons.monetization_on,
                      '${result.totalGold}',
                      'Oro',
                      AppTheme.secondaryGold,
                    ),
                  ],
                ),
                if (result.reachedCheckpoint != null) ...[
                  const SizedBox(height: 20),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.successGreen.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.shield,
                            color: AppTheme.successGreen, size: 20),
                        const SizedBox(width: 8),
                        Text(
                          'Checkpoint ${result.reachedCheckpoint!.questionNumber} alcanzado!',
                          style: const TextStyle(
                            color: AppTheme.successGreen,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ).animate().fadeIn(delay: 400.ms).slideY(begin: 0.2, end: 0),

          const SizedBox(height: 40),

          // Action buttons
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _playAgain,
              icon: const Icon(Icons.refresh),
              label: const Text('JUGAR DE NUEVO'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryPurple,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ).animate().fadeIn(delay: 500.ms),

          const SizedBox(height: 12),

          TextButton(
            onPressed: () => context.pop(),
            child: const Text('Volver al inicio'),
          ).animate().fadeIn(delay: 600.ms),
        ],
      ),
    );
  }

  Widget _buildRewardItem(IconData icon, String value, String label, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 40),
        const SizedBox(height: 8),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontSize: 32,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            color: AppTheme.textSecondary,
            fontSize: 14,
          ),
        ),
      ],
    )
        .animate()
        .fadeIn(delay: 450.ms)
        .scale(begin: const Offset(0.8, 0.8), curve: Curves.elasticOut);
  }

  // Actions

  Future<void> _startGame() async {
    setState(() => _isLoading = true);
    final success = await ref.read(millionaireProvider.notifier).startGame();
    setState(() => _isLoading = false);

    if (!success && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No se pudo iniciar el juego. Intenta de nuevo.'),
          backgroundColor: AppTheme.dangerRed,
        ),
      );
    }
  }

  void _onOptionSelected(String optionId) {
    ref.read(millionaireProvider.notifier).submitAnswer(optionId);
  }

  void _onLifelineUsed(LifelineType type) {
    final notifier = ref.read(millionaireProvider.notifier);

    switch (type) {
      case LifelineType.fiftyFifty:
        notifier.useFiftyFifty();
        break;
      case LifelineType.askAI:
        notifier.useAskAI();
        break;
      case LifelineType.skip:
        notifier.useSkip();
        break;
    }
  }

  void _showWalkAwayDialog() {
    final gameState = ref.read(millionaireProvider);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.bgCard,
        title: const Text('Retirarse?'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Si te retiras ahora te llevas:',
              style: TextStyle(color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(Icons.bolt, color: AppTheme.accentCyan),
                const SizedBox(width: 8),
                Text(
                  '${gameState.earnedXp} XP',
                  style: const TextStyle(
                    color: AppTheme.accentCyan,
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.monetization_on, color: AppTheme.secondaryGold),
                const SizedBox(width: 8),
                Text(
                  '${gameState.earnedGold} Oro',
                  style: const TextStyle(
                    color: AppTheme.secondaryGold,
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Continuar jugando'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              ref.read(millionaireProvider.notifier).walkAway();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.warningOrange,
            ),
            child: const Text('Retirarme'),
          ),
        ],
      ),
    );
  }

  void _showExitDialog() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.bgCard,
        title: const Text('Salir del juego?'),
        content: const Text(
          'Si sales ahora perderas todo el progreso de esta partida.',
          style: TextStyle(color: AppTheme.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              ref.read(millionaireProvider.notifier).resetGame();
              context.pop();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.dangerRed,
            ),
            child: const Text('Salir'),
          ),
        ],
      ),
    );
  }

  void _playAgain() {
    final gameState = ref.read(millionaireProvider);
    if (gameState.canPlay) {
      ref.read(millionaireProvider.notifier).resetGame();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Ya usaste tus 3 partidas de hoy. Vuelve manana!'),
          backgroundColor: AppTheme.warningOrange,
        ),
      );
      context.pop();
    }
  }
}
