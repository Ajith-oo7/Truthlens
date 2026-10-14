import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class TruthColors {
  static const voidBg = Color(0xFF0B0F17);
  static const surface = Color(0xFF0F131C);
  static const panel = Color(0xFF111827);
  static const panelHigh = Color(0xFF1E293B);
  static const cyan = Color(0xFF06B6D4);
  static const cyanBright = Color(0xFF4CD7F6);
  static const indigo = Color(0xFF6366F1);
  static const verdant = Color(0xFF10B981);
  static const crimson = Color(0xFFEF4444);
  static const amber = Color(0xFFF59E0B);
  static const purple = Color(0xFF8B5CF6);
  static const text = Color(0xFFF8FAFC);
  static const muted = Color(0xFF94A3B8);

  static Color verdict(String label) {
    switch (label) {
      case 'TRUE':
        return verdant;
      case 'FALSE':
        return crimson;
      case 'PARTIALLY_TRUE':
      case 'MISLEADING':
        return amber;
      default:
        return purple;
    }
  }
}

ThemeData truthTheme() {
  final base = ThemeData(
    brightness: Brightness.dark,
    useMaterial3: true,
    scaffoldBackgroundColor: TruthColors.voidBg,
    colorScheme: const ColorScheme.dark(
      primary: TruthColors.cyan,
      secondary: TruthColors.indigo,
      surface: TruthColors.surface,
    ),
  );
  return base.copyWith(
    textTheme: GoogleFonts.interTextTheme(base.textTheme).apply(
      bodyColor: TruthColors.text,
      displayColor: TruthColors.text,
    ),
  );
}
