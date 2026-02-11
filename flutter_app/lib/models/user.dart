/// Model uporabnika
class User {
  final int id;
  final String username;
  final String role;
  final List<String> permissions;

  User({
    required this.id,
    required this.username,
    required this.role,
    required this.permissions,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['user_id'] ?? json['id'],
      username: json['username'],
      role: json['role'],
      permissions: List<String>.from(json['permissions'] ?? []),
    );
  }

  bool hasPermission(String permission) {
    return permissions.contains(permission);
  }
}

/// Token model
class AuthTokens {
  final String accessToken;
  final String refreshToken;
  final String tokenType;

  AuthTokens({
    required this.accessToken,
    required this.refreshToken,
    this.tokenType = 'bearer',
  });

  factory AuthTokens.fromJson(Map<String, dynamic> json) {
    return AuthTokens(
      accessToken: json['access_token'],
      refreshToken: json['refresh_token'],
      tokenType: json['token_type'] ?? 'bearer',
    );
  }
}
