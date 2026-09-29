import 'package:flutter/cupertino.dart';

/// All UI, map and vehicle paint colors live here. Brand reds are independent
/// of status colors; map tokens stay fixed because OSM tiles remain light.
class ZentryxColors {
  const ZentryxColors._();

  static const brand = Color(0xFFE63E5C);
  static const brandStrong = Color(0xFFC92745);
  static const brandDark = Color(0xFF8E1D34);
  static const brandSoft = Color(0xFFFCE8EC);
  static const white = Color(0xFFFFFFFF);
  static const text = Color(0xFF1D1B1C);

  static const ink = CupertinoDynamicColor.withBrightness(
    color: text,
    darkColor: Color(0xFFF6F6F7),
  );
  static const muted = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF6F696B),
    darkColor: Color(0xFFBDB6B9),
  );
  static const paper = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFF6F6F7),
    darkColor: Color(0xFF151315),
  );
  static const surface = CupertinoDynamicColor.withBrightness(
    color: white,
    darkColor: Color(0xFF231F21),
  );
  static const line = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFE6E1E3),
    darkColor: Color(0xFF42393D),
  );
  // Stronger than brand for small text on white; lighter on dark surfaces.
  static const action = CupertinoDynamicColor.withBrightness(
    color: brandStrong,
    darkColor: Color(0xFFFF8BA0),
  );
  static const selection = CupertinoDynamicColor.withBrightness(
    color: brandSoft,
    darkColor: Color(0xFF491F2A),
  );
  static const onSelection = CupertinoDynamicColor.withBrightness(
    color: brandDark,
    darkColor: Color(0xFFFFCED8),
  );

  // Semantic status colors: never alias these to brand red.
  static const success = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF1C7041),
    darkColor: Color(0xFF73D6A0),
  );
  static const warning = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF8A5700),
    darkColor: Color(0xFFF4C56A),
  );
  static const danger = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFB42318),
    darkColor: Color(0xFFFFA18F),
  );
  static const info = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF245FAD),
    darkColor: Color(0xFF91BEF8),
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

  static const surfaceShadow = Color(0x171D1B1C);
  static const markerShadow = Color(0x331D1B1C);
  static const markShadow = Color(0x661D1B1C);
  static const markHighlight = Color(0x33FFFFFF);
  static const routeHalo = Color(0xF2FFFFFF);
  static const routeBorder = brandDark;
  static const route = brand;
  static const stationBorder = brandStrong;
  static const stationSelected = brandStrong;
  static const stationHalo = Color(0xE6FCE8EC);
  static const stationNormalHalo = Color(0xBBFFFFFF);
  static const attributionSurface = Color(0xEFFFFFFF);

  // Original bus palette deliberately distinct from the red route.
  static const busBody = Color(0xFF07566C);
  static const busRoof = Color(0xFF29B8D5);
  static const busOffline = Color(0xFF92AFB8);
  static const busGlass = Color(0xFF083A4C);
  static const busReflection = Color(0xFF6BD9ED);
  static const busRoofHighlight = Color(0xFFA4EDFA);
  static const busTailLight = Color(0xFFD94B37);
  static const busOfflineBadge = Color(0xFFB66D00);
  static const busShadow = Color(0x991D1B1C);
}

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
      letterSpacing: -0.2,
    ),
    navLargeTitleTextStyle: TextStyle(
      color: ZentryxColors.ink,
      fontSize: 34,
      fontWeight: FontWeight.w700,
      letterSpacing: -1.1,
    ),
  ),
);
