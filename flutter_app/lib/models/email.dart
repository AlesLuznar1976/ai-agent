/// Model emaila
class Email {
  final int id;
  final String? zadeva;
  final String? posiljatelj;
  final String? prejemniki;
  final String? kategorija;
  final String? status;
  final DateTime? datum;
  final String? analizaStatus;
  final Map<String, dynamic>? analizaRezultat;
  final List<dynamic>? priloge;
  final Map<String, dynamic>? izvleceniPodatki;

  Email({
    required this.id,
    this.zadeva,
    this.posiljatelj,
    this.prejemniki,
    this.kategorija,
    this.status,
    this.datum,
    this.analizaStatus,
    this.analizaRezultat,
    this.priloge,
    this.izvleceniPodatki,
  });

  factory Email.fromJson(Map<String, dynamic> json) {
    return Email(
      id: json['id'],
      zadeva: json['zadeva'],
      posiljatelj: json['posiljatelj'],
      prejemniki: json['prejemniki'],
      kategorija: json['kategorija'],
      status: json['status'],
      datum: json['datum'] != null ? DateTime.parse(json['datum']) : null,
      analizaStatus: json['analiza_status'],
      analizaRezultat: json['analiza_rezultat'] != null
          ? Map<String, dynamic>.from(json['analiza_rezultat'])
          : null,
      priloge: json['priloge'] != null
          ? List<dynamic>.from(json['priloge'])
          : null,
      izvleceniPodatki: json['izvleceni_podatki'] != null
          ? Map<String, dynamic>.from(json['izvleceni_podatki'])
          : null,
    );
  }

  /// Ali ima priloge
  bool get imaPriloge => priloge != null && priloge!.isNotEmpty;

  /// Število prilog
  int get steviloPrilog => priloge?.length ?? 0;
}
