import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';

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
    return Column(
      children: [
        // Filtri
        Container(
          height: 50,
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            itemCount: _faze.length,
            itemBuilder: (context, index) {
              final faza = _faze[index];
              final isSelected = (_selectedFaza ?? 'Vse') == faza;

              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
                child: FilterChip(
                  label: Text(faza),
                  selected: isSelected,
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

        const Divider(height: 1),

        // Seznam projektov
        Expanded(
          child: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _error != null
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.error_outline,
                              size: 48, color: Colors.red.shade300),
                          const SizedBox(height: 16),
                          Text(_error!),
                          const SizedBox(height: 16),
                          ElevatedButton(
                            onPressed: _loadProjekti,
                            child: const Text('Poskusi znova'),
                          ),
                        ],
                      ),
                    )
                  : _projekti.isEmpty
                      ? Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.folder_off,
                                  size: 48, color: Colors.grey.shade400),
                              const SizedBox(height: 16),
                              Text(
                                'Ni projektov',
                                style: TextStyle(color: Colors.grey.shade600),
                              ),
                            ],
                          ),
                        )
                      : RefreshIndicator(
                          onRefresh: _loadProjekti,
                          child: ListView.builder(
                            padding: const EdgeInsets.all(8),
                            itemCount: _projekti.length,
                            itemBuilder: (context, index) {
                              return _buildProjektCard(_projekti[index]);
                            },
                          ),
                        ),
        ),
      ],
    );
  }

  Widget _buildProjektCard(Projekt projekt) {
    final fazaColor = Color(int.parse(projekt.fazaColor.replaceFirst('#', '0xFF')));

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: () {
          // TODO: Odpri projekt detajl
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Odpiranje ${projekt.stevilkaProjekta}...')),
          );
        },
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Glava
              Row(
                children: [
                  // Številka projekta
                  Text(
                    projekt.stevilkaProjekta,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                  const Spacer(),
                  // Faza
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: fazaColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: fazaColor.withOpacity(0.5)),
                    ),
                    child: Text(
                      projekt.faza,
                      style: TextStyle(
                        color: fazaColor,
                        fontWeight: FontWeight.w500,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // Naziv
              Text(
                projekt.naziv,
                style: const TextStyle(fontSize: 15),
              ),
              const SizedBox(height: 8),

              // Info
              Row(
                children: [
                  Icon(Icons.calendar_today,
                      size: 14, color: Colors.grey.shade600),
                  const SizedBox(width: 4),
                  Text(
                    DateFormat('dd.MM.yyyy').format(projekt.datumRfq),
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade600,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Icon(Icons.circle,
                      size: 8,
                      color: projekt.status == 'Aktiven'
                          ? Colors.green
                          : Colors.grey),
                  const SizedBox(width: 4),
                  Text(
                    projekt.status,
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey.shade600,
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
