/// Konfiguracija aplikacije
class AppConfig {
  // API naslovi - LAN IP deluje iz vseh platform (web, Android, iOS, Windows)
  static const String _serverHost = '192.168.0.66';
  static const int _serverPort = 8000;

  static String get apiBaseUrl => 'http://$_serverHost:$_serverPort/api';
  static String get wsBaseUrl => 'ws://$_serverHost:$_serverPort/ws';

  // App info
  static const String appName = 'AI Agent';
  static const String appVersion = '1.0.0';

  // Timeouts
  static const int httpTimeout = 30; // sekund
  static const int wsReconnectDelay = 5; // sekund
}
