import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../config/brand_theme.dart';
import '../services/api_service.dart';
import '../models/email.dart';
import 'email_detail_screen.dart';

class EmailiScreen extends StatefulWidget {
  const EmailiScreen({super.key});

  @override
  State<EmailiScreen> createState() => _EmailiScreenState();
}

class _EmailiScreenState extends State<EmailiScreen> {
  List<Email> _vsiEmaili = [];
  List<Email> _emaili = [];
  bool _isLoading = true;
  String? _selectedStatus;
  String? _selectedMailbox;
  String? _error;

  final List<String> _statusi = [
    'Vse',
    'Končano',
    'Čaka',
    'V obdelavi',
    'Napaka',
    'Brez',
  ];

  final List<String> _predali = [
    'Vsi',
    'ales',
    'info',
    'spela',
    'nabava',
    'tehnolog',
    'martina',
    'oddaja',
    'anela',
    'cam',
    'matej',
    'prevzem',
    'skladisce',
  ];

  @override
  void initState() {
    super.initState();
    _loadEmaili();
  }

  Future<void> _loadEmaili() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = context.read<ApiService>();
      final emaili = await apiService.getEmaili();

      setState(() {
        _vsiEmaili = emaili;
        _applyFilters();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Napaka pri nalaganju emailov';
        _isLoading = false;
      });
    }
  }

  void _applyFilters() {
    var filtered = _vsiEmaili;

    // Filter by analiza status
    final status = _selectedStatus;
    if (status != null && status != 'Vse') {
      filtered = filtered
          .where((e) => (e.analizaStatus ?? 'Brez') == status)
          .toList();
    }

    // Filter by mailbox
    final mailbox = _selectedMailbox;
    if (mailbox != null && mailbox != 'Vsi') {
      filtered = filtered.where((e) {
        final m = e.izvleceniPodatki?['mailbox'];
        return m != null && m.toString() == mailbox;
      }).toList();
    }

    _emaili = filtered;
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

  String _statusLabel(String? status) {
    return status ?? 'Brez';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: LuznarBrand.surface,
      child: Column(
        children: [
          // Filter bar
          Container(
            height: 52,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            color: LuznarBrand.surfaceWhite,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _statusi.length,
              itemBuilder: (context, index) {
                final status = _statusi[index];
                final isSelected = (_selectedStatus ?? 'Vse') == status;

                return Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 3, vertical: 8),
                  child: FilterChip(
                    label: Text(
                      status,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight:
                            isSelected ? FontWeight.w600 : FontWeight.w400,
                        color: isSelected
                            ? LuznarBrand.navy
                            : LuznarBrand.textSecondary,
                      ),
                    ),
                    selected: isSelected,
                    selectedColor: LuznarBrand.navy.withValues(alpha: 0.1),
                    backgroundColor: LuznarBrand.surfaceWhite,
                    checkmarkColor: LuznarBrand.navy,
                    side: BorderSide(
                      color: isSelected
                          ? LuznarBrand.navy.withValues(alpha: 0.3)
                          : LuznarBrand.navy.withValues(alpha: 0.1),
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius:
                          BorderRadius.circular(LuznarBrand.radiusXLarge),
                    ),
                    onSelected: (selected) {
                      setState(() {
                        _selectedStatus = selected ? status : null;
                        _applyFilters();
                      });
                    },
                  ),
                );
              },
            ),
          ),

          Divider(height: 1, color: LuznarBrand.navy.withValues(alpha: 0.06)),

          // Mailbox filter bar
          Container(
            height: 52,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            color: LuznarBrand.surfaceWhite,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _predali.length,
              itemBuilder: (context, index) {
                final predal = _predali[index];
                final isSelected = (_selectedMailbox ?? 'Vsi') == predal;

                return Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 3, vertical: 8),
                  child: FilterChip(
                    avatar: predal != 'Vsi'
                        ? Icon(Icons.inbox_outlined,
                            size: 14,
                            color: isSelected
                                ? LuznarBrand.gold
                                : LuznarBrand.textMuted)
                        : null,
                    label: Text(
                      predal,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight:
                            isSelected ? FontWeight.w600 : FontWeight.w400,
                        color: isSelected
                            ? LuznarBrand.navy
                            : LuznarBrand.textSecondary,
                      ),
                    ),
                    selected: isSelected,
                    selectedColor: LuznarBrand.gold.withValues(alpha: 0.1),
                    backgroundColor: LuznarBrand.surfaceWhite,
                    checkmarkColor: LuznarBrand.gold,
                    side: BorderSide(
                      color: isSelected
                          ? LuznarBrand.gold.withValues(alpha: 0.3)
                          : LuznarBrand.navy.withValues(alpha: 0.1),
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius:
                          BorderRadius.circular(LuznarBrand.radiusXLarge),
                    ),
                    onSelected: (selected) {
                      setState(() {
                        _selectedMailbox = selected ? predal : null;
                        _applyFilters();
                      });
                    },
                  ),
                );
              },
            ),
          ),

          Divider(height: 1, color: LuznarBrand.navy.withValues(alpha: 0.06)),

          // Email list
          Expanded(
            child: _isLoading
                ? const Center(
                    child: CircularProgressIndicator(
                      color: LuznarBrand.gold,
                      strokeWidth: 2,
                    ),
                  )
                : _error != null
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.error_outline,
                                size: 48,
                                color:
                                    LuznarBrand.error.withValues(alpha: 0.5)),
                            const SizedBox(height: 16),
                            Text(
                              _error!,
                              style: const TextStyle(
                                  color: LuznarBrand.textSecondary),
                            ),
                            const SizedBox(height: 16),
                            OutlinedButton.icon(
                              onPressed: _loadEmaili,
                              icon: const Icon(Icons.refresh, size: 18),
                              label: const Text('Poskusi znova'),
                            ),
                          ],
                        ),
                      )
                    : _emaili.isEmpty
                        ? Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.email_outlined,
                                    size: 48, color: LuznarBrand.textMuted),
                                const SizedBox(height: 16),
                                const Text(
                                  'Ni emailov',
                                  style: TextStyle(
                                      color: LuznarBrand.textSecondary),
                                ),
                              ],
                            ),
                          )
                        : RefreshIndicator(
                            color: LuznarBrand.gold,
                            onRefresh: _loadEmaili,
                            child: ListView.builder(
                              padding: const EdgeInsets.all(12),
                              itemCount: _emaili.length,
                              itemBuilder: (context, index) {
                                return _buildEmailCard(_emaili[index]);
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmailCard(Email email) {
    final statusColor = _statusColor(email.analizaStatus);
    final statusLabel = _statusLabel(email.analizaStatus);

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => EmailDetailScreen(email: email),
            ),
          ).then((_) => _loadEmaili());
        },
        borderRadius: BorderRadius.circular(LuznarBrand.radiusMedium),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header: zadeva + status badge
              Row(
                children: [
                  Expanded(
                    child: Text(
                      email.zadeva ?? '(brez zadeve)',
                      style: const TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                        color: LuznarBrand.navy,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 3,
                    ),
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
                        fontSize: 11,
                        letterSpacing: 0.3,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),

              // Pošiljatelj
              Text(
                email.posiljatelj ?? '',
                style: const TextStyle(
                  fontSize: 12,
                  color: LuznarBrand.textSecondary,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 10),

              // Footer: datum + kategorija + priloge
              Row(
                children: [
                  if (email.datum != null) ...[
                    Icon(Icons.calendar_today_outlined,
                        size: 13, color: LuznarBrand.textMuted),
                    const SizedBox(width: 4),
                    Text(
                      DateFormat('dd.MM.yyyy').format(email.datum!),
                      style: const TextStyle(
                        fontSize: 12,
                        color: LuznarBrand.textSecondary,
                      ),
                    ),
                  ],
                  if (email.kategorija != null) ...[
                    const SizedBox(width: 12),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: LuznarBrand.navy.withValues(alpha: 0.06),
                        borderRadius:
                            BorderRadius.circular(LuznarBrand.radiusXLarge),
                      ),
                      child: Text(
                        email.kategorija!,
                        style: const TextStyle(
                          fontSize: 11,
                          color: LuznarBrand.textSecondary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                  const Spacer(),
                  if (email.imaPriloge) ...[
                    Icon(Icons.attach_file,
                        size: 15, color: LuznarBrand.textMuted),
                    const SizedBox(width: 2),
                    Text(
                      '${email.steviloPrilog}',
                      style: const TextStyle(
                        fontSize: 12,
                        color: LuznarBrand.textMuted,
                      ),
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
