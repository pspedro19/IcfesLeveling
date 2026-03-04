import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/routes.dart';
import '../../../../core/services/onboarding_service.dart';
import '../providers/auth_provider.dart';

class RegisterPage extends ConsumerStatefulWidget {
  const RegisterPage({super.key});

  @override
  ConsumerState<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends ConsumerState<RegisterPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState!.validate()) {
      ref.read(authProvider.notifier).register(
            _emailController.text.trim(),
            _passwordController.text,
            _nameController.text.trim(),
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<AuthState>(authProvider, (previous, next) {
      if (next.error != null && !next.isLoading) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(next.error!), backgroundColor: Colors.red),
        );
      }

      // Navigate on successful registration
      if (next.user != null && previous?.user == null) {
        // New user registered - advance to diagnostic step
        final onboardingNotifier = ref.read(onboardingProvider.notifier);
        onboardingNotifier.setStep(OnboardingStep.diagnostic);
        context.go(AppRoutes.diagnosticQuick);
      }
    });

    final authState = ref.watch(authProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A), // AppTheme.darkBackground
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  "UNETE A LA CACERÍA",
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 28,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 1.5,
                  ),
                ).animate().fadeIn().slideX(),
                const SizedBox(height: 8),
                const Text(
                  "Crea tu cuenta de cazador para comenzar.",
                  style: TextStyle(color: Colors.grey, fontSize: 16),
                ).animate().fadeIn().slideX(delay: 100.ms),
                const SizedBox(height: 32),
                
                // Name
                TextFormField(
                  controller: _nameController,
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(
                    labelText: "Nombre de Cazador",
                    prefixIcon: Icon(Icons.person_outline),
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) => v!.isEmpty ? "Requerido" : null,
                ).animate().fadeIn(delay: 200.ms),
                const SizedBox(height: 16),
                
                // Email
                TextFormField(
                  controller: _emailController,
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(
                    labelText: "Correo Electrónico",
                    prefixIcon: Icon(Icons.email_outlined),
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) => !v!.contains("@") ? "Email inválido" : null,
                ).animate().fadeIn(delay: 300.ms),
                const SizedBox(height: 16),
                
                // Password
                TextFormField(
                  controller: _passwordController,
                  obscureText: true,
                  style: const TextStyle(color: Colors.white),
                  decoration: const InputDecoration(
                    labelText: "Contraseña",
                    prefixIcon: Icon(Icons.lock_outline),
                    border: OutlineInputBorder(),
                  ),
                  validator: (v) => v!.length < 6 ? "Mínimo 6 caracteres" : null,
                ).animate().fadeIn(delay: 400.ms),
                const SizedBox(height: 32),

                ElevatedButton(
                  onPressed: authState.isLoading ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: authState.isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text("DESPERTAR", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ).animate().fadeIn(delay: 500.ms).scale(),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
