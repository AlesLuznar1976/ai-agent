import 'package:flutter/material.dart';

/// Luznar Electronics brand theme
/// Based on corporate identity: Navy blue + Gold accent
class LuznarBrand {
  LuznarBrand._();

  // ─── Brand Colors ───────────────────────────────────────────────
  static const Color navy = Color(0xFF1A2744);
  static const Color navyLight = Color(0xFF2C3E5F);
  static const Color navyDark = Color(0xFF0F1A2E);

  static const Color gold = Color(0xFFB8963E);
  static const Color goldLight = Color(0xFFD4B366);
  static const Color goldDark = Color(0xFF8C6F2A);

  static const Color surface = Color(0xFFF8F9FB);
  static const Color surfaceWhite = Color(0xFFFFFFFF);
  static const Color surfaceCard = Color(0xFFFFFFFF);
  static const Color surfaceDark = Color(0xFFF0F2F5);

  static const Color textPrimary = Color(0xFF1A2744);
  static const Color textSecondary = Color(0xFF5A6577);
  static const Color textMuted = Color(0xFF8B95A5);
  static const Color textOnNavy = Color(0xFFFFFFFF);
  static const Color textOnGold = Color(0xFF1A2744);

  static const Color success = Color(0xFF2E7D4F);
  static const Color error = Color(0xFFC53030);
  static const Color warning = Color(0xFFB8963E);
  static const Color info = Color(0xFF2C5282);

  // ─── Gradients ──────────────────────────────────────────────────
  static const LinearGradient navyGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF1A2744), Color(0xFF2C3E5F)],
  );

  static const LinearGradient loginGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Color(0xFF0F1A2E), Color(0xFF1A2744), Color(0xFF2C3E5F)],
    stops: [0.0, 0.5, 1.0],
  );

  static const LinearGradient goldGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFFD4B366), Color(0xFFB8963E)],
  );

  // ─── Typography ─────────────────────────────────────────────────
  static const String fontFamily = 'Roboto';

  static const TextStyle headingLarge = TextStyle(
    fontSize: 28,
    fontWeight: FontWeight.w700,
    color: navy,
    letterSpacing: -0.5,
  );

  static const TextStyle headingMedium = TextStyle(
    fontSize: 22,
    fontWeight: FontWeight.w600,
    color: navy,
    letterSpacing: -0.3,
  );

  static const TextStyle headingSmall = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w600,
    color: navy,
  );

  static const TextStyle bodyLarge = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.w400,
    color: textPrimary,
  );

  static const TextStyle bodyMedium = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w400,
    color: textPrimary,
  );

  static const TextStyle bodySmall = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w400,
    color: textSecondary,
  );

  static const TextStyle label = TextStyle(
    fontSize: 11,
    fontWeight: FontWeight.w600,
    color: textMuted,
    letterSpacing: 0.5,
  );

  static const TextStyle brandTitle = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.w700,
    color: surfaceWhite,
    letterSpacing: 1.5,
  );

  static const TextStyle brandSubtitle = TextStyle(
    fontSize: 13,
    fontWeight: FontWeight.w400,
    color: gold,
    letterSpacing: 2.0,
  );

  // ─── Dimensions ─────────────────────────────────────────────────
  static const double radiusSmall = 6.0;
  static const double radiusMedium = 12.0;
  static const double radiusLarge = 16.0;
  static const double radiusXLarge = 24.0;

  // ─── Shadows ────────────────────────────────────────────────────
  static List<BoxShadow> get shadowSmall => [
    BoxShadow(
      color: navy.withValues(alpha: 0.06),
      blurRadius: 8,
      offset: const Offset(0, 2),
    ),
  ];

  static List<BoxShadow> get shadowMedium => [
    BoxShadow(
      color: navy.withValues(alpha: 0.08),
      blurRadius: 16,
      offset: const Offset(0, 4),
    ),
  ];

  static List<BoxShadow> get shadowLarge => [
    BoxShadow(
      color: navy.withValues(alpha: 0.12),
      blurRadius: 24,
      offset: const Offset(0, 8),
    ),
  ];

  // ─── Material Theme ─────────────────────────────────────────────
  static ThemeData get theme => ThemeData(
    useMaterial3: true,
    fontFamily: fontFamily,

    colorScheme: ColorScheme(
      brightness: Brightness.light,
      primary: navy,
      onPrimary: textOnNavy,
      secondary: gold,
      onSecondary: textOnGold,
      error: error,
      onError: surfaceWhite,
      surface: surface,
      onSurface: textPrimary,
      surfaceContainerHighest: surfaceDark,
    ),

    scaffoldBackgroundColor: surface,

    appBarTheme: const AppBarTheme(
      backgroundColor: navy,
      foregroundColor: textOnNavy,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w600,
        color: textOnNavy,
        letterSpacing: 0.3,
      ),
    ),

    cardTheme: CardThemeData(
      elevation: 0,
      color: surfaceCard,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(radiusMedium),
        side: BorderSide(color: navy.withValues(alpha: 0.08)),
      ),
      margin: const EdgeInsets.only(bottom: 8),
    ),

    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: navy,
        foregroundColor: textOnNavy,
        elevation: 0,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusSmall),
        ),
        textStyle: const TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.3,
        ),
      ),
    ),

    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: navy,
        side: BorderSide(color: navy.withValues(alpha: 0.3)),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(radiusSmall),
        ),
      ),
    ),

    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: navy,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),
    ),

    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: surfaceWhite,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(radiusSmall),
        borderSide: BorderSide(color: navy.withValues(alpha: 0.15)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(radiusSmall),
        borderSide: BorderSide(color: navy.withValues(alpha: 0.15)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(radiusSmall),
        borderSide: const BorderSide(color: navy, width: 1.5),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(radiusSmall),
        borderSide: const BorderSide(color: error),
      ),
      labelStyle: TextStyle(color: textSecondary),
      hintStyle: TextStyle(color: textMuted),
    ),

    chipTheme: ChipThemeData(
      backgroundColor: surfaceWhite,
      selectedColor: navy.withValues(alpha: 0.1),
      labelStyle: const TextStyle(fontSize: 13, color: textPrimary),
      side: BorderSide(color: navy.withValues(alpha: 0.12)),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(radiusXLarge),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
    ),

    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: surfaceWhite,
      elevation: 0,
      indicatorColor: navy.withValues(alpha: 0.1),
      labelTextStyle: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: navy,
          );
        }
        return const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w400,
          color: textMuted,
        );
      }),
      iconTheme: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return const IconThemeData(color: navy, size: 24);
        }
        return const IconThemeData(color: textMuted, size: 24);
      }),
    ),

    dividerTheme: DividerThemeData(
      color: navy.withValues(alpha: 0.08),
      thickness: 1,
    ),

    snackBarTheme: SnackBarThemeData(
      backgroundColor: navy,
      contentTextStyle: const TextStyle(color: textOnNavy),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(radiusSmall),
      ),
      behavior: SnackBarBehavior.floating,
    ),

    dialogTheme: DialogThemeData(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(radiusMedium),
      ),
    ),

    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: gold,
    ),
  );
}

/// Luznar diamond logo widget - rendered via CustomPainter
class LuznarLogo extends StatelessWidget {
  final double size;
  final Color? color;
  final bool withGlow;

  const LuznarLogo({
    super.key,
    this.size = 48,
    this.color,
    this.withGlow = false,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        painter: _LuznarLogoPainter(
          color: color ?? LuznarBrand.gold,
          withGlow: withGlow,
        ),
      ),
    );
  }
}

class _LuznarLogoPainter extends CustomPainter {
  final Color color;
  final bool withGlow;

  _LuznarLogoPainter({required this.color, required this.withGlow});

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final cx = w / 2;
    final cy = h / 2;

    // Outer diamond
    final outerPath = Path()
      ..moveTo(cx, 0)
      ..lineTo(w, cy)
      ..lineTo(cx, h)
      ..lineTo(0, cy)
      ..close();

    // Glow effect
    if (withGlow) {
      final glowPaint = Paint()
        ..color = color.withValues(alpha: 0.15)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 12);
      canvas.drawPath(outerPath, glowPaint);
    }

    // Outer diamond fill
    final outerPaint = Paint()
      ..color = color
      ..style = PaintingStyle.fill;
    canvas.drawPath(outerPath, outerPaint);

    // Inner arrow / chevron pointing right
    final innerPaint = Paint()
      ..color = LuznarBrand.navy
      ..style = PaintingStyle.fill;

    final arrowPath = Path()
      ..moveTo(cx * 0.55, cy * 0.55)
      ..lineTo(cx * 1.3, cy)
      ..lineTo(cx * 0.55, cy * 1.45)
      ..lineTo(cx * 0.75, cy)
      ..close();
    canvas.drawPath(arrowPath, innerPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Diamond pattern background painter for login screen
class DiamondPatternPainter extends CustomPainter {
  final Color color;
  final double opacity;

  DiamondPatternPainter({
    this.color = const Color(0xFFFFFFFF),
    this.opacity = 0.03,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color.withValues(alpha: opacity)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 0.8;

    const spacing = 60.0;
    const diamondSize = 18.0;

    for (double x = -spacing; x < size.width + spacing; x += spacing) {
      for (double y = -spacing; y < size.height + spacing; y += spacing) {
        // Offset every other row
        final offsetX = (y ~/ spacing).isOdd ? spacing / 2 : 0.0;
        final px = x + offsetX;

        final path = Path()
          ..moveTo(px, y - diamondSize)
          ..lineTo(px + diamondSize, y)
          ..lineTo(px, y + diamondSize)
          ..lineTo(px - diamondSize, y)
          ..close();

        canvas.drawPath(path, paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

/// Gold accent line separator
class GoldAccentLine extends StatelessWidget {
  final double width;

  const GoldAccentLine({super.key, this.width = 40});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: 2,
      decoration: const BoxDecoration(
        gradient: LuznarBrand.goldGradient,
        borderRadius: BorderRadius.all(Radius.circular(1)),
      ),
    );
  }
}
