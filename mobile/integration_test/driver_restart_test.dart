import 'package:flutter/cupertino.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:zentryx_mobile/app/zentryx_app.dart';
import 'package:zentryx_mobile/features/driver/application/driver_session.dart';
import 'package:zentryx_mobile/features/driver/data/driver_session_store.dart';
import 'package:zentryx_mobile/features/driver/presentation/device_diagnostics_screen.dart';
import 'package:zentryx_mobile/features/driver/presentation/prepare_trip_screen.dart';

// Run twice on the same simulator: write then restore. Each invocation launches
// a new native process and uses the real preferences plugin, never a fake store.
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  const phase = String.fromEnvironment(
    'ZENTRYX_RESTART_PHASE',
    defaultValue: 'write',
  );
  const marker = 'zentryx.test.expected-start';
  testWidgets('native driver flow and process restart: $phase', (tester) async {
    final prefs = SharedPreferencesAsync();
    if (phase == 'write') {
      await prefs.remove(PreferencesDriverSessionStore.key);
      await prefs.remove(marker);
    }
    await tester.pumpWidget(const ProviderScope(child: ZentryxApp()));
    await tester.pumpAndSettle();
    await reveal(tester, find.text('Soy conductor'));
    await tester.tap(find.text('Soy conductor'));
    await tester.pumpAndSettle();
    final container = ProviderScope.containerOf(
      tester.element(find.byType(ZentryxApp)),
    );
    await container.read(driverSessionProvider.notifier).ready;
    await tester.pumpAndSettle();
    if (phase == 'write') {
      expect(find.byType(PrepareTripScreen), findsOneWidget);
      await reveal(tester, find.text('Iniciar recorrido'));
      await tester.tap(find.text('Iniciar recorrido'));
      await waitFor(tester, find.text('Recorrido activo'));
      final startedAt = container.read(driverSessionProvider).startedAt!;
      await prefs.setString(marker, startedAt.toUtc().toIso8601String());
      await reveal(tester, find.text('Ver diagnóstico'));
      await tester.tap(find.text('Ver diagnóstico'));
      await tester.pumpAndSettle();
      expect(find.byType(DeviceDiagnosticsScreen), findsOneWidget);
      expect(find.text('Entorno de simulación'), findsOneWidget);
      await tester.tap(find.byType(CupertinoNavigationBarBackButton));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Reportar incidente'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Tráfico'));
      await waitFor(tester, find.text('Registrado localmente: Tráfico'));
      expect(container.read(driverSessionProvider).startedAt, startedAt);
    } else {
      final expected = await prefs.getString(marker);
      expect(
        expected,
        isNotNull,
        reason: 'The write phase must run in a previous process.',
      );
      final session = container.read(driverSessionProvider);
      expect(session.startedAt!.toUtc().toIso8601String(), expected);
      expect(session.unit!.id, 'unit-demo-01');
      expect(session.lastIncident, IncidentType.traffic);
      expect(session.reportCount, 1);
      expect(find.text('Recorrido activo'), findsOneWidget);
      expect(find.text('Iniciar recorrido'), findsNothing);
      expect(find.text('Registrado localmente: Tráfico'), findsOneWidget);
      await prefs.remove(marker);
      await prefs.remove(PreferencesDriverSessionStore.key);
    }
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
  });
}

Future<void> waitFor(WidgetTester tester, Finder finder) async {
  for (var i = 0; i < 50 && finder.evaluate().isEmpty; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
  await tester.pumpAndSettle();
  expect(finder, findsOneWidget);
}

Future<void> reveal(WidgetTester tester, Finder finder) async {
  if (finder.evaluate().isEmpty) {
    await tester.scrollUntilVisible(
      finder,
      160,
      scrollable: find.byType(Scrollable).first,
      maxScrolls: 40,
    );
  } else {
    await tester.ensureVisible(finder.first);
  }
  await tester.pumpAndSettle();
}
