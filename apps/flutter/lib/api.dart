import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'models.dart';

class TruthLensApi {
  TruthLensApi([this.baseUrl = 'http://localhost:8080']);
  final String baseUrl;

  Future<FactCheckCreated> verifyClaim(String claim) async {
    final res = await http.post(
      Uri.parse('$baseUrl/v1/fact-checks'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'claim': claim}),
    );
    if (res.statusCode >= 400) {
      throw Exception(res.body);
    }
    return FactCheckCreated(jsonDecode(res.body)['fact_check_id'] as String);
  }

  Future<FactCheckCreated> verifyScreenshot(List<int> bytes, String filename) async {
    final req = http.MultipartRequest('POST', Uri.parse('$baseUrl/v1/fact-checks/screenshot'));
    req.files.add(http.MultipartFile.fromBytes('image', bytes, filename: filename));
    final streamed = await req.send();
    final body = await streamed.stream.bytesToString();
    if (streamed.statusCode >= 400) {
      throw Exception(body);
    }
    return FactCheckCreated(jsonDecode(body)['fact_check_id'] as String);
  }

  Stream<PipelineEvent> events(String id) async* {
    final req = http.Request('GET', Uri.parse('$baseUrl/v1/fact-checks/$id/events'));
    final res = await req.send();
    String type = 'message';
    await for (final chunk in res.stream.transform(utf8.decoder)) {
      for (final line in chunk.split('\n')) {
        if (line.startsWith('event: ')) {
          type = line.substring(7).trim();
        } else if (line.startsWith('data: ')) {
          final data = jsonDecode(line.substring(6));
          yield PipelineEvent(type, data['message'] as String? ?? type);
        }
      }
    }
  }

  Future<Dossier> dossier(String id) async {
    final res = await http.get(Uri.parse('$baseUrl/v1/fact-checks/$id'));
    return Dossier(jsonDecode(res.body) as Map<String, dynamic>);
  }

  Future<List<HistoryRow>> history() async {
    final res = await http.get(Uri.parse('$baseUrl/v1/fact-checks'));
    final list = jsonDecode(res.body) as List<dynamic>;
    return list.map((e) => HistoryRow(e as Map<String, dynamic>)).toList();
  }

  Future<Analytics> analytics() async {
    final res = await http.get(Uri.parse('$baseUrl/v1/analytics/summary'));
    return Analytics(jsonDecode(res.body) as Map<String, dynamic>);
  }
}
