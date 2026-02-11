import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../services/auth_service.dart';
import 'chat_screen.dart';
import 'projects_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  final List<Widget> _screens = const [
    ChatScreen(),
    ProjectsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final authService = context.watch<AuthService>();
    final user = authService.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.smart_toy, size: 28),
            const SizedBox(width: 8),
            const Text('AI Agent'),
          ],
        ),
        actions: [
          // Uporabnik info
          if (user != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Center(
                child: Chip(
                  avatar: const Icon(Icons.person, size: 18),
                  label: Text(user.username),
                  backgroundColor: Colors.white.withOpacity(0.2),
                  labelStyle: const TextStyle(color: Colors.white),
                ),
              ),
            ),

          // Odjava
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Odjava',
            onPressed: () async {
              final confirm = await showDialog<bool>(
                context: context,
                builder: (context) => AlertDialog(
                  title: const Text('Odjava'),
                  content: const Text('Ali se želite odjaviti?'),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context, false),
                      child: const Text('Prekliči'),
                    ),
                    ElevatedButton(
                      onPressed: () => Navigator.pop(context, true),
                      child: const Text('Odjava'),
                    ),
                  ],
                ),
              );

              if (confirm == true) {
                await authService.logout();
              }
            },
          ),
        ],
      ),
      body: _screens[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.chat_outlined),
            selectedIcon: Icon(Icons.chat),
            label: 'Chat',
          ),
          NavigationDestination(
            icon: Icon(Icons.folder_outlined),
            selectedIcon: Icon(Icons.folder),
            label: 'Projekti',
          ),
        ],
      ),
    );
  }
}
