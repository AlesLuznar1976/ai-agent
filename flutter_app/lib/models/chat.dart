/// Model chat sporočila
class ChatMessage {
  final String role; // 'user', 'agent', 'system'
  final String content;
  final DateTime timestamp;
  final int? projektId;
  final bool needsConfirmation;
  final List<Map<String, dynamic>>? actions;
  final List<String>? suggestedCommands;

  ChatMessage({
    required this.role,
    required this.content,
    required this.timestamp,
    this.projektId,
    this.needsConfirmation = false,
    this.actions,
    this.suggestedCommands,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      role: json['role'] ?? 'agent',
      content: json['content'] ?? json['response'] ?? '',
      timestamp: json['timestamp'] != null
          ? DateTime.parse(json['timestamp'])
          : DateTime.now(),
      projektId: json['projekt_id'],
      needsConfirmation: json['needs_confirmation'] ?? false,
      actions: json['actions'] != null
          ? List<Map<String, dynamic>>.from(json['actions'])
          : null,
      suggestedCommands: json['suggested_commands'] != null
          ? List<String>.from(json['suggested_commands'])
          : null,
    );
  }

  /// Ali je sporočilo od uporabnika
  bool get isUser => role == 'user';

  /// Ali je sporočilo od agenta
  bool get isAgent => role == 'agent';

  /// Ali je sistemsko sporočilo
  bool get isSystem => role == 'system';
}

/// Model čakajoče akcije
class PendingAction {
  final String id;
  final String tip;
  final String opis;
  final Map<String, dynamic> podatki;
  String status;

  PendingAction({
    required this.id,
    required this.tip,
    required this.opis,
    required this.podatki,
    this.status = 'Čaka',
  });

  factory PendingAction.fromJson(Map<String, dynamic> json) {
    return PendingAction(
      id: json['id'],
      tip: json['tip'],
      opis: json['opis'],
      podatki: Map<String, dynamic>.from(json['podatki'] ?? {}),
      status: json['status'] ?? 'Čaka',
    );
  }

  bool get isPending => status == 'Čaka';
}
