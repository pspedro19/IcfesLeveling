import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../core/config/routes.dart';
import '../../../../core/services/onboarding_service.dart';
import '../providers/auth_provider.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isPasswordVisible = false;
  bool _showEmailForm = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleGoogleSignIn() async {
    await ref.read(authProvider.notifier).signInWithGoogle();
  }

  Future<void> _handleAppleSignIn() async {
    await ref.read(authProvider.notifier).signInWithApple();
  }

  Future<void> _handleGuestSignIn() async {
    // Use demo mode for offline testing (no Firebase/backend required)
    await ref.read(authProvider.notifier).enterDemoMode();
  }

  @override
  Widget build(BuildContext context) {
    // Listen for auth state changes
    ref.listen<AuthState>(authProvider, (previous, next) {
      if (next.error != null && !next.isLoading) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(next.error!),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
      // Navigate on successful login
      if (next.user != null && previous?.user == null) {
        // User just logged in - advance onboarding step and navigate
        final onboardingNotifier = ref.read(onboardingProvider.notifier);

        if (next.user!.diagnosticCompleted) {
          // Diagnostic already done (returning user) - complete onboarding
          onboardingNotifier.completeOnboarding();
          context.go(AppRoutes.home);
        } else {
          // New user or returning without completed diagnostic - go to diagnostic
          onboardingNotifier.setStep(OnboardingStep.diagnostic);
          context.go(AppRoutes.diagnosticQuick);
        }
      }
    });

    final authState = ref.watch(authProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: Stack(
        children: [
          // Background accents
          Positioned(
            top: -100,
            right: -100,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.blue.withOpacity(0.05),
              ),
            ).animate(onPlay: (c) => c.repeat(reverse: true))
             .scale(begin: const Offset(1, 1), end: const Offset(1.2, 1.2), duration: 3.seconds),
          ),

          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 60),

                  // Rank/Icon
                  Center(
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.blue.withOpacity(0.3), width: 1),
                      ),
                      child: const Icon(
                        Icons.fingerprint,
                        size: 64,
                        color: Colors.white,
                      ),
                    ).animate().scale(duration: 600.ms, curve: Curves.easeOut),
                  ),

                  const SizedBox(height: 32),

                  const Text(
                    "EL SISTEMA TE BUSCA",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 2,
                    ),
                  ).animate().fadeIn(delay: 300.ms),

                  const SizedBox(height: 12),

                  const Text(
                    "Inicia sesión para registrar tu progreso y reclamar tus recompensas de cazador.",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: Colors.grey,
                      fontSize: 16,
                      height: 1.5,
                    ),
                  ).animate().fadeIn(delay: 500.ms),

                  const SizedBox(height: 40),

                  // Email/Password Form (expandable)
                  if (_showEmailForm) ...[
                    _buildEmailForm(authState),
                  ] else ...[
                    // Social login buttons
                    _LoginButton(
                      label: "CONTINUAR CON GOOGLE",
                      icon: Icons.g_mobiledata,
                      onPressed: authState.isLoading ? null : () => _handleGoogleSignIn(),
                    ).animate().slideY(begin: 0.2, end: 0, delay: 700.ms).fadeIn(delay: 700.ms),

                    const SizedBox(height: 16),

                    _LoginButton(
                      label: "CONTINUAR CON APPLE",
                      icon: Icons.apple,
                      onPressed: authState.isLoading ? null : () => _handleAppleSignIn(),
                    ).animate().slideY(begin: 0.2, end: 0, delay: 850.ms).fadeIn(delay: 850.ms),

                    const SizedBox(height: 24),

                    // Divider
                    Row(
                      children: [
                        Expanded(child: Divider(color: Colors.grey.shade700)),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Text("O", style: TextStyle(color: Colors.grey.shade600)),
                        ),
                        Expanded(child: Divider(color: Colors.grey.shade700)),
                      ],
                    ).animate().fadeIn(delay: 1.seconds),

                    const SizedBox(height: 24),

                    // Email login button
                    _LoginButton(
                      label: "CONTINUAR CON EMAIL",
                      icon: Icons.email_outlined,
                      backgroundColor: Colors.blue.shade700,
                      textColor: Colors.white,
                      onPressed: authState.isLoading ? null : () {
                        setState(() => _showEmailForm = true);
                      },
                    ).animate().slideY(begin: 0.2, end: 0, delay: 1.1.seconds).fadeIn(delay: 1.1.seconds),
                  ],

                  const SizedBox(height: 24),

                  // Demo Mode - works offline without backend
                  ElevatedButton.icon(
                    onPressed: authState.isLoading ? null : () => _handleGuestSignIn(),
                    icon: const Icon(Icons.play_circle_outline, size: 20),
                    label: const Text(
                      'MODO DESARROLLADOR',
                      style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green.shade700,
                      foregroundColor: Colors.white,
                      minimumSize: const Size(200, 48),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ).animate().fadeIn(delay: _showEmailForm ? 100.ms : 1.2.seconds),

                  const SizedBox(height: 8),

                  Text(
                    "Explora la app sin conexion",
                    style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                  ).animate().fadeIn(delay: _showEmailForm ? 150.ms : 1.3.seconds),

                  const SizedBox(height: 40),

                  RichText(
                    textAlign: TextAlign.center,
                    text: TextSpan(
                      text: "Al continuar, aceptas nuestros ",
                      style: const TextStyle(color: Colors.white24, fontSize: 12),
                      children: [
                        TextSpan(
                          text: "Términos de Servicio",
                          style: const TextStyle(
                            color: Colors.blue,
                            decoration: TextDecoration.underline,
                          ),
                          recognizer: TapGestureRecognizer()
                            ..onTap = () => _launchUrl('https://icfesleveling.com/terms'),
                        ),
                        const TextSpan(text: " y "),
                        TextSpan(
                          text: "Política de Privacidad",
                          style: const TextStyle(
                            color: Colors.blue,
                            decoration: TextDecoration.underline,
                          ),
                          recognizer: TapGestureRecognizer()
                            ..onTap = () => _launchUrl('https://icfesleveling.com/privacy'),
                        ),
                        const TextSpan(text: "."),
                      ],
                    ),
                  ).animate().fadeIn(delay: 1.5.seconds),

                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),

          // Loading indicator
          if (authState.isLoading)
            Container(
              color: Colors.black.withOpacity(0.7),
              child: const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    CircularProgressIndicator(color: Colors.blue),
                    SizedBox(height: 16),
                    Text(
                      "Conectando con el Sistema...",
                      style: TextStyle(color: Colors.white70),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildEmailForm(AuthState authState) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          // Back button
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton.icon(
              onPressed: () => setState(() => _showEmailForm = false),
              icon: const Icon(Icons.arrow_back, color: Colors.grey),
              label: const Text("Volver", style: TextStyle(color: Colors.grey)),
            ),
          ),

          const SizedBox(height: 16),

          // Email field
          TextFormField(
            controller: _emailController,
            keyboardType: TextInputType.emailAddress,
            style: const TextStyle(color: Colors.white),
            decoration: InputDecoration(
              labelText: "Email",
              labelStyle: TextStyle(color: Colors.grey.shade400),
              prefixIcon: const Icon(Icons.email_outlined, color: Colors.grey),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: Colors.grey.shade700),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.blue),
              ),
              errorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.red),
              ),
              focusedErrorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.red),
              ),
              filled: true,
              fillColor: Colors.grey.shade900,
            ),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Ingresa tu email';
              }
              if (!value.contains('@')) {
                return 'Ingresa un email válido';
              }
              return null;
            },
          ).animate().fadeIn().slideY(begin: 0.1, end: 0),

          const SizedBox(height: 16),

          // Password field
          TextFormField(
            controller: _passwordController,
            obscureText: !_isPasswordVisible,
            style: const TextStyle(color: Colors.white),
            decoration: InputDecoration(
              labelText: "Contraseña",
              labelStyle: TextStyle(color: Colors.grey.shade400),
              prefixIcon: const Icon(Icons.lock_outline, color: Colors.grey),
              suffixIcon: IconButton(
                icon: Icon(
                  _isPasswordVisible ? Icons.visibility_off : Icons.visibility,
                  color: Colors.grey,
                ),
                onPressed: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: Colors.grey.shade700),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.blue),
              ),
              errorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.red),
              ),
              focusedErrorBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.red),
              ),
              filled: true,
              fillColor: Colors.grey.shade900,
            ),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return 'Ingresa tu contraseña';
              }
              if (value.length < 6) {
                return 'La contraseña debe tener al menos 6 caracteres';
              }
              return null;
            },
          ).animate().fadeIn(delay: 100.ms).slideY(begin: 0.1, end: 0),

          const SizedBox(height: 24),

          // Login button
          SizedBox(
            width: double.infinity,
            height: 56,
            child: ElevatedButton(
              onPressed: authState.isLoading ? null : _handleEmailLogin,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue.shade700,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text(
                "INICIAR SESIÓN",
                style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1),
              ),
            ),
          ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.1, end: 0),

          const SizedBox(height: 16),

          // Register link
          TextButton(
            onPressed: () => context.push(AppRoutes.register),
            child: RichText(
              text: TextSpan(
                text: "¿No tienes cuenta? ",
                style: TextStyle(color: Colors.grey.shade500),
                children: const [
                  TextSpan(
                    text: "Regístrate",
                    style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
          ).animate().fadeIn(delay: 300.ms),
        ],
      ),
    );
  }

  void _handleEmailLogin() {
    if (_formKey.currentState!.validate()) {
      ref.read(authProvider.notifier).login(
        _emailController.text.trim(),
        _passwordController.text,
      );
    }
  }

  Future<void> _launchUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

}

class _LoginButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback? onPressed;
  final Color? backgroundColor;
  final Color? textColor;

  const _LoginButton({
    required this.label,
    required this.icon,
    required this.onPressed,
    this.backgroundColor,
    this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: backgroundColor ?? Colors.white,
        foregroundColor: textColor ?? Colors.black,
        minimumSize: const Size(double.infinity, 56),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 28),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
