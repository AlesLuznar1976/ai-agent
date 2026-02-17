import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../config/brand_theme.dart';
import '../services/api_service.dart';
import '../models/email.dart';

class EmailDetailScreen extends StatefulWidget {
  final Email email;

  const EmailDetailScreen({super.key, required this.email});

  @override
  State<EmailDetailScreen> createState() => _EmailDetailScreenState();
}

class _EmailDetailScreenState extends State<EmailDetailScreen> {
  late Email _email;
  bool _isAnalyzing = false;

  @override
  void initState() {
    super.initState();
    _email = widget.email;
    // Fetch fresh analysis data if status is Končano
    if (_email.analizaStatus == 'Končano' && _email.analizaRezultat == null) {
      _loadAnalysis();
    }
  }

  Future<void> _loadAnalysis() async {
    try {
      final apiService = context.read<ApiService>();
      final data = await apiService.getEmailAnalysis(_email.id);
      setState(() {
        _email = Email(
          id: _email.id,
          zadeva: _email.zadeva,
          posiljatelj: _email.posiljatelj,
          prejemniki: _email.prejemniki,
          kategorija: _email.kategorija,
          rfqPodkategorija: _email.rfqPodkategorija,
          status: _email.status,
          datum: _email.datum,
          analizaStatus: data['analiza_status'] ?? _email.analizaStatus,
          analizaRezultat: data['analiza_rezultat'] != null
              ? Map<String, dynamic>.from(data['analiza_rezultat'])
              : _email.analizaRezultat,
          priloge: _email.priloge,
          izvleceniPodatki: _email.izvleceniPodatki,
        );
      });
    } catch (_) {
      // Silently fail - we still have the list data
    }
  }

  Future<void> _triggerAnalysis() async {
    setState(() => _isAnalyzing = true);

    try {
      final apiService = context.read<ApiService>();
      final data = await apiService.triggerAnalysis(_email.id);

      setState(() {
        _email = Email(
          id: _email.id,
          zadeva: _email.zadeva,
          posiljatelj: _email.posiljatelj,
          prejemniki: _email.prejemniki,
          kategorija: _email.kategorija,
          rfqPodkategorija: _email.rfqPodkategorija,
          status: _email.status,
          datum: _email.datum,
          analizaStatus: data['analiza_status'] ?? 'Končano',
          analizaRezultat: data['analiza_rezultat'] != null
              ? Map<String, dynamic>.from(data['analiza_rezultat'])
              : null,
          priloge: _email.priloge,
          izvleceniPodatki: _email.izvleceniPodatki,
        );
        _isAnalyzing = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Analiza uspešna')),
        );
      }
    } catch (e) {
      setState(() => _isAnalyzing = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Napaka: $e')),
        );
      }
    }
  }

  Color _statusColor(String? status) {
    switch (status) {
      case 'Končano':
        return LuznarBrand.success;
      case 'Čaka':
        return LuznarBrand.info;
      case 'V obdelavi':
        return LuznarBrand.warning;
      case 'Napaka':
        return LuznarBrand.error;
      default:
        return LuznarBrand.textMuted;
    }
  }

  Color _rfqPodkategorijaColor(String? podkat) {
    switch (podkat) {
      case 'Kompletno':
        return LuznarBrand.success;
      case 'Nepopolno':
        return LuznarBrand.warning;
      case 'Povpraševanje':
        return LuznarBrand.info;
      case 'Repeat Order':
        return const Color(0xFF7C3AED); // vijolična
      default:
        return LuznarBrand.textMuted;
    }
  }

  Color _prioritetaColor(String? prioriteta) {
    switch (prioriteta) {
      case 'Visoka':
        return LuznarBrand.error;
      case 'Srednja':
        return LuznarBrand.warning;
      case 'Nizka':
        return LuznarBrand.success;
      default:
        return LuznarBrand.textMuted;
    }
  }

  @override
  Widget build(BuildContext context) {
    final rezultat = _email.analizaRezultat;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: LuznarBrand.navy,
        title: Text(
          _email.zadeva ?? '(brez zadeve)',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header card
            _buildHeaderCard(),

            // Analysis sections
            if (rezultat != null) ...[
              if (rezultat['stranka'] != null) _buildStrankaCard(rezultat['stranka']),
              if (rezultat['izdelki'] != null) _buildIzdelkiCard(rezultat['izdelki']),
              if (rezultat['prilozeni_dokumenti'] != null)
                _buildDokumentiCard(rezultat['prilozeni_dokumenti']),
              _buildPodanoManjkajoceCard(
                rezultat['podano_od_stranke'],
                rezultat['manjkajoci_podatki'],
              ),
              _buildPovzetekCard(rezultat),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildHeaderCard() {
    final statusColor = _statusColor(_email.analizaStatus);
    final statusLabel = _email.analizaStatus ?? 'Brez';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Pošiljatelj
            Row(
              children: [
                const Icon(Icons.person_outline,
                    size: 16, color: LuznarBrand.textMuted),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    _email.posiljatelj ?? '',
                    style: const TextStyle(
                      fontSize: 14,
                      color: LuznarBrand.textPrimary,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),

            // Datum
            if (_email.datum != null)
              Row(
                children: [
                  const Icon(Icons.calendar_today_outlined,
                      size: 16, color: LuznarBrand.textMuted),
                  const SizedBox(width: 6),
                  Text(
                    DateFormat('dd.MM.yyyy HH:mm').format(_email.datum!),
                    style: const TextStyle(
                      fontSize: 13,
                      color: LuznarBrand.textSecondary,
                    ),
                  ),
                ],
              ),
            const SizedBox(height: 8),

            // Kategorija + Pod-kategorija + Status
            Row(
              children: [
                if (_email.kategorija != null) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: LuznarBrand.navy.withValues(alpha: 0.06),
                      borderRadius:
                          BorderRadius.circular(LuznarBrand.radiusXLarge),
                    ),
                    child: Text(
                      _email.kategorija!,
                      style: const TextStyle(
                        fontSize: 12,
                        color: LuznarBrand.textSecondary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
                if (_email.rfqPodkategorija != null) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: _rfqPodkategorijaColor(_email.rfqPodkategorija)
                          .withValues(alpha: 0.08),
                      borderRadius:
                          BorderRadius.circular(LuznarBrand.radiusXLarge),
                    ),
                    child: Text(
                      _email.rfqPodkategorija!,
                      style: TextStyle(
                        color: _rfqPodkategorijaColor(
                            _email.rfqPodkategorija),
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor.withValues(alpha: 0.08),
                    borderRadius:
                        BorderRadius.circular(LuznarBrand.radiusXLarge),
                  ),
                  child: Text(
                    statusLabel,
                    style: TextStyle(
                      color: statusColor,
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                ),
                const Spacer(),
                if (_email.imaPriloge)
                  Row(
                    children: [
                      const Icon(Icons.attach_file,
                          size: 15, color: LuznarBrand.textMuted),
                      const SizedBox(width: 2),
                      Text(
                        '${_email.steviloPrilog} prilog',
                        style: const TextStyle(
                          fontSize: 12,
                          color: LuznarBrand.textMuted,
                        ),
                      ),
                    ],
                  ),
              ],
            ),

            // Analyze button
            if (_email.analizaStatus != 'Končano') ...[
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isAnalyzing ? null : _triggerAnalysis,
                  icon: _isAnalyzing
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.analytics_outlined, size: 18),
                  label: Text(_isAnalyzing ? 'Analiziranje...' : 'Analiziraj'),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 18, color: LuznarBrand.navy),
          const SizedBox(width: 6),
          Text(
            title,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: LuznarBrand.navy,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStrankaCard(Map<String, dynamic> stranka) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionTitle('Stranka', Icons.business),
            if (stranka['ime'] != null)
              _buildInfoRow('Ime', stranka['ime'].toString()),
            if (stranka['kontakt'] != null)
              _buildInfoRow('Kontakt', stranka['kontakt'].toString()),
            if (stranka['email'] != null)
              _buildInfoRow('Email', stranka['email'].toString()),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 13,
                color: LuznarBrand.textMuted,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 13,
                color: LuznarBrand.textPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildIzdelkiCard(List<dynamic> izdelki) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionTitle('Izdelki', Icons.inventory_2_outlined),
            ...izdelki.asMap().entries.map((entry) {
              final i = entry.key;
              final izdelek = entry.value as Map<String, dynamic>;
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (i > 0)
                    Divider(
                        height: 20,
                        color: LuznarBrand.navy.withValues(alpha: 0.06)),
                  if (izdelek['naziv'] != null)
                    Text(
                      izdelek['naziv'].toString(),
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                        color: LuznarBrand.navy,
                      ),
                    ),
                  const SizedBox(height: 4),
                  if (izdelek['kolicina'] != null)
                    _buildInfoRow('Količina', izdelek['kolicina'].toString()),
                  if (izdelek['specifikacije'] != null &&
                      izdelek['specifikacije'] is Map)
                    ...(izdelek['specifikacije'] as Map<String, dynamic>)
                        .entries
                        .map(
                          (spec) =>
                              _buildInfoRow(spec.key, spec.value.toString()),
                        ),
                ],
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildDokumentiCard(List<dynamic> dokumenti) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionTitle('Dokumenti', Icons.description_outlined),
            ...dokumenti.map((doc) {
              final dokument = doc as Map<String, dynamic>;
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.insert_drive_file_outlined,
                        size: 16, color: LuznarBrand.textMuted),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Flexible(
                                child: Text(
                                  dokument['ime']?.toString() ?? '',
                                  style: const TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                    color: LuznarBrand.textPrimary,
                                  ),
                                ),
                              ),
                              if (dokument['tip'] != null) ...[
                                const SizedBox(width: 8),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 6, vertical: 1),
                                  decoration: BoxDecoration(
                                    color: LuznarBrand.info
                                        .withValues(alpha: 0.08),
                                    borderRadius: BorderRadius.circular(
                                        LuznarBrand.radiusXLarge),
                                  ),
                                  child: Text(
                                    dokument['tip'].toString(),
                                    style: const TextStyle(
                                      fontSize: 10,
                                      color: LuznarBrand.info,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                              ],
                            ],
                          ),
                          if (dokument['vsebina_povzetek'] != null) ...[
                            const SizedBox(height: 2),
                            Text(
                              dokument['vsebina_povzetek'].toString(),
                              style: const TextStyle(
                                fontSize: 12,
                                color: LuznarBrand.textSecondary,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildPodanoManjkajoceCard(
    List<dynamic>? podano,
    List<dynamic>? manjkajoce,
  ) {
    if ((podano == null || podano.isEmpty) &&
        (manjkajoce == null || manjkajoce.isEmpty)) {
      return const SizedBox.shrink();
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionTitle('Podano vs Manjkajoče', Icons.checklist),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Podano
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Podano',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: LuznarBrand.success,
                        ),
                      ),
                      const SizedBox(height: 6),
                      if (podano != null)
                        ...podano.map(
                          (item) => Padding(
                            padding: const EdgeInsets.only(bottom: 4),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Icon(Icons.check_circle,
                                    size: 14, color: LuznarBrand.success),
                                const SizedBox(width: 4),
                                Expanded(
                                  child: Text(
                                    item.toString(),
                                    style: const TextStyle(
                                      fontSize: 12,
                                      color: LuznarBrand.textPrimary,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                // Manjkajoče
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Manjkajoče',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: LuznarBrand.error,
                        ),
                      ),
                      const SizedBox(height: 6),
                      if (manjkajoce != null)
                        ...manjkajoce.map(
                          (item) => Padding(
                            padding: const EdgeInsets.only(bottom: 4),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Icon(Icons.cancel,
                                    size: 14, color: LuznarBrand.error),
                                const SizedBox(width: 4),
                                Expanded(
                                  child: Text(
                                    item.toString(),
                                    style: const TextStyle(
                                      fontSize: 12,
                                      color: LuznarBrand.textPrimary,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPovzetekCard(Map<String, dynamic> rezultat) {
    final povzetek = rezultat['povzetek'];
    final prioriteta = rezultat['prioriteta']?.toString();
    final koraki = rezultat['priporoceni_naslednji_koraki'] as List<dynamic>?;

    if (povzetek == null && prioriteta == null && (koraki == null || koraki.isEmpty)) {
      return const SizedBox.shrink();
    }

    final prioritetaColor = _prioritetaColor(prioriteta);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSectionTitle('Povzetek', Icons.summarize_outlined),

            if (povzetek != null) ...[
              Text(
                povzetek.toString(),
                style: const TextStyle(
                  fontSize: 13,
                  color: LuznarBrand.textPrimary,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 10),
            ],

            if (prioriteta != null)
              Row(
                children: [
                  const Text(
                    'Prioriteta: ',
                    style: TextStyle(
                      fontSize: 13,
                      color: LuznarBrand.textSecondary,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                    decoration: BoxDecoration(
                      color: prioritetaColor.withValues(alpha: 0.08),
                      borderRadius:
                          BorderRadius.circular(LuznarBrand.radiusXLarge),
                    ),
                    child: Text(
                      prioriteta,
                      style: TextStyle(
                        color: prioritetaColor,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),

            if (koraki != null && koraki.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text(
                'Priporočeni naslednji koraki:',
                style: TextStyle(
                  fontSize: 13,
                  color: LuznarBrand.textSecondary,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 6),
              ...koraki.asMap().entries.map(
                    (entry) => Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SizedBox(
                            width: 22,
                            child: Text(
                              '${entry.key + 1}.',
                              style: const TextStyle(
                                fontSize: 13,
                                color: LuznarBrand.navy,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          Expanded(
                            child: Text(
                              entry.value.toString(),
                              style: const TextStyle(
                                fontSize: 13,
                                color: LuznarBrand.textPrimary,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
            ],
          ],
        ),
      ),
    );
  }
}
