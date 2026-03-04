import 'package:flutter/material.dart';
import '../../features/practice/domain/entities/question.dart';

/// A widget that displays the content of a single question, including its text
/// and an optional image.
///
/// [question] The [Question] entity containing the question details to display.
class QuestionCard extends StatelessWidget {
  final Question question;

  const QuestionCard({super.key, required this.question});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (question.imageUrl != null)
          Semantics(
            label: 'Imagen de la pregunta',
            child: Container(
              margin: const EdgeInsets.only(bottom: 16),
              height: 200,
              width: double.infinity,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                image: DecorationImage(
                  image: NetworkImage(question.imageUrl!),
                  fit: BoxFit.contain,
                ),
              ),
            ),
          ),
        Text(
          question.text,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.bold,
            height: 1.4,
          ),
        ),
      ],
    );
  }
}
