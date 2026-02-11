/// Konfiguracija aplikacije
class AppConfig {
  // API naslovi
  static const String apiBaseUrl = 'http://localhost:8000/api';
  static const String wsBaseUrl = 'ws://localhost:8000/ws';

  // Za produkcijo
  // static const String apiBaseUrl = 'https://ai-agent.luznar.local/api';
  // static const String wsBaseUrl = 'wss://ai-agent.luznar.local/ws';

  // App info
  static const String appName = 'AI Agent';
  static const String appVersion = '1.0.0';

  // Timeouts
  static const int httpTimeout = 30; // sekund
  static const int wsReconnectDelay = 5; // sekund
}
