import 'package:flutter/cupertino.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/presentation/home_screen.dart';

class ZentryxApp extends StatelessWidget {
  const ZentryxApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const CupertinoApp(
      debugShowCheckedModeBanner: false,
      title: 'Zentryx',
      theme: zentryxTheme,
      home: HomeScreen(),
    );
  }
}
