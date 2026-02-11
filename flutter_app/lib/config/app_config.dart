import 'package:flutter/foundation.dart' show kIsWeb;

/// Konfiguracija aplikacije
class AppConfig {
  // API naslovi - auto-detect glede na kje teče app
  // Če je web: isti host kot browser, port 8000
  // Če je native: localhost:8000
  static String get apiBaseUrl {
    if (kIsWeb) {
      // V brskalniku: uporabi isti host, port 8000
      return 'http://192.168.0.66:8000/api';
    }
    return 'http://192.168.0.66:8000/api';
  }

  static String get wsBaseUrl {
    if (kIsWeb) {
      return 'ws://192.168.0.66:8000/ws';
    }
    return 'ws://192.168.0.66:8000/ws';
  }

  // App info
  static const String appName = 'AI Agent';
  static const String appVersion = '1.0.0';

  // Timeouts
  static const int httpTimeout = 30; // sekund
  static const int wsReconnectDelay = 5; // sekund
}
