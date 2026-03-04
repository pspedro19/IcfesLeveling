import '../../../practice/data/models/question_model.dart';

class DeepDiagnosticSessionModel {
  final String diagnosticId;
  final String subjectId;
  final String subjectName;
  final List<QuestionModel> questions;
  final int total;

  DeepDiagnosticSessionModel({
    required this.diagnosticId,
    required this.subjectId,
    required this.subjectName,
    required this.questions,
    required this.total,
  });

  factory DeepDiagnosticSessionModel.fromJson(Map<String, dynamic> json) {
    var questionsList = json['questions'] as List;
    List<QuestionModel> questions = questionsList.map((i) => QuestionModel.fromJson(i)).toList();
    
    return DeepDiagnosticSessionModel(
      diagnosticId: json['diagnostic_id'],
      subjectId: json['subject_id'],
      subjectName: json['subject_name'],
      questions: questions,
      total: json['total'],
    );
  }
}

class DeepDiagnosticResultsModel {
  final bool completed;
  final String subjectId;
  final int correct;
  final int total;
  final List<SkillTreeTopicModel> skillTree;

  DeepDiagnosticResultsModel({
    required this.completed,
    required this.subjectId,
    required this.correct,
    required this.total,
    required this.skillTree,
  });

  factory DeepDiagnosticResultsModel.fromJson(Map<String, dynamic> json) {
    var skillTreeList = json['skill_tree'] as List;
    List<SkillTreeTopicModel> skillTree = skillTreeList.map((i) => SkillTreeTopicModel.fromJson(i)).toList();

    return DeepDiagnosticResultsModel(
      completed: json['completed'],
      subjectId: json['subject_id'],
      correct: json['correct'],
      total: json['total'],
      skillTree: skillTree,
    );
  }
}

class SkillTreeTopicModel {
  final String topicId;
  final String topicName;
  final double masteryScore;
  final String status;

  SkillTreeTopicModel({
    required this.topicId,
    required this.topicName,
    required this.masteryScore,
    required this.status,
  });

  factory SkillTreeTopicModel.fromJson(Map<String, dynamic> json) {
    return SkillTreeTopicModel(
      topicId: json['topic_id'],
      topicName: json['topic_name'],
      masteryScore: (json['mastery_score'] as num).toDouble(),
      status: json['status'],
    );
  }
}
