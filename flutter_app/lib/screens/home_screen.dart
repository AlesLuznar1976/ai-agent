import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/brand_theme.dart';
import '../services/auth_service.dart';
import 'chat_screen.dart';
import 'projects_screen.dart';
import 'emaili_screen.dart';

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
    EmailiScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final authService = context.watch<AuthService>();
    final user = authService.currentUser;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: LuznarBrand.navy,
        title: Row(
          children: [
            const LuznarLogo(size: 28, color: LuznarBrand.gold),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'LUZNAR',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                    letterSpacing: 1.2,
                  ),
                ),
                Text(
                  'AI Agent',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w400,
                    color: LuznarBrand.gold.withValues(alpha: 0.9),
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          // User info
          if (user != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(LuznarBrand.radiusXLarge),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.15),
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.person_outline,
                        size: 16,
                        color: LuznarBrand.gold.withValues(alpha: 0.8),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        user.username,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // Logout
          IconButton(
            icon: Icon(
              Icons.logout_rounded,
              color: Colors.white.withValues(alpha: 0.7),
              size: 20,
            ),
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
          const SizedBox(width: 4),
        ],
      ),
      body: _screens[_selectedIndex],
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: LuznarBrand.surfaceWhite,
          border: Border(
            top: BorderSide(
              color: LuznarBrand.navy.withValues(alpha: 0.08),
            ),
          ),
        ),
        child: NavigationBar(
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
            NavigationDestination(
              icon: Icon(Icons.email_outlined),
              selectedIcon: Icon(Icons.email),
              label: 'Emaili',
            ),
          ],
        ),
      ),
    );
  }
}
