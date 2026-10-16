import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/cupertino.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:zentryx_mobile/app/zentryx_app.dart';
import 'package:zentryx_mobile/core/network/api_client.dart';
import 'package:zentryx_mobile/design_system/relative_time.dart';
import 'package:zentryx_mobile/design_system/system_status.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';
import 'package:zentryx_mobile/features/transit/data/transit_repository.dart';
import 'package:zentryx_mobile/features/transit/presentation/home_screen.dart';
import 'package:zentryx_mobile/features/transit/presentation/widgets/live_status_indicator.dart';
import 'package:zentryx_mobile/features/welcome/presentation/welcome_screen.dart';

import 'transit_ui_test.dart' show fixtureState, vehicle;

class _TransitFixture extends TransitController {
  _TransitFixture() : super(TransitRepository(ApiClient('http://localhost'))) {
    state = fixtureState;
  }
}

void main() {
  setUpAll(() async {
    final root = Platform.environment['FLUTTER_ROOT'];
    if (root == null) return;
    final font = File(
      '$root/bin/cache/artifacts/material_fonts/Roboto-Regular.ttf',
    );
    if (!font.existsSync()) return;
    await (FontLoader('ReviewFont')
          ..addFont(Future.value(ByteData.sublistView(font.readAsBytesSync()))))
        .load();
    await (FontLoader('packages/cupertino_icons/CupertinoIcons')..addFont(
          rootBundle.load('packages/cupertino_icons/assets/CupertinoIcons.ttf'),
        ))
        .load();
  });

  test('presentation status distinguishes syncing, offline, stale, errors and live', () {
    final now = DateTime(2026, 9, 30, 12);
    expect(
      transitSystemStatus(const TransitState(), now),
      SystemStatus.syncing,
    );
    expect(
      transitSystemStatus(const TransitState(loading: false), now),
      SystemStatus.disconnected,
    );
    expect(
      transitSystemStatus(
        const TransitState(loading: false, error: 'Failure'),
        now,
      ),
      SystemStatus.error,
    );
    expect(
      transitSystemStatus(
        TransitState(loading: false, vehicle: vehicle, lastSuccess: now),
        now,
      ),
      SystemStatus.connected,
    );
    expect(
      transitSystemStatus(fixtureState.copyWith(stale: true), now),
      SystemStatus.stale,
    );
    expect(
      transitSystemStatus(fixtureState.copyWith(refreshing: true), now),
      SystemStatus.syncing,
    );
    expect(
      transitSystemStatus(
        fixtureState.copyWith(
          lastSuccess: now.subtract(const Duration(minutes: 1)),
        ),
        now,
      ),
      SystemStatus.stale,
    );
    expect(
      updatedAgo(now.subtract(const Duration(seconds: 2)), now),
      'Actualizado hace 2 s',
    );
    expect(updatedAgo(null, now), 'Sin actualización');
  });

  testWidgets(
    'welcome is immediate and lifecycle does not initialize transit',
    (tester) async {
      final container = ProviderContainer();
      addTearDown(() => tester.pumpWidget(const SizedBox.shrink()));
      try {
        await tester.pumpWidget(
          UncontrolledProviderScope(
            container: container,
            child: const ZentryxApp(),
          ),
        );
        await tester.pumpAndSettle();
        expect(find.byType(WelcomeScreen), findsOneWidget);
        expect(container.exists(transitControllerProvider), isFalse);
        tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
        tester.binding.handleAppLifecycleStateChanged(
          AppLifecycleState.resumed,
        );
        expect(container.exists(transitControllerProvider), isFalse);
      } finally {
        await tester.pumpWidget(const SizedBox.shrink());
        container.dispose();
      }
    },
  );

  testWidgets(
    'passenger opens existing map in one tap and returns to welcome',
    (tester) async {
      addTearDown(() => tester.pumpWidget(const SizedBox.shrink()));
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            transitControllerProvider.overrideWith((ref) => _TransitFixture()),
          ],
          child: const ZentryxApp(),
        ),
      );
      await tester.pumpAndSettle();
      await _reveal(tester, find.text('Ver mapa y unidades'));
      await tester.tap(find.text('Ver mapa y unidades'));
      await tester.pumpAndSettle();
      expect(find.byType(HomeScreen), findsOneWidget);
      expect(find.text('Modo pasajero'), findsOneWidget);
      await tester.tap(find.byType(CupertinoNavigationBarBackButton));
      await tester.pumpAndSettle();
      expect(find.byType(WelcomeScreen), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'driver mode on welcome runs data/INE verification and opens shared map with emergency SOS',
    (tester) async {
      addTearDown(() => tester.pumpWidget(const SizedBox.shrink()));
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            transitControllerProvider.overrideWith((ref) => _TransitFixture()),
          ],
          child: const ZentryxApp(),
        ),
      );
      await tester.pumpAndSettle();
      await _reveal(tester, find.text('Modo conductor'));
      await tester.tap(find.text('Modo conductor'));
      await tester.pumpAndSettle();

      expect(find.text('Verificación de Operador'), findsOneWidget);
      await _reveal(tester, find.text('Folio 84021 · MEX-1234'));
      await tester.tap(find.text('Folio 84021 · MEX-1234'));
      await tester.pumpAndSettle();
      expect(find.text('Operador Vigente y Asignado'), findsOneWidget);

      await _reveal(tester, find.text('Continuar a Verificación de INE'));
      await tester.tap(find.text('Continuar a Verificación de INE'));
      await tester.pumpAndSettle();

      expect(
        find.text('Toma una foto del anverso y reverso de tu INE'),
        findsOneWidget,
      );
      final galleryButtons = find.text('Subir desde Galería');
      await _reveal(tester, galleryButtons.first);
      await tester.tap(galleryButtons.first);
      await tester.pumpAndSettle();
      await _reveal(tester, galleryButtons.last);
      await tester.tap(galleryButtons.last);
      await tester.pumpAndSettle();

      await _reveal(tester, find.text('Verificar INE y Abrir Mapa de Unidad'));
      await tester.tap(find.text('Verificar INE y Abrir Mapa de Unidad'));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pumpAndSettle();

      expect(find.byType(HomeScreen), findsOneWidget);
      expect(find.text('Modo conductor · MEX-1234'), findsOneWidget);
      expect(
        find.text('BOTÓN DE PÁNICO / EMERGENCIA SOS'),
        findsOneWidget,
      );
    },
  );

  for (final width in [360.0, 390.0, 430.0]) {
    for (final scale in [1.0, 2.0]) {
      for (final brightness in Brightness.values) {
        testWidgets('welcome fits $width scale $scale $brightness', (
          tester,
        ) async {
          tester.view.physicalSize = Size(width, 844);
          tester.view.devicePixelRatio = 1;
          addTearDown(tester.view.resetPhysicalSize);
          addTearDown(tester.view.resetDevicePixelRatio);
          addTearDown(() => tester.pumpWidget(const SizedBox.shrink()));
          final boundary = GlobalKey();
          Widget host(Widget child) => ProviderScope(
            child: CupertinoApp(
              debugShowCheckedModeBanner: false,
              theme: zentryxTheme.copyWith(
                brightness: brightness,
                textTheme: const CupertinoTextThemeData(
                  navTitleTextStyle: TextStyle(
                    fontFamily: 'ReviewFont',
                    fontSize: 17,
                    fontWeight: FontWeight.w600,
                    color: ZentryxColors.ink,
                  ),
                  navActionTextStyle: TextStyle(
                    fontFamily: 'ReviewFont',
                    fontSize: 17,
                    color: ZentryxColors.action,
                  ),
                  textStyle: TextStyle(
                    fontFamily: 'ReviewFont',
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
                  textScaler: TextScaler.linear(scale),
                  padding: const EdgeInsets.only(top: 47, bottom: 34),
                ),
                child: RepaintBoundary(key: boundary, child: child),
              ),
            ),
          );
          await tester.pumpWidget(
            host(WelcomeScreen(onPassenger: () {})),
          );
          await tester.pumpAndSettle();
          expect(tester.takeException(), isNull);
          if (const bool.fromEnvironment('ZENTRYX_CAPTURE_REVIEW')) {
            await _capture(
              tester,
              boundary,
              'welcome-${width.toInt()}-$scale-${brightness.name}',
            );
          }
          await _reveal(tester, find.text('Ver mapa y unidades'));
          expect(tester.takeException(), isNull);
        });
      }
    }
  }
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

Future<void> _reveal(WidgetTester tester, Finder target) async {
  if (target.evaluate().isEmpty) {
    await tester.scrollUntilVisible(
      target,
      180,
      scrollable: find.byType(Scrollable).first,
      maxScrolls: 30,
    );
  } else {
    await tester.ensureVisible(target);
  }
  await tester.pumpAndSettle();
}
