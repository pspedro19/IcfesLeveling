import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';
import '../../../../shared/widgets/lottie_overlay.dart';
import '../providers/battle_provider.dart';
import '../widgets/battle_result_dialog.dart';

class BattlePage extends ConsumerStatefulWidget {
  final String? encounterId;

  const BattlePage({super.key, this.encounterId});

  @override
  ConsumerState<BattlePage> createState() => _BattlePageState();
}

class _BattlePageState extends ConsumerState<BattlePage> {
  @override
  void initState() {
    super.initState();
    // Start the battle when the page loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final encounterId = widget.encounterId ??
          ref.read(battleEncounterIdProvider) ??
          'default_encounter';
      ref.read(battleProvider.notifier).startBattle(encounterId);
    });
  }

  @override
  void dispose() {
    super.dispose();
  }

  void _onSurrender() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          'Rendirse',
          style: TextStyle(color: Colors.white),
        ),
        content: const Text(
          'Estas seguro que quieres rendirte? Perderas todo el progreso de esta batalla.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancelar'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              ref.read(battleProvider.notifier).surrender();
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Rendirse'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final battleState = ref.watch(battleProvider);

    // Listen for battle result to show dialog
    ref.listen<BattleState>(battleProvider, (previous, next) {
      if (next.result != null && previous?.result == null) {
        _showResultDialog(next.result!);
      }
    });

    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: Stack(
        children: [
          // Background Arena
          Positioned.fill(
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.purple.shade900.withOpacity(0.4),
                    const Color(0xFF0F172A),
                  ],
                ),
              ),
            ),
          ),

          // Main Content
          if (battleState.isLoading)
            const _LoadingView()
          else if (battleState.error != null)
            _ErrorView(
              error: battleState.error!,
              onRetry: () {
                final encounterId = widget.encounterId ??
                    ref.read(battleEncounterIdProvider) ??
                    'default_encounter';
                ref.read(battleProvider.notifier).startBattle(encounterId);
              },
            )
          else if (battleState.questions.isEmpty)
            const _LoadingView()
          else
            _BattleContent(battleState: battleState),

          // Surrender Button
          Positioned(
            top: 50,
            left: 16,
            child: IconButton(
              icon: const Icon(Icons.flag, color: Colors.white38),
              onPressed: battleState.isBattleEnded ? null : _onSurrender,
            ),
          ),
        ],
      ),
    );
  }

  void _showResultDialog(BattleResult result) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => BattleResultDialog(
        isVictory: result.isVictory,
        xpEarned: result.xpEarned,
        goldEarned: result.goldEarned,
      ),
    ).then((_) {
      if (mounted) {
        ref.read(battleProvider.notifier).reset();
        context.pop();
      }
    });
  }
}

// ============================================================================
// LOADING VIEW
// ============================================================================

class _LoadingView extends StatelessWidget {
  const _LoadingView();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Lottie battle start animation
          Lottie.asset(
            LottieAssets.battleStart,
            width: 150,
            height: 150,
            repeat: true,
            errorBuilder: (_, __, ___) => const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Colors.purple),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Preparando batalla...',
            style: TextStyle(
              color: Colors.white.withOpacity(0.7),
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================================
// ERROR VIEW
// ============================================================================

class _ErrorView extends StatelessWidget {
  final String error;
  final VoidCallback onRetry;

  const _ErrorView({required this.error, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 64),
            const SizedBox(height: 16),
            Text(
              'Error al cargar la batalla',
              style: TextStyle(
                color: Colors.white.withOpacity(0.9),
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style: TextStyle(color: Colors.white.withOpacity(0.6)),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.purple,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ============================================================================
// BATTLE CONTENT
// ============================================================================

class _BattleContent extends ConsumerWidget {
  final BattleState battleState;

  const _BattleContent({required this.battleState});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SafeArea(
      child: Column(
        children: [
          // 1. COMBAT ZONE (Top Half)
          Expanded(
            flex: 5,
            child: Stack(
              children: [
                // Enemy (Top Right)
                Positioned(
                  top: 40,
                  right: 20,
                  child: Column(
                    children: [
                      _HealthBar(
                        current: battleState.enemyHpPercent,
                        label: battleState.enemyName,
                        color: Colors.red,
                      ),
                      const SizedBox(height: 10),
                      _EnemyAvatar(
                        imageUrl: battleState.enemyImageUrl,
                        theme: battleState.theme,
                        isAnimating: battleState.isAnimating &&
                            battleState.lastAnswerResult?.isCorrect == true,
                      ),
                    ],
                  ),
                ),

                // Player (Bottom Left)
                Positioned(
                  bottom: 40,
                  left: 20,
                  child: Column(
                    children: [
                      _PlayerAvatar(
                        isAnimating: battleState.isAnimating &&
                            battleState.lastAnswerResult?.isCorrect == false,
                      ),
                      const SizedBox(height: 10),
                      _HealthBar(
                        current: battleState.playerHpPercent,
                        label: "Cazador (Tu)",
                        color: Colors.green,
                      ),
                    ],
                  ),
                ),

                // Damage Text (Overlay)
                if (battleState.isAnimating && battleState.lastAnswerResult != null)
                  _DamageOverlay(result: battleState.lastAnswerResult!),
              ],
            ),
          ),

          // 2. CONTROL ZONE (Bottom Half)
          Expanded(
            flex: 4,
            child: _QuestionPanel(battleState: battleState),
          ),
        ],
      ),
    );
  }
}

// ============================================================================
// ENEMY AVATAR
// ============================================================================

class _EnemyAvatar extends StatelessWidget {
  final String? imageUrl;
  final bool isAnimating;
  final String theme;

  const _EnemyAvatar({this.imageUrl, this.isAnimating = false, this.theme = 'math'});

  @override
  Widget build(BuildContext context) {
    // Determine asset path based on theme if imageUrl is null
    final assetPath = 'assets/images/boss_$theme.png';
    
    Widget avatar = Container(
      height: 150,
      width: 150,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.red.withOpacity(0.1),
        border: Border.all(color: Colors.red.withOpacity(0.3)),
        image: imageUrl != null
            ? DecorationImage(
                image: NetworkImage(imageUrl!),
                fit: BoxFit.cover,
              )
            : DecorationImage(
                image: AssetImage(assetPath),
                fit: BoxFit.cover,
                onError: (exception, stackTrace) {
                   // Fallback if specific boss asset doesn't exist yet
                }
              ),
      ),
      child: imageUrl == null
          ? Image.asset(
              assetPath, 
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => const Icon(Icons.change_history, size: 80, color: Colors.red),
            )
          : null,
    );

    if (isAnimating) {
      return avatar
          .animate()
          .shake(duration: 500.ms)
          .then()
          .scale(begin: const Offset(0.95, 0.95), end: const Offset(1, 1));
    }

    return avatar
        .animate(onPlay: (controller) => controller.repeat(reverse: true))
        .scale(
            begin: const Offset(1, 1),
            end: const Offset(1.05, 1.05),
            duration: 2.seconds);
  }
}

// ============================================================================
// PLAYER AVATAR
// ============================================================================

class _PlayerAvatar extends StatelessWidget {
  final bool isAnimating;

  const _PlayerAvatar({this.isAnimating = false});

  @override
  Widget build(BuildContext context) {
    Widget avatar = Container(
      height: 120,
      width: 120,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Colors.blue.withOpacity(0.1),
        border: Border.all(color: Colors.blue.withOpacity(0.3)),
        image: const DecorationImage(
          image: AssetImage('assets/images/hero_avatar.png'),
          fit: BoxFit.cover,
        ),
      ),
    );

    if (isAnimating) {
      return avatar.animate().shake(duration: 500.ms);
    }

    return avatar;
  }
}

// ============================================================================
// DAMAGE OVERLAY
// ============================================================================

class _DamageOverlay extends StatelessWidget {
  final AnswerResult result;

  const _DamageOverlay({required this.result});

  @override
  Widget build(BuildContext context) {
    final text = result.isCorrect ? "-${result.damageDealt}" : "MISS";
    final color = result.isCorrect ? Colors.orange : Colors.red;

    return Center(
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 48,
          fontWeight: FontWeight.w900,
          fontStyle: FontStyle.italic,
        ),
      ).animate().slideY(begin: 0, end: -0.5).fadeOut(),
    );
  }
}

// ============================================================================
// QUESTION PANEL
// ============================================================================

class _QuestionPanel extends ConsumerWidget {
  final BattleState battleState;

  const _QuestionPanel({required this.battleState});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentQuestion = battleState.currentQuestion;

    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF1E293B),
        borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Combo Indicator
          if (battleState.comboCount > 1)
            Center(
              child: Text(
                "COMBO x${battleState.comboCount}!",
                style: const TextStyle(
                  color: Colors.amber,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 2,
                ),
              ).animate().scale(duration: 200.ms, curve: Curves.bounceOut),
            ),
          const SizedBox(height: 8),

          // Question Progress
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                "Pregunta ${battleState.currentQuestionIndex + 1}/${battleState.totalQuestions}",
                style: TextStyle(
                  color: Colors.white.withOpacity(0.6),
                  fontSize: 12,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Question Text
          Expanded(
            flex: 2,
            child: SingleChildScrollView(
              child: Column(
                children: [
                  Text(
                    currentQuestion?.text ?? 'Cargando pregunta...',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  // Question Image (if present)
                  if (currentQuestion?.imageUrl != null) ...[
                    const SizedBox(height: 12),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.network(
                        currentQuestion!.imageUrl!,
                        height: 120,
                        fit: BoxFit.contain,
                        errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Options Grid
          Expanded(
            flex: 3,
            child: _OptionsGrid(battleState: battleState),
          ),

          // Action Button (Check/Next)
          if (battleState.selectedAnswerId != null &&
              !battleState.isAnswering &&
              battleState.lastAnswerResult == null)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: ElevatedButton(
                onPressed: () => ref.read(battleProvider.notifier).submitAnswer(),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: const Text(
                  'ATACAR',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ),

          // Next Question Button (after answer)
          if (battleState.lastAnswerResult != null && !battleState.isBattleEnded)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: ElevatedButton(
                onPressed: battleState.isAnimating
                    ? null
                    : () => ref.read(battleProvider.notifier).nextQuestion(),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: Text(
                  battleState.hasMoreQuestions ? 'SIGUIENTE' : 'FINALIZAR',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// ============================================================================
// OPTIONS GRID
// ============================================================================

class _OptionsGrid extends ConsumerWidget {
  final BattleState battleState;

  const _OptionsGrid({required this.battleState});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final options = battleState.currentQuestion?.options ?? [];
    final colors = [Colors.blue, Colors.purple, Colors.orange, Colors.teal];
    final isAnswered = battleState.lastAnswerResult != null;

    return Column(
      children: [
        Expanded(
          child: Row(
            children: [
              if (options.isNotEmpty)
                Expanded(
                  child: _OptionButton(
                    text: options[0].text,
                    imageUrl: options[0].imageUrl,
                    color: colors[0],
                    isSelected: battleState.selectedAnswerId == options[0].id,
                    isCorrect: isAnswered
                        ? battleState.lastAnswerResult!.correctAnswerId ==
                            options[0].id
                        : null,
                    isAnswered: isAnswered,
                    onPressed: battleState.isAnswering || isAnswered
                        ? null
                        : () => ref
                            .read(battleProvider.notifier)
                            .selectAnswer(options[0].id),
                  ),
                ),
              const SizedBox(width: 12),
              if (options.length > 1)
                Expanded(
                  child: _OptionButton(
                    text: options[1].text,
                    imageUrl: options[1].imageUrl,
                    color: colors[1],
                    isSelected: battleState.selectedAnswerId == options[1].id,
                    isCorrect: isAnswered
                        ? battleState.lastAnswerResult!.correctAnswerId ==
                            options[1].id
                        : null,
                    isAnswered: isAnswered,
                    onPressed: battleState.isAnswering || isAnswered
                        ? null
                        : () => ref
                            .read(battleProvider.notifier)
                            .selectAnswer(options[1].id),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        Expanded(
          child: Row(
            children: [
              if (options.length > 2)
                Expanded(
                  child: _OptionButton(
                    text: options[2].text,
                    imageUrl: options[2].imageUrl,
                    color: colors[2],
                    isSelected: battleState.selectedAnswerId == options[2].id,
                    isCorrect: isAnswered
                        ? battleState.lastAnswerResult!.correctAnswerId ==
                            options[2].id
                        : null,
                    isAnswered: isAnswered,
                    onPressed: battleState.isAnswering || isAnswered
                        ? null
                        : () => ref
                            .read(battleProvider.notifier)
                            .selectAnswer(options[2].id),
                  ),
                ),
              const SizedBox(width: 12),
              if (options.length > 3)
                Expanded(
                  child: _OptionButton(
                    text: options[3].text,
                    imageUrl: options[3].imageUrl,
                    color: colors[3],
                    isSelected: battleState.selectedAnswerId == options[3].id,
                    isCorrect: isAnswered
                        ? battleState.lastAnswerResult!.correctAnswerId ==
                            options[3].id
                        : null,
                    isAnswered: isAnswered,
                    onPressed: battleState.isAnswering || isAnswered
                        ? null
                        : () => ref
                            .read(battleProvider.notifier)
                            .selectAnswer(options[3].id),
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

// ============================================================================
// OPTION BUTTON
// ============================================================================

class _OptionButton extends StatelessWidget {
  final String text;
  final String? imageUrl;
  final Color color;
  final bool isSelected;
  final bool? isCorrect;
  final bool isAnswered;
  final VoidCallback? onPressed;

  const _OptionButton({
    required this.text,
    this.imageUrl,
    required this.color,
    this.isSelected = false,
    this.isCorrect,
    this.isAnswered = false,
    this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    Color buttonColor = color;
    Color borderColor = color.withOpacity(0.5);

    if (isAnswered && isCorrect != null) {
      if (isCorrect!) {
        buttonColor = Colors.green;
        borderColor = Colors.green;
      } else if (isSelected) {
        buttonColor = Colors.red;
        borderColor = Colors.red;
      }
    } else if (isSelected) {
      borderColor = color;
    }

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          decoration: BoxDecoration(
            color: buttonColor.withOpacity(isSelected ? 0.3 : 0.2),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: borderColor,
              width: isSelected ? 2 : 1,
            ),
          ),
          padding: const EdgeInsets.all(12),
          child: Center(
            child: imageUrl != null
                ? Image.network(
                    imageUrl!,
                    fit: BoxFit.contain,
                    errorBuilder: (_, __, ___) => Text(
                      text,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: buttonColor.withOpacity(0.9),
                      ),
                      textAlign: TextAlign.center,
                    ),
                  )
                : Text(
                    text,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: isAnswered && isCorrect == true
                          ? Colors.white
                          : buttonColor.withOpacity(0.9),
                    ),
                    textAlign: TextAlign.center,
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                  ),
          ),
        ),
      ),
    );
  }
}

// ============================================================================
// HEALTH BAR
// ============================================================================

class _HealthBar extends StatelessWidget {
  final double current;
  final String label;
  final Color color;

  const _HealthBar({
    required this.current,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Container(
          width: 120,
          height: 8,
          decoration: BoxDecoration(
            color: Colors.black,
            borderRadius: BorderRadius.circular(4),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: TweenAnimationBuilder<double>(
              tween: Tween(begin: 1.0, end: current.clamp(0.0, 1.0)),
              duration: const Duration(milliseconds: 300),
              builder: (context, value, child) {
                return FractionallySizedBox(
                  alignment: Alignment.centerLeft,
                  widthFactor: value,
                  child: Container(
                    decoration: BoxDecoration(
                      color: color,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                );
              },
            ),
          ),
        ),
      ],
    );
  }
}
