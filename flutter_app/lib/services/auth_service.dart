import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/user.dart';

/// Servis za avtentikacijo
class AuthService extends ChangeNotifier {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  AuthTokens? _tokens;
  User? _currentUser;
  bool _isLoading = false;

  bool get isAuthenticated => _tokens != null;
  bool get isLoading => _isLoading;
  User? get currentUser => _currentUser;
  String? get accessToken => _tokens?.accessToken;

  /// Prijava
  Future<bool> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final response = await http.post(
        Uri.parse('${AppConfig.apiBaseUrl}/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _tokens = AuthTokens.fromJson(data);

        // Shrani tokene
        await _storage.write(key: 'access_token', value: _tokens!.accessToken);
        await _storage.write(key: 'refresh_token', value: _tokens!.refreshToken);

        // Pridobi podatke o uporabniku
        await _fetchCurrentUser();

        _isLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Login error: $e');
    }

    _isLoading = false;
    notifyListeners();
    return false;
  }

  /// Odjava
  Future<void> logout() async {
    _tokens = null;
    _currentUser = null;

    await _storage.delete(key: 'access_token');
    await _storage.delete(key: 'refresh_token');

    notifyListeners();
  }

  /// Preveri ali je seja veljavna
  Future<bool> checkAuth() async {
    final accessToken = await _storage.read(key: 'access_token');
    final refreshToken = await _storage.read(key: 'refresh_token');

    if (accessToken == null || refreshToken == null) {
      return false;
    }

    _tokens = AuthTokens(
      accessToken: accessToken,
      refreshToken: refreshToken,
    );

    // Poskusi pridobiti podatke o uporabniku
    final success = await _fetchCurrentUser();

    if (!success) {
      // Token je potekel, poskusi osvežiti
      return await _refreshTokens();
    }

    return true;
  }

  /// Pridobi podatke o trenutnem uporabniku
  Future<bool> _fetchCurrentUser() async {
    if (_tokens == null) return false;

    try {
      final response = await http.get(
        Uri.parse('${AppConfig.apiBaseUrl}/auth/me'),
        headers: {
          'Authorization': 'Bearer ${_tokens!.accessToken}',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _currentUser = User.fromJson(data);
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Fetch user error: $e');
    }

    return false;
  }

  /// Osveži tokene
  Future<bool> _refreshTokens() async {
    if (_tokens == null) return false;

    try {
      final response = await http.post(
        Uri.parse('${AppConfig.apiBaseUrl}/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'refresh_token': _tokens!.refreshToken,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _tokens = AuthTokens.fromJson(data);

        await _storage.write(key: 'access_token', value: _tokens!.accessToken);
        await _storage.write(key: 'refresh_token', value: _tokens!.refreshToken);

        await _fetchCurrentUser();
        return true;
      }
    } catch (e) {
      debugPrint('Refresh token error: $e');
    }

    // Osvežitev ni uspela, odjavi
    await logout();
    return false;
  }

  /// Vrne veljavni token (osveži če potrebno)
  Future<String?> getValidToken() async {
    if (_tokens == null) return null;

    // Tukaj bi lahko preverili ali je token potekel
    // Za zdaj samo vrnemo trenutni token
    return _tokens!.accessToken;
  }
}
