import 'dart:convert';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/projekt.dart';
import '../models/chat.dart';
import '../models/email.dart';
import 'auth_service.dart';

/// Servis za API klice
class ApiService {
  final AuthService _authService;

  ApiService(this._authService);

  /// HTTP headers z avtentikacijo
  Future<Map<String, String>> get _headers async {
    final token = await _authService.getValidToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // ==================== CHAT ====================

  /// Pošlji sporočilo agentu
  Future<ChatMessage> sendMessage(String message, {int? projektId}) async {
    final response = await http.post(
      Uri.parse('${AppConfig.apiBaseUrl}/chat'),
      headers: await _headers,
      body: jsonEncode({
        'message': message,
        if (projektId != null) 'projekt_id': projektId,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return ChatMessage.fromJson({...data, 'role': 'agent'});
    }

    throw Exception('Napaka pri pošiljanju sporočila: ${response.statusCode}');
  }

  /// Pridobi zgodovino pogovora
  Future<List<ChatMessage>> getChatHistory({int? projektId}) async {
    final url = projektId != null
        ? '${AppConfig.apiBaseUrl}/chat/history/$projektId'
        : '${AppConfig.apiBaseUrl}/chat/history';

    final response = await http.get(
      Uri.parse(url),
      headers: await _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final history = data['history'] as List;
      return history.map((m) => ChatMessage.fromJson(m)).toList();
    }

    throw Exception('Napaka pri pridobivanju zgodovine');
  }

  /// Potrdi akcijo
  Future<void> confirmAction(String actionId) async {
    final response = await http.post(
      Uri.parse('${AppConfig.apiBaseUrl}/chat/actions/$actionId/confirm'),
      headers: await _headers,
    );

    if (response.statusCode != 200) {
      throw Exception('Napaka pri potrjevanju akcije');
    }
  }

  /// Zavrni akcijo
  Future<void> rejectAction(String actionId) async {
    final response = await http.post(
      Uri.parse('${AppConfig.apiBaseUrl}/chat/actions/$actionId/reject'),
      headers: await _headers,
    );

    if (response.statusCode != 200) {
      throw Exception('Napaka pri zavračanju akcije');
    }
  }

  // ==================== PROJEKTI ====================

  /// Seznam projektov
  Future<List<Projekt>> getProjekti({
    String? faza,
    String? status,
    String? search,
  }) async {
    var url = '${AppConfig.apiBaseUrl}/projekti?';

    if (faza != null) url += 'faza=$faza&';
    if (status != null) url += 'status=$status&';
    if (search != null) url += 'search=$search&';

    final response = await http.get(
      Uri.parse(url),
      headers: await _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final projekti = data['projekti'] as List;
      return projekti.map((p) => Projekt.fromJson(p)).toList();
    }

    throw Exception('Napaka pri pridobivanju projektov');
  }

  /// Pridobi projekt
  Future<Projekt> getProjekt(int id) async {
    final response = await http.get(
      Uri.parse('${AppConfig.apiBaseUrl}/projekti/$id'),
      headers: await _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return Projekt.fromJson(data);
    }

    throw Exception('Projekt ne obstaja');
  }

  /// Časovnica projekta
  Future<List<ProjektCasovnica>> getProjektCasovnica(int projektId) async {
    final response = await http.get(
      Uri.parse('${AppConfig.apiBaseUrl}/projekti/$projektId/casovnica'),
      headers: await _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final casovnica = data['casovnica'] as List;
      return casovnica.map((c) => ProjektCasovnica.fromJson(c)).toList();
    }

    throw Exception('Napaka pri pridobivanju časovnice');
  }

  // ==================== EMAILI ====================

  /// Seznam emailov
  Future<List<Email>> getEmaili({
    String? kategorija,
    String? analizaStatus,
  }) async {
    var url = '${AppConfig.apiBaseUrl}/emaili?';

    if (kategorija != null) url += 'kategorija=$kategorija&';

    final response = await http.get(
      Uri.parse(url),
      headers: await _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final emaili = data['emaili'] as List;
      var result = emaili.map((e) => Email.fromJson(e)).toList();

      // Filter locally by analiza_status (backend may not support this filter)
      if (analizaStatus != null) {
        result = result
            .where((e) => (e.analizaStatus ?? 'Brez') == analizaStatus)
            .toList();
      }

      return result;
    }

    throw Exception('Napaka pri pridobivanju emailov');
  }

  /// Pridobi analizo emaila
  Future<Map<String, dynamic>> getEmailAnalysis(int emailId) async {
    final response = await http.get(
      Uri.parse('${AppConfig.apiBaseUrl}/emaili/$emailId/analysis'),
      headers: await _headers,
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }

    throw Exception('Napaka pri pridobivanju analize');
  }

  /// Sproži analizo emaila
  Future<Map<String, dynamic>> triggerAnalysis(int emailId) async {
    final response = await http.post(
      Uri.parse('${AppConfig.apiBaseUrl}/emaili/$emailId/analyze'),
      headers: await _headers,
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }

    throw Exception('Napaka pri sprožanju analize: ${response.statusCode}');
  }

  // ==================== HEALTH ====================

  /// Preveri zdravje API-ja
  Future<bool> healthCheck() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConfig.apiBaseUrl.replaceAll('/api', '')}/health'),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
