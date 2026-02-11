/// Model projekta
class Projekt {
  final int id;
  final String stevilkaProjekta;
  final String naziv;
  final int? strankaId;
  final String faza;
  final String status;
  final DateTime datumRfq;
  final DateTime? datumZakljucka;
  final String? opombe;

  Projekt({
    required this.id,
    required this.stevilkaProjekta,
    required this.naziv,
    this.strankaId,
    required this.faza,
    required this.status,
    required this.datumRfq,
    this.datumZakljucka,
    this.opombe,
  });

  factory Projekt.fromJson(Map<String, dynamic> json) {
    return Projekt(
      id: json['id'],
      stevilkaProjekta: json['stevilka_projekta'],
      naziv: json['naziv'],
      strankaId: json['stranka_id'],
      faza: json['faza'],
      status: json['status'],
      datumRfq: DateTime.parse(json['datum_rfq']),
      datumZakljucka: json['datum_zakljucka'] != null
          ? DateTime.parse(json['datum_zakljucka'])
          : null,
      opombe: json['opombe'],
    );
  }

  /// Vrne barvo glede na fazo
  String get fazaColor {
    switch (faza) {
      case 'RFQ':
        return '#3B82F6'; // blue
      case 'Ponudba':
        return '#8B5CF6'; // purple
      case 'Naročilo':
        return '#10B981'; // green
      case 'Tehnologija':
        return '#F59E0B'; // amber
      case 'Nabava':
        return '#EF4444'; // red
      case 'Proizvodnja':
        return '#06B6D4'; // cyan
      case 'Dostava':
        return '#84CC16'; // lime
      case 'Zaključek':
        return '#6B7280'; // gray
      default:
        return '#6B7280';
    }
  }
}

/// Model časovnice
class ProjektCasovnica {
  final int id;
  final int projektId;
  final String dogodek;
  final String opis;
  final String? staraVrednost;
  final String? novaVrednost;
  final DateTime datum;
  final String uporabnikAliAgent;

  ProjektCasovnica({
    required this.id,
    required this.projektId,
    required this.dogodek,
    required this.opis,
    this.staraVrednost,
    this.novaVrednost,
    required this.datum,
    required this.uporabnikAliAgent,
  });

  factory ProjektCasovnica.fromJson(Map<String, dynamic> json) {
    return ProjektCasovnica(
      id: json['id'],
      projektId: json['projekt_id'],
      dogodek: json['dogodek'],
      opis: json['opis'],
      staraVrednost: json['stara_vrednost'],
      novaVrednost: json['nova_vrednost'],
      datum: DateTime.parse(json['datum']),
      uporabnikAliAgent: json['uporabnik_ali_agent'],
    );
  }
}
