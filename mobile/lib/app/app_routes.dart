import 'package:flutter/cupertino.dart';
import 'package:zentryx_mobile/features/driver/domain/driver_session.dart';
import 'package:zentryx_mobile/features/driver/presentation/driver_verification_screen.dart';
import 'package:zentryx_mobile/features/transit/presentation/home_screen.dart';
import 'package:zentryx_mobile/features/welcome/presentation/welcome_screen.dart';

/// One native navigator. Features own their screens; no second routing layer.
abstract final class AppRoutes {
  static const welcome = '/';
  static const passenger = '/passenger';
  static const driverVerify = '/driver-verify';
  static const driverMap = '/driver-map';

  static Route<void> generate(RouteSettings settings) =>
      CupertinoPageRoute<void>(
        settings: settings,
        builder: (context) => switch (settings.name) {
          passenger => const HomeScreen(),
          driverVerify => DriverVerificationScreen(
            onVerified: (session) => Navigator.of(context).pushReplacementNamed(
              driverMap,
              arguments: session,
            ),
          ),
          driverMap => HomeScreen(
            driverSession: settings.arguments is DriverSession
                ? settings.arguments! as DriverSession
                : const DriverSession(
                    folio: '84021',
                    unitPlate: 'MEX-1234',
                    operatorName: 'Carlos Eduardo Mendoza Rojas',
                    economicNumber: 'unit-demo-01',
                    authMethod: 'manual',
                  ),
          ),
          _ => WelcomeScreen(
            onPassenger: () => Navigator.of(context).pushNamed(passenger),
            onDriver: () => Navigator.of(context).pushNamed(driverVerify),
          ),
        },
      );
}
