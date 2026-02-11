import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/brand_theme.dart';
import '../services/auth_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  String? _errorMessage;
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _fadeAnimation = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeOut,
    );
    _fadeController.forward();
  }

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _fadeController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _errorMessage = null;
    });

    final authService = context.read<AuthService>();
    final success = await authService.login(
      _usernameController.text.trim(),
      _passwordController.text,
    );

    if (!success && mounted) {
      setState(() {
        _errorMessage = 'Napačno uporabniško ime ali geslo';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final authService = context.watch<AuthService>();

    return Scaffold(
      body: Stack(
        children: [
          // Background gradient
          Container(
            decoration: const BoxDecoration(
              gradient: LuznarBrand.loginGradient,
            ),
          ),

          // Diamond pattern overlay
          Positioned.fill(
            child: CustomPaint(
              painter: DiamondPatternPainter(
                color: Colors.white,
                opacity: 0.03,
              ),
            ),
          ),

          // Content
          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: FadeTransition(
                  opacity: _fadeAnimation,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Logo and branding
                      const LuznarLogo(size: 72, withGlow: true),
                      const SizedBox(height: 20),
                      const Text(
                        'LUZNAR',
                        style: LuznarBrand.brandTitle,
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'ELECTRONICS',
                        style: LuznarBrand.brandSubtitle,
                      ),
                      const SizedBox(height: 8),
                      const GoldAccentLine(width: 48),
                      const SizedBox(height: 40),

                      // Login card
                      Container(
                        constraints: const BoxConstraints(maxWidth: 400),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(LuznarBrand.radiusMedium),
                          boxShadow: LuznarBrand.shadowLarge,
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(32),
                          child: Form(
                            key: _formKey,
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                // Title
                                const Text(
                                  'Prijava',
                                  style: TextStyle(
                                    fontSize: 22,
                                    fontWeight: FontWeight.w600,
                                    color: LuznarBrand.navy,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'AI Agent ERP System',
                                  style: TextStyle(
                                    fontSize: 13,
                                    color: LuznarBrand.textMuted,
                                    letterSpacing: 0.3,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                                const SizedBox(height: 28),

                                // Error message
                                if (_errorMessage != null) ...[
                                  Container(
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: LuznarBrand.error.withValues(alpha: 0.06),
                                      borderRadius: BorderRadius.circular(LuznarBrand.radiusSmall),
                                      border: Border.all(
                                        color: LuznarBrand.error.withValues(alpha: 0.2),
                                      ),
                                    ),
                                    child: Row(
                                      children: [
                                        Icon(Icons.error_outline,
                                            color: LuznarBrand.error, size: 20),
                                        const SizedBox(width: 10),
                                        Expanded(
                                          child: Text(
                                            _errorMessage!,
                                            style: const TextStyle(
                                              color: LuznarBrand.error,
                                              fontSize: 13,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(height: 20),
                                ],

                                // Username field
                                Text(
                                  'UPORABNIŠKO IME',
                                  style: LuznarBrand.label,
                                ),
                                const SizedBox(height: 6),
                                TextFormField(
                                  controller: _usernameController,
                                  decoration: const InputDecoration(
                                    hintText: 'Vnesite uporabniško ime',
                                    prefixIcon: Icon(Icons.person_outline, size: 20),
                                  ),
                                  textInputAction: TextInputAction.next,
                                  validator: (value) {
                                    if (value == null || value.isEmpty) {
                                      return 'Vnesite uporabniško ime';
                                    }
                                    return null;
                                  },
                                ),
                                const SizedBox(height: 20),

                                // Password field
                                Text(
                                  'GESLO',
                                  style: LuznarBrand.label,
                                ),
                                const SizedBox(height: 6),
                                TextFormField(
                                  controller: _passwordController,
                                  obscureText: _obscurePassword,
                                  decoration: InputDecoration(
                                    hintText: 'Vnesite geslo',
                                    prefixIcon: const Icon(Icons.lock_outline, size: 20),
                                    suffixIcon: IconButton(
                                      icon: Icon(
                                        _obscurePassword
                                            ? Icons.visibility_off_outlined
                                            : Icons.visibility_outlined,
                                        size: 20,
                                      ),
                                      onPressed: () {
                                        setState(() {
                                          _obscurePassword = !_obscurePassword;
                                        });
                                      },
                                    ),
                                  ),
                                  textInputAction: TextInputAction.done,
                                  onFieldSubmitted: (_) => _login(),
                                  validator: (value) {
                                    if (value == null || value.isEmpty) {
                                      return 'Vnesite geslo';
                                    }
                                    return null;
                                  },
                                ),
                                const SizedBox(height: 28),

                                // Login button
                                SizedBox(
                                  height: 48,
                                  child: ElevatedButton(
                                    onPressed: authService.isLoading ? null : _login,
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: LuznarBrand.navy,
                                      foregroundColor: Colors.white,
                                      disabledBackgroundColor: LuznarBrand.navyLight,
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(LuznarBrand.radiusSmall),
                                      ),
                                    ),
                                    child: authService.isLoading
                                        ? const SizedBox(
                                            width: 22,
                                            height: 22,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 2,
                                              color: LuznarBrand.gold,
                                            ),
                                          )
                                        : const Text(
                                            'Prijava',
                                            style: TextStyle(
                                              fontSize: 15,
                                              fontWeight: FontWeight.w600,
                                              letterSpacing: 0.5,
                                            ),
                                          ),
                                  ),
                                ),

                                const SizedBox(height: 16),
                                Text(
                                  'Privzeto: admin / admin123',
                                  style: TextStyle(
                                    fontSize: 11,
                                    color: LuznarBrand.textMuted,
                                  ),
                                  textAlign: TextAlign.center,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 32),

                      // Footer
                      Text(
                        'Luznar Electronics d.o.o.',
                        style: TextStyle(
                          fontSize: 11,
                          color: Colors.white.withValues(alpha: 0.4),
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Hrastje 52g, SI-4000 Kranj',
                        style: TextStyle(
                          fontSize: 10,
                          color: Colors.white.withValues(alpha: 0.25),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
