import 'package:flutter/material.dart';
import '../../../../core/constants/app_strings.dart';

class SessionErrorWidget extends StatelessWidget {
  final String error;
  final VoidCallback onRetry;

  const SessionErrorWidget({
    super.key,
    required this.error,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64, color: Colors.red, semanticLabel: 'Error de carga'),
          const SizedBox(height: 16),
          Text(
            'Error: $error',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: onRetry,
            child: const Text(AppStrings.retry),
          ),
        ],
      ),
    );
  }
}
