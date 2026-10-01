import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/cupertino.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:zentryx_mobile/app/zentryx_app.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/driver/application/driver_session.dart';
import 'package:zentryx_mobile/features/driver/application/device_telemetry_controller.dart';
import 'package:zentryx_mobile/features/driver/data/driver_session_store.dart';
import 'package:zentryx_mobile/features/driver/data/simulated_device_telemetry_source.dart';
import 'package:zentryx_mobile/features/driver/presentation/driver_screen.dart';
import 'package:zentryx_mobile/features/driver/presentation/device_diagnostics_screen.dart';
import 'package:zentryx_mobile/features/driver/presentation/prepare_trip_screen.dart';

import 'driver_test_support.dart';

void main() {
  setUpAll(() async {
    final root = Platform.environment['FLUTTER_ROOT'];
    if (root == null) return;
    final font = File(
      '$root/bin/cache/artifacts/material_fonts/Roboto-Regular.ttf',
    );
    if (font.existsSync()) {
      await (FontLoader('ReviewFont')..addFont(
            Future.value(ByteData.sublistView(font.readAsBytesSync())),
          ))
          .load();
      await (FontLoader('packages/cupertino_icons/CupertinoIcons')..addFont(
            rootBundle.load(
              'packages/cupertino_icons/assets/CupertinoIcons.ttf',
            ),
          ))
          .load();
    }
  });
  testWidgets(
    'preparation precedes start; diagnosis returns to same preparation',
    (tester) async {
      addTearDown(() => tester.pumpWidget(const SizedBox.shrink()));
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            driverSessionStoreProvider.overrideWithValue(MemorySessionStore()),
          ],
          child: const ZentryxApp(),
        ),
      );
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.text('Soy conductor'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Soy conductor'));
      await tester.pumpAndSettle();
      expect(find.byType(PrepareTripScreen), findsOneWidget);
      expect(find.text('ZTX-GPS-001'), findsOneWidget);
      await _reveal(tester, find.text('Ver diagnóstico'));
      await tester.tap(find.text('Ver diagnóstico'));
      await tester.pumpAndSettle();
      expect(find.byType(DeviceDiagnosticsScreen), findsOneWidget);
      await tester.tap(find.byType(CupertinoNavigationBarBackButton));
      await tester.pumpAndSettle();
      expect(find.byType(PrepareTripScreen), findsOneWidget);
      await _reveal(tester, find.text('Iniciar recorrido'));
      await tester.tap(find.text('Iniciar recorrido'));
      await tester.pumpAndSettle();
      expect(find.byType(PrepareTripScreen), findsNothing);
      expect(find.text('Recorrido activo'), findsOneWidget);
    },
  );
  testWidgets(
    'new ProviderScope restores active dashboard instead of offering a new start',
    (tester) async {
      final store = MemorySessionStore();
      final first = DriverSessionController(store);
      await first.start(SimulatedDeviceTelemetrySource.unit);
      await first.report(IncidentType.other);
      first.dispose();
      addTearDown(() => tester.pumpWidget(const SizedBox.shrink()));
      await tester.pumpWidget(
        ProviderScope(
          overrides: [driverSessionStoreProvider.overrideWithValue(store)],
          child: const CupertinoApp(theme: zentryxTheme, home: DriverScreen()),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Recorrido activo'), findsOneWidget);
      expect(find.text('Iniciar recorrido'), findsNothing);
      expect(find.text('Registrado localmente: Otro'), findsOneWidget);
    },
  );
  testWidgets(
    'device adapter pauses in background and is disposed on return to welcome',
    (tester) async {
      final source = FixedTelemetrySource(demoPacket());
      final container = ProviderContainer(
        overrides: [
          driverSessionStoreProvider.overrideWithValue(MemorySessionStore()),
          deviceTelemetrySourceProvider.overrideWith((ref) {
            ref.onDispose(source.dispose);
            return source;
          }),
        ],
      );
      addTearDown(container.dispose);
      addTearDown(() => tester.pumpWidget(const SizedBox.shrink()));
      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: const ZentryxApp(),
        ),
      );
      await tester.pumpAndSettle();
      await _reveal(tester, find.text('Soy conductor'));
      await tester.tap(find.text('Soy conductor'));
      await tester.pumpAndSettle();
      expect(source.starts, 1);
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
      expect(source.pauses, greaterThan(0));
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      expect(source.starts, 2);
      expect(container.exists(transitControllerProvider), isFalse);
      await tester.tap(find.byType(CupertinoNavigationBarBackButton));
      await tester.pumpAndSettle();
      expect(source.disposed, isTrue);
      expect(container.exists(deviceTelemetryProvider), isFalse);
      expect(tester.takeException(), isNull);
    },
  );
  for (final entry in {
    SimulatedTelemetryScenario.disconnected: 'Dispositivo desconectado',
    SimulatedTelemetryScenario.noGps: 'GPS sin señal',
    SimulatedTelemetryScenario.noServer: 'Servidor desconectado',
    SimulatedTelemetryScenario.stale: 'Telemetría atrasada',
    SimulatedTelemetryScenario.waiting: 'Esperando primer paquete',
    SimulatedTelemetryScenario.syncing: 'Sincronizando',
    SimulatedTelemetryScenario.failure: 'Fallo del dispositivo',
  }.entries) {
    testWidgets(
      'diagnosis renders ${entry.key.name} without claiming live telemetry',
      (tester) async {
        addTearDown(() => tester.pumpWidget(const SizedBox.shrink()));
        await tester.pumpWidget(
          ProviderScope(
            overrides: [
              deviceTelemetrySourceProvider.overrideWith((ref) {
                final source = FixedTelemetrySource(demoPacket(entry.key));
                ref.onDispose(source.dispose);
                return source;
              }),
            ],
            child: const CupertinoApp(
              theme: zentryxTheme,
              home: DeviceDiagnosticsScreen(),
            ),
          ),
        );
        await tester.pumpAndSettle();
        await _reveal(tester, find.text(entry.value).last);
        expect(find.text(entry.value), findsWidgets);
        expect(tester.takeException(), isNull);
      },
    );
  }
  for (final width in [360.0, 390.0, 430.0]) {
    for (final scale in [1.0, 2.0]) {
      for (final brightness in Brightness.values) {
        testWidgets('diagnosis layout $width $scale $brightness', (
          tester,
        ) async {
          tester.view.physicalSize = Size(width, 844);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);
          addTearDown(() => tester.pumpWidget(const SizedBox.shrink()));
          final key = GlobalKey();
          await tester.pumpWidget(
            ProviderScope(
              overrides: [
                deviceTelemetrySourceProvider.overrideWith((ref) {
                  final source = FixedTelemetrySource(demoPacket());
                  ref.onDispose(source.dispose);
                  return source;
                }),
              ],
              child: CupertinoApp(
                debugShowCheckedModeBanner: false,
                theme: zentryxTheme.copyWith(
                  brightness: brightness,
                  textTheme: const CupertinoTextThemeData(
                    textStyle: TextStyle(
                      fontFamily: 'ReviewFont',
                      color: ZentryxColors.ink,
                    ),
                    navTitleTextStyle: TextStyle(
                      fontFamily: 'ReviewFont',
                      fontSize: 17,
                      color: ZentryxColors.ink,
                    ),
                    actionTextStyle: TextStyle(
                      fontFamily: 'ReviewFont',
                      color: ZentryxColors.action,
                    ),
                  ),
                ),
                home: MediaQuery(
                  data: MediaQueryData(
                    size: Size(width, 844),
                    platformBrightness: brightness,
                    padding: const EdgeInsets.only(top: 47, bottom: 34),
                    textScaler: TextScaler.linear(scale),
                  ),
                  child: RepaintBoundary(
                    key: key,
                    child: const DeviceDiagnosticsScreen(),
                  ),
                ),
              ),
            ),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          if (const bool.fromEnvironment('ZENTRYX_CAPTURE_REVIEW')) {
            await _capture(
              tester,
              key,
              'diagnosis-${width.toInt()}-$scale-${brightness.name}',
            );
          }
          await _reveal(tester, find.text('Latitud'));
          expect(find.text('19.622110'), findsOneWidget);
          expect(tester.takeException(), isNull);
          if (const bool.fromEnvironment('ZENTRYX_CAPTURE_REVIEW')) {
            await _capture(
              tester,
              key,
              'diagnosis-gps-${width.toInt()}-$scale-${brightness.name}',
            );
          }
        });
      }
    }
  }
}

Future<void> _reveal(WidgetTester tester, Finder target) async {
  if (target.evaluate().isEmpty) {
    await tester.scrollUntilVisible(
      target,
      160,
      scrollable: find.byType(Scrollable).first,
      maxScrolls: 40,
    );
  } else {
    await tester.ensureVisible(target.first);
  }
  await tester.pumpAndSettle();
}

Future<void> _capture(WidgetTester tester, GlobalKey key, String name) async {
  debugDisableShadows = false;
  void repaint(RenderObject object) {
    object.markNeedsPaint();
    object.visitChildren(repaint);
  }

  repaint(key.currentContext!.findRenderObject()!);
  await tester.pump();
  try {
    await tester.runAsync(() async {
      final image =
          await (key.currentContext!.findRenderObject()
                  as RenderRepaintBoundary)
              .toImage();
      final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
      final file = File('build/visual-review/$name.png');
      await file.parent.create(recursive: true);
      await file.writeAsBytes(bytes!.buffer.asUint8List());
      image.dispose();
    });
  } finally {
    debugDisableShadows = true;
  }
}
