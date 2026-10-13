import 'package:flutter/cupertino.dart';

/// Tier-1 Enterprise Design System Colors for Zentryx Passenger Experience.
///
/// Refined around the authentic Mexibús Línea 2 crimson-red identity.
/// Strictly non-neon, high-contrast, optimized for both light and deep-dark modes.
class ZentryxColors {
  const ZentryxColors._();

  // --- Core Brand Identity (Tier-1 Crimson Heritage, strictly non-neon) ---
  static const brand = Color(0xFFD31034);        // Cardinal red, high energy, elegant
  static const brandStrong = Color(0xFFB50D2B);  // Deep executive crimson for primary CTAs
  static const brandDark = Color(0xFF7A091D);    // Regal wine/burgundy for contrast accents
  static const brandSoft = Color(0xFFFDEBED);    // Soft ruby mist for light highlights
  static const brandSoftDark = Color(0xFF381018);// Muted wine dark backdrop
  static const white = Color(0xFFFFFFFF);
  static const black = Color(0xFF000000);

  // --- Dynamic Surface & Typography Tokens (Uber-grade minimal neutrals) ---
  static const ink = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF111217),      // Deep graphite black
    darkColor: Color(0xFFF9FAFB),  // Pure soft white
  );
  static const text = ink;

  static const muted = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF5F6368),      // Crisp neutral secondary
    darkColor: Color(0xFF9CA3AF),  // Balanced low-glare secondary
  );

  static const subtle = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF8C9099),      // Tertiary helper labels
    darkColor: Color(0xFF6B7280),
  );

  static const paper = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFF8F9FA),      // Clean minimal off-white
    darkColor: Color(0xFF0E0F12),  // Luxury obsidian backdrop
  );

  static const surface = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFFFFFFF),      // Pure white card
    darkColor: Color(0xFF18191E),  // Deep charcoal card
  );

  static const surfaceElevated = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFFFFFFF),
    darkColor: Color(0xFF22242B),  // Elevated card for modals & sheets
  );

  static const line = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFE5E7EB),      // Subtle hairline border
    darkColor: Color(0xFF282A33),
  );

  static const action = CupertinoDynamicColor.withBrightness(
    color: brandStrong,
    darkColor: Color(0xFFFF4D67),  // Warm ruby highlight on dark
  );

  static const selection = CupertinoDynamicColor.withBrightness(
    color: brandSoft,
    darkColor: Color(0xFF381018),
  );

  static const onSelection = CupertinoDynamicColor.withBrightness(
    color: brandDark,
    darkColor: Color(0xFFFFBAC5),
  );

  // --- Semantic Status Indicators (Strictly balanced, never neon) ---
  static const success = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF0F7644),      // Rich forest emerald
    darkColor: Color(0xFF34D399),
  );

  static const warning = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFB45309),      // Warm amber ochre
    darkColor: Color(0xFFFBBF24),
  );

  static const danger = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFB91C1C),      // Urgent brick red
    darkColor: Color(0xFFF87171),
  );

  static const info = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF1D4ED8),      // Sapphire royal blue
    darkColor: Color(0xFF60A5FA),
  );

  static Color occupancy(String value) => switch (value.toLowerCase()) {
    'low' || 'baja' => success,
    'medium' || 'media' => warning,
    'high' || 'alta' => danger,
    _ => muted,
  };

  static Color alert(String severity) => switch (severity) {
    'critical' => danger,
    'warning' => warning,
    _ => info,
  };

  // --- Map & Cartography Paint Tokens ---
  static const surfaceShadow = Color(0x180D0E12);
  static const markerShadow = Color(0x380D0E12);
  static const markShadow = Color(0x500D0E12);
  static const markHighlight = Color(0x40FFFFFF);

  // Route styling: crisp double-cased track with outer casing and solid ruby core
  static const routeHalo = Color(0xEEFFFFFF);
  static const routeBorder = brandDark;
  static const route = brand;

  // Station styling: Uber-like pins
  static const stationBorder = brandStrong;
  static const stationSelected = brandStrong;
  static const stationHalo = Color(0xCCFDEBED);
  static const stationNormalHalo = Color(0xDDFFFFFF);
  static const attributionSurface = Color(0xF0FFFFFF);

  // Vehicle styling: Sleek executive transit bus
  static const busBody = Color(0xFF14151B);         // Obsidian black graphite body
  static const busRoof = brand;                     // Signature Mexibús red roof crown
  static const busOffline = Color(0xFF6B7280);
  static const busGlass = Color(0xFF242631);
  static const busReflection = Color(0x40FFFFFF);
  static const busRoofHighlight = Color(0xFFE8425F);
  static const busTailLight = Color(0xFFEF4444);
  static const busOfflineBadge = Color(0xFFD97706);
  static const busShadow = Color(0x66000000);
}

/// Tier-1 Cupertino Theme Configuration.
const zentryxTheme = CupertinoThemeData(
  primaryColor: ZentryxColors.action,
  primaryContrastingColor: ZentryxColors.white,
  scaffoldBackgroundColor: ZentryxColors.paper,
  barBackgroundColor: ZentryxColors.surface,
  textTheme: CupertinoTextThemeData(
    primaryColor: ZentryxColors.action,
    textStyle: TextStyle(
      color: ZentryxColors.ink,
      fontSize: 16,
      letterSpacing: -0.3,
    ),
    navTitleTextStyle: TextStyle(
      color: ZentryxColors.ink,
      fontSize: 17,
      fontWeight: FontWeight.w600,
      letterSpacing: -0.4,
    ),
    navLargeTitleTextStyle: TextStyle(
      color: ZentryxColors.ink,
      fontSize: 34,
      fontWeight: FontWeight.w800,
      letterSpacing: -1.2,
    ),
    actionTextStyle: TextStyle(
      color: ZentryxColors.action,
      fontSize: 16,
      fontWeight: FontWeight.w600,
      letterSpacing: -0.2,
    ),
  ),
);
