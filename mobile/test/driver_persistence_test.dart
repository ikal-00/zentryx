import 'package:flutter_test/flutter_test.dart';
import 'package:zentryx_mobile/features/driver/application/driver_session.dart';
import 'package:zentryx_mobile/features/driver/data/driver_session_store.dart';
import 'package:zentryx_mobile/features/driver/domain/device_telemetry.dart';

import 'driver_test_support.dart';

const selectedUnit = DriverUnit(
  id: 'unit-42',
  name: 'Unidad 42',
  line: 'Línea asignada',
);
void main() {
  test('fresh controller restores exact start, selected unit and report after restart', () async {
    final store = MemorySessionStore();
    final first = DriverSessionController(store);
    await first.start(selectedUnit); // Must wait for the initial read.
    final started = first.state.startedAt;
    await first.report(IncidentType.closedStation);
    final reportTime = first.state.reportedAt;
    first.dispose();
    final second = DriverSessionController(store);
    addTearDown(second.dispose);
    await second.ready;
    expect(second.state.active, isTrue);
    expect(second.state.startedAt, started);
    expect(second.state.unit!.id, selectedUnit.id);
    expect(second.state.lastIncident, IncidentType.closedStation);
    expect(second.state.reportedAt, reportTime);
    expect(store.value, isNot(contains('latitude')));
    final writes = store.writes;
    await Future<void>.delayed(const Duration(milliseconds: 20));
    expect(
      store.writes,
      writes,
    ); // Elapsed time is reconstructed, never saved per tick.
  });
  test('stop is persisted and cannot resurrect the previous trip', () async {
    final store = MemorySessionStore();
    final first = DriverSessionController(store);
    await first.start(selectedUnit);
    await first.report(IncidentType.traffic);
    await first.stop();
    first.dispose();
    final restored = DriverSessionController(store);
    addTearDown(restored.dispose);
    await restored.ready;
    expect(restored.state.active, isFalse);
    expect(restored.state.unit!.id, selectedUnit.id);
    expect(restored.state.lastIncident, IncidentType.traffic);
  });
  test(
    'read failure blocks overwriting an unknown saved session and can retry',
    () async {
      final store = MemorySessionStore()..failRead = true;
      final controller = DriverSessionController(store);
      addTearDown(controller.dispose);
      expect(await controller.start(selectedUnit), isFalse);
      expect(store.writes, 0);
      expect(controller.state.storageError, isNotNull);
      store.failRead = false;
      await controller.retryRestore();
      expect(await controller.start(selectedUnit), isTrue);
    },
  );
  test(
    'write failures preserve the previous state and never confirm an incident',
    () async {
      final store = MemorySessionStore();
      final controller = DriverSessionController(store);
      addTearDown(controller.dispose);
      await controller.start(selectedUnit);
      store.failWrite = true;
      expect(await controller.report(IncidentType.accident), isFalse);
      expect(controller.state.lastIncident, isNull);
      expect(await controller.stop(), isFalse);
      expect(controller.state.active, isTrue);
      store.failWrite = false;
      expect(await controller.stop(), isTrue);
    },
  );
  test(
    'queued operations are stored in order even with slow persistence',
    () async {
      final store = _SlowStore();
      final controller = DriverSessionController(store);
      addTearDown(controller.dispose);
      final start = controller.start(selectedUnit);
      final report = controller.report(IncidentType.stopped);
      final stop = controller.stop();
      expect(await Future.wait([start, report, stop]), [true, true, true]);
      final decoded = DriverSession.decode(store.value!);
      expect(decoded.active, isFalse);
      expect(decoded.lastIncident, IncidentType.stopped);
    },
  );
  for (final raw in [
    'broken',
    '{"version":99}',
    '{"version":1,"startedAt":"bad"}',
  ]) {
    test('invalid stored session is not silently overwritten: $raw', () async {
      final store = MemorySessionStore(raw);
      final controller = DriverSessionController(store);
      addTearDown(controller.dispose);
      await controller.ready;
      expect(controller.state.restored, isFalse);
      expect(await controller.start(selectedUnit), isFalse);
      expect(store.value, raw);
    });
  }
}

class _SlowStore implements DriverSessionStore {
  String? value;
  @override
  Future<String?> read() async {
    await Future<void>.delayed(const Duration(milliseconds: 5));
    return value;
  }

  @override
  Future<void> write(String data) async {
    await Future<void>.delayed(const Duration(milliseconds: 5));
    value = data;
  }
}
