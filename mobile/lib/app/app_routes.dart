import 'package:flutter/cupertino.dart';
import 'package:zentryx_mobile/features/welcome/presentation/welcome_screen.dart';
import 'package:zentryx_mobile/features/transit/presentation/home_screen.dart';

/// One native navigator. Features own their screens; no second routing layer.
abstract final class AppRoutes {
  static const welcome = '/';
  static const passenger = '/passenger';

  static Route<void> generate(RouteSettings settings) =>
      CupertinoPageRoute<void>(
        settings: settings,
        builder: (context) => switch (settings.name) {
          passenger => const HomeScreen(),
          _ => WelcomeScreen(
            onPassenger: () => Navigator.of(context).pushNamed(passenger),
          ),
        },
      );
}
