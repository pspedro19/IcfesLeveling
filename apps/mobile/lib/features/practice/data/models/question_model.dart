import '../../domain/entities/question.dart';

class QuestionModel extends Question {
  QuestionModel({
    required super.id,
    required super.subjectId,
    required super.topicId,
    required super.text,
    super.imageUrl,
    required super.options,
    required super.correctAnswer,
    super.xpReward,
    required super.difficulty,
    super.topicName,
    super.subjectName,
    super.explanation,
    super.attemptType = AttemptType.newQuestion,
  });

  factory QuestionModel.fromJson(Map<String, dynamic> json) {
    return QuestionModel(
      id: json['id'],
      subjectId: json['subject_id'],
      topicId: json['topic_id'],
      text: json['pregunta_texto'] ?? json['text'] ?? '',
      imageUrl: json['pregunta_imagen'] ?? json['image_url'],
      options: [
        OptionModel.fromJson({'id': 'A', 'text': json['opcion_a_texto'], 'image_url': json['opcion_a_imagen']}),
        OptionModel.fromJson({'id': 'B', 'text': json['opcion_b_texto'], 'image_url': json['opcion_b_imagen']}),
        OptionModel.fromJson({'id': 'C', 'text': json['opcion_c_texto'], 'image_url': json['opcion_c_imagen']}),
        OptionModel.fromJson({'id': 'D', 'text': json['opcion_d_texto'], 'image_url': json['opcion_d_imagen']}),
      ],
      correctAnswer: json['respuesta_correcta'] ?? 'A',
      xpReward: json['puntos_xp'] ?? 10,
      difficulty: json['difficulty_rating']?.toString() ?? 'E',
      topicName: json['topic_name'],
      subjectName: json['subject_name'],
      explanation: json['explicacion_texto'] ?? json['explanation'],
      attemptType: _mapAttemptType(json['attempt_type']),
    );
  }

  static AttemptType _mapAttemptType(String? type) {
    switch (type) {
      case 'valid_review':
        return AttemptType.validReview;
      case 'invalid_repeat':
        return AttemptType.invalidRepeat;
      default:
        return AttemptType.newQuestion;
    }
  }
}

class OptionModel extends Option {
  OptionModel({
    required super.id,
    required super.text,
    super.imageUrl,
  });

  factory OptionModel.fromJson(Map<String, dynamic> json) {
    return OptionModel(
      id: json['id'],
      text: json['text'] ?? '',
      imageUrl: json['image_url'],
    );
  }
}
