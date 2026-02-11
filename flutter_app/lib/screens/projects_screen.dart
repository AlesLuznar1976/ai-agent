import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

import '../config/brand_theme.dart';
import '../services/api_service.dart';
import '../models/projekt.dart';

class ProjectsScreen extends StatefulWidget {
  const ProjectsScreen({super.key});

  @override
  State<ProjectsScreen> createState() => _ProjectsScreenState();
}

class _ProjectsScreenState extends State<ProjectsScreen> {
  List<Projekt> _projekti = [];
  bool _isLoading = true;
  String? _selectedFaza;
  String? _error;

  final List<String> _faze = [
    'Vse',
    'RFQ',
    'Ponudba',
    'Naročilo',
    'Tehnologija',
    'Nabava',
    'Proizvodnja',
    'Dostava',
    'Zaključek',
  ];

  @override
  void initState() {
    super.initState();
    _loadProjekti();
  }

  Future<void> _loadProjekti() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = context.read<ApiService>();
      final projekti = await apiService.getProjekti(
        faza: _selectedFaza == 'Vse' ? null : _selectedFaza,
      );

      setState(() {
        _projekti = projekti;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Napaka pri nalaganju projektov';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: LuznarBrand.surface,
      child: Column(
        children: [
          // Filters
          Container(
            height: 52,
            padding: const EdgeInsets.symmetric(horizontal: 12),
            color: LuznarBrand.surfaceWhite,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: _faze.length,
              itemBuilder: (context, index) {
                final faza = _faze[index];
                final isSelected = (_selectedFaza ?? 'Vse') == faza;

                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 8),
                  child: FilterChip(
                    label: Text(
                      faza,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                        color: isSelected ? LuznarBrand.navy : LuznarBrand.textSecondary,
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
                      borderRadius: BorderRadius.circular(LuznarBrand.radiusXLarge),
                    ),
                    onSelected: (selected) {
                      setState(() {
                        _selectedFaza = selected ? faza : null;
                      });
                      _loadProjekti();
                    },
                  ),
                );
              },
            ),
          ),

          Divider(height: 1, color: LuznarBrand.navy.withValues(alpha: 0.06)),

          // Project list
          Expanded(
            child: _isLoading
                ? Center(
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
                                size: 48, color: LuznarBrand.error.withValues(alpha: 0.5)),
                            const SizedBox(height: 16),
                            Text(
                              _error!,
                              style: TextStyle(color: LuznarBrand.textSecondary),
                            ),
                            const SizedBox(height: 16),
                            OutlinedButton.icon(
                              onPressed: _loadProjekti,
                              icon: const Icon(Icons.refresh, size: 18),
                              label: const Text('Poskusi znova'),
                            ),
                          ],
                        ),
                      )
                    : _projekti.isEmpty
                        ? Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.folder_off_outlined,
                                    size: 48, color: LuznarBrand.textMuted),
                                const SizedBox(height: 16),
                                Text(
                                  'Ni projektov',
                                  style: TextStyle(color: LuznarBrand.textSecondary),
                                ),
                              ],
                            ),
                          )
                        : RefreshIndicator(
                            color: LuznarBrand.gold,
                            onRefresh: _loadProjekti,
                            child: ListView.builder(
                              padding: const EdgeInsets.all(12),
                              itemCount: _projekti.length,
                              itemBuilder: (context, index) {
                                return _buildProjektCard(_projekti[index]);
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }

  Widget _buildProjektCard(Projekt projekt) {
    Color fazaColor;
    try {
      fazaColor = Color(int.parse(projekt.fazaColor.replaceFirst('#', '0xFF')));
    } catch (_) {
      fazaColor = LuznarBrand.navy;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        onTap: () {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Odpiranje ${projekt.stevilkaProjekta}...')),
          );
        },
        borderRadius: BorderRadius.circular(LuznarBrand.radiusMedium),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                  // Project number
                  Text(
                    projekt.stevilkaProjekta,
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                      color: LuznarBrand.navy,
                    ),
                  ),
                  const Spacer(),
                  // Phase badge
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: fazaColor.withValues(alpha: 0.08),
                      borderRadius: BorderRadius.circular(LuznarBrand.radiusXLarge),
                    ),
                    child: Text(
                      projekt.faza,
                      style: TextStyle(
                        color: fazaColor,
                        fontWeight: FontWeight.w600,
                        fontSize: 11,
                        letterSpacing: 0.3,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // Name
              Text(
                projekt.naziv,
                style: const TextStyle(
                  fontSize: 14,
                  color: LuznarBrand.textPrimary,
                ),
              ),
              const SizedBox(height: 10),

              // Info row
              Row(
                children: [
                  Icon(Icons.calendar_today_outlined,
                      size: 13, color: LuznarBrand.textMuted),
                  const SizedBox(width: 4),
                  Text(
                    DateFormat('dd.MM.yyyy').format(projekt.datumRfq),
                    style: const TextStyle(
                      fontSize: 12,
                      color: LuznarBrand.textSecondary,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: projekt.status == 'Aktiven'
                          ? LuznarBrand.success
                          : LuznarBrand.textMuted,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    projekt.status,
                    style: const TextStyle(
                      fontSize: 12,
                      color: LuznarBrand.textSecondary,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
