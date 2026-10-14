class FactCheckCreated {
  FactCheckCreated(this.id);
  final String id;
}

class PipelineEvent {
  PipelineEvent(this.type, this.message);
  final String type;
  final String message;
}

class Dossier {
  Dossier(this.json);
  final Map<String, dynamic> json;

  String get status => json['status'] as String? ?? '';
  String get original => json['original_input'] as String? ?? '';
  Map<String, dynamic>? get verdict => json['verdict'] as Map<String, dynamic>?;
  Map<String, dynamic>? get claim => json['claim'] as Map<String, dynamic>?;
  List<dynamic> get evidence => json['evidence'] as List<dynamic>? ?? [];
  List<dynamic> get sources => json['sources'] as List<dynamic>? ?? [];
  Map<String, dynamic>? get graph => json['knowledge_graph'] as Map<String, dynamic>?;
}

class HistoryRow {
  HistoryRow(this.json);
  final Map<String, dynamic> json;
}

class Analytics {
  Analytics(this.json);
  final Map<String, dynamic> json;
}
