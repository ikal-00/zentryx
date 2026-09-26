import 'dart:async';

import 'package:flutter/cupertino.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';
import 'package:zentryx_mobile/features/transit/presentation/home_screen.dart';

class ZentryxApp extends ConsumerStatefulWidget {
  const ZentryxApp({super.key});

  @override
  ConsumerState<ZentryxApp> createState() => _ZentryxAppState();
}

class _ZentryxAppState extends ConsumerState<ZentryxApp>
    with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final controller = ref.read(transitControllerProvider.notifier);
    if (state == AppLifecycleState.resumed) {
      unawaited(controller.resume());
      return;
    }
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.detached) {
      controller.pause();
    }
  }

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
