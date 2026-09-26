import 'package:flutter/cupertino.dart';

class ZentryxColors {
  const ZentryxColors._();

  static const ink = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF153C34),
    darkColor: Color(0xFFE9F3EF),
  );
  static const accent = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFD6F67A),
    darkColor: Color(0xFFC6EB62),
  );
  static const paper = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFF6F8F4),
    darkColor: Color(0xFF0C1110),
  );
  static const surface = CupertinoDynamicColor.withBrightness(
    color: Color(0xEFFFFFFF),
    darkColor: Color(0xE619211E),
  );
  static const muted = CupertinoDynamicColor.withBrightness(
    color: Color(0xFF64736D),
    darkColor: Color(0xFFA8B5B0),
  );
  static const line = CupertinoDynamicColor.withBrightness(
    color: Color(0xFFE2E9E2),
    darkColor: Color(0xFF2A3431),
  );
  static const warning = Color(0xFFD58B22);
  static const danger = Color(0xFFE85D5D);
}

const zentryxTheme = CupertinoThemeData(
  primaryColor: ZentryxColors.ink,
  scaffoldBackgroundColor: ZentryxColors.paper,
  barBackgroundColor: ZentryxColors.surface,
  textTheme: CupertinoTextThemeData(
    primaryColor: ZentryxColors.ink,
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
