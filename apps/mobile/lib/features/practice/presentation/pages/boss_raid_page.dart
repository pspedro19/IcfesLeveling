import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../providers/boss_raid_provider.dart';

/// Boss Raid Entry Page - Shows the boss overview and lets users start a raid
class BossRaidPage extends ConsumerWidget {
  const BossRaidPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(bossRaidProvider);
    final notifier = ref.read(bossRaidProvider.notifier);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: Stack(
        children: [
          // Background Boss Aura
          Positioned.fill(
            child: Container(
              decoration: BoxDecoration(
                gradient: RadialGradient(
                  colors: [Colors.purple.withOpacity(0.15), Colors.black],
                  center: Alignment.topCenter,
                  radius: 1.2,
                ),
              ),
            ),
          ).animate(onPlay: (c) => c.repeat(reverse: true))
           .shimmer(duration: 4.seconds, color: Colors.purple.withOpacity(0.1)),

          if (state.isLoading && state.status == null)
            const Center(child: CircularProgressIndicator(color: Colors.purple))
          else if (state.error != null && state.status == null)
            _ErrorView(
              error: state.error!,
              onRetry: () => notifier.fetchStatus(),
            )
          else if (state.status != null)
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  children: [
                    const SizedBox(height: 20),

                    // Top bar
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        IconButton(
                          icon: const Icon(Icons.close, color: Colors.white, size: 28),
                          onPressed: () => context.pop(),
                        ),
                        if (state.status!.isActive)
                          _RaidTimerBadge(
                            timeRemaining: state.status!.formattedTimeRemaining,
                          ),
                      ],
                    ),

                    const SizedBox(height: 40),

                    // Boss Visual
                    _BossVisual(
                      name: state.status!.bossName,
                      rank: state.status!.isActive ? "S-RANK BOSS" : "ESPERANDO",
                      isActive: state.status!.isActive,
                    ).animate().shake(duration: 800.ms, hz: 4).fadeIn(),

                    const SizedBox(height: 40),

                    // Boss Status Card
                    _BossStatusCard(
                      maxHp: state.status!.bossHp,
                      currentHp: state.status!.bossCurrentHp,
                      myDamage: state.status!.myDamageDealt,
                      myRank: state.status!.myRank,
                      xpMultiplier: state.status!.xpMultiplier,
                    ).animate().slideY(begin: 0.2, end: 0).fadeIn(delay: 400.ms),

                    const Spacer(),

                    // Start Raid Button
                    if (state.status!.isActive)
                      _StartRaidButton(
                        isLoading: state.isLoading,
                        onPressed: () async {
                          final sessionId = await notifier.startRaid();
                          if (sessionId != null && context.mounted) {
                            context.push('/boss-raid/battle/$sessionId');
                          }
                        },
                      )
                    else
                      _RaidInactiveMessage(),

                    const SizedBox(height: 40),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String error;
  final VoidCallback onRetry;

  const _ErrorView({required this.error, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 64),
            const SizedBox(height: 16),
            Text(
              'Error al cargar la raid',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style: const TextStyle(color: Colors.white70),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Reintentar'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.purple,
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BossVisual extends StatelessWidget {
  final String name;
  final String rank;
  final bool isActive;

  const _BossVisual({
    required this.name,
    required this.rank,
    required this.isActive,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 180,
          height: 180,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: isActive
                  ? Colors.purple.withOpacity(0.5)
                  : Colors.grey.withOpacity(0.3),
              width: 2,
            ),
            boxShadow: isActive ? [
              BoxShadow(
                color: Colors.purple.withOpacity(0.3),
                blurRadius: 40,
                spreadRadius: 10,
              ),
            ] : null,
          ),
          child: Icon(
            Icons.psychology,
            color: isActive ? Colors.purpleAccent : Colors.grey,
            size: 100,
          ),
        ),
        const SizedBox(height: 24),
        Text(
          rank,
          style: TextStyle(
            color: isActive ? Colors.redAccent : Colors.grey,
            fontWeight: FontWeight.w900,
            fontSize: 14,
            letterSpacing: 4,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          name,
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 24,
            fontWeight: FontWeight.w900,
            letterSpacing: 1,
          ),
        ),
      ],
    );
  }
}

class _BossStatusCard extends StatelessWidget {
  final int maxHp;
  final int currentHp;
  final int myDamage;
  final int? myRank;
  final double xpMultiplier;

  const _BossStatusCard({
    required this.maxHp,
    required this.currentHp,
    required this.myDamage,
    this.myRank,
    required this.xpMultiplier,
  });

  @override
  Widget build(BuildContext context) {
    final progress = (currentHp > 0 && maxHp > 0) ? currentHp / maxHp : 0.0;
    final damageDealt = maxHp - currentHp;
    final phase = progress > 0.66 ? 1 : progress > 0.33 ? 2 : 3;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        children: [
          // Phase and HP
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.purple.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  "FASE $phase",
                  style: const TextStyle(
                    color: Colors.purpleAccent,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
              Text(
                "$currentHp / $maxHp HP",
                style: const TextStyle(
                  color: Colors.white70,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // HP Bar
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 12,
              backgroundColor: Colors.white.withOpacity(0.05),
              valueColor: AlwaysStoppedAnimation<Color>(
                progress > 0.5 ? Colors.red : progress > 0.25 ? Colors.orange : Colors.yellow,
              ),
            ),
          ),

          const SizedBox(height: 20),

          // Stats row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _StatItem(
                icon: Icons.flash_on,
                label: 'Dano total',
                value: damageDealt.toString(),
                color: Colors.red,
              ),
              _StatItem(
                icon: Icons.person,
                label: 'Mi dano',
                value: myDamage.toString(),
                color: Colors.cyan,
              ),
              _StatItem(
                icon: Icons.star,
                label: 'XP Bonus',
                value: '${xpMultiplier.toStringAsFixed(0)}x',
                color: Colors.amber,
              ),
            ],
          ),

          // Rank if available
          if (myRank != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.amber.withOpacity(0.15),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.amber.withOpacity(0.3)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.leaderboard, color: Colors.amber, size: 18),
                  const SizedBox(width: 8),
                  Text(
                    'Puesto #$myRank en la Raid',
                    style: const TextStyle(
                      color: Colors.amber,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _StatItem({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            color: color.withOpacity(0.7),
            fontSize: 10,
          ),
        ),
      ],
    );
  }
}

class _RaidTimerBadge extends StatelessWidget {
  final String timeRemaining;

  const _RaidTimerBadge({required this.timeRemaining});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.15),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.red.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.timer, color: Colors.red, size: 20),
          const SizedBox(width: 8),
          Text(
            timeRemaining,
            style: const TextStyle(
              color: Colors.red,
              fontWeight: FontWeight.w900,
              fontSize: 16,
              fontFamily: 'monospace',
            ),
          ),
        ],
      ),
    ).animate(onPlay: (c) => c.repeat(reverse: true))
     .scale(begin: const Offset(1, 1), end: const Offset(1.02, 1.02), duration: 1.seconds);
  }
}

class _StartRaidButton extends StatelessWidget {
  final bool isLoading;
  final VoidCallback onPressed;

  const _StartRaidButton({
    required this.isLoading,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: isLoading ? null : onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.red.shade900,
        foregroundColor: Colors.white,
        minimumSize: const Size(double.infinity, 70),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: Colors.red.withOpacity(0.5), width: 2),
        ),
        elevation: 15,
        shadowColor: Colors.red,
      ),
      child: isLoading
          ? const SizedBox(
              width: 28,
              height: 28,
              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 3),
            )
          : Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: const [
                Icon(Icons.flash_on, size: 28),
                SizedBox(width: 12),
                Text(
                  "ENTRAR A LA MAZMORRA",
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 2,
                  ),
                ),
              ],
            ),
    ).animate(onPlay: (c) => c.repeat(reverse: true))
     .scale(begin: const Offset(1, 1), end: const Offset(1.02, 1.02), duration: 1.seconds)
     .shimmer(delay: 1.seconds, color: Colors.red.withOpacity(0.3));
  }
}

class _RaidInactiveMessage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.grey.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.grey.withOpacity(0.3)),
      ),
      child: Column(
        children: const [
          Icon(Icons.hourglass_empty, color: Colors.grey, size: 40),
          SizedBox(height: 12),
          Text(
            'La Raid no esta activa',
            style: TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Vuelve pronto para enfrentarte al Boss',
            style: TextStyle(color: Colors.grey, fontSize: 14),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
