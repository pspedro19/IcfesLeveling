import '../../data/models/boss_raid_models.dart';

enum AttemptType { newQuestion, validReview, invalidRepeat }

class Question {
  final String id;
  final String subjectId;
  final String topicId;
  final String text;
  final String? imageUrl;
  final List<Option> options;
  final String correctAnswer;
  final int xpReward;
  final String difficulty;
  final String? topicName;
  final String? subjectName;
  final String? explanation;
  final AttemptType attemptType;

  Question({
    required this.id,
    required this.subjectId,
    required this.topicId,
    required this.text,
    this.imageUrl,
    required this.options,
    required this.correctAnswer,
    this.xpReward = 10,
    required this.difficulty,
    this.topicName,
    this.subjectName,
    this.explanation,
    this.attemptType = AttemptType.newQuestion,
  });

  /// Factory constructor to create a Question from a RaidQuestionModel
  factory Question.fromModel(RaidQuestionModel model) {
    return Question(
      id: model.id,
      subjectId: 'raid', // Boss raid questions may not have subject
      topicId: 'raid',
      text: model.text,
      imageUrl: model.imageUrl,
      options: model.options
          .map((o) => Option(
                id: o.id,
                text: o.text ?? '',
                imageUrl: o.imageUrl,
              ))
          .toList(),
      correctAnswer: '', // Will be revealed by server after answer
      difficulty: 'medium',
    );
  }
}

class Option {
  final String id;
  final String text;
  final String? imageUrl;

  Option({
    required this.id,
    required this.text,
    this.imageUrl,
  });
}
