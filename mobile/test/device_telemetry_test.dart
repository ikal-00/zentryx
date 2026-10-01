import 'package:fake_async/fake_async.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:zentryx_mobile/features/driver/domain/device_telemetry.dart';
import 'package:zentryx_mobile/features/driver/data/simulated_device_telemetry_source.dart';
import 'package:zentryx_mobile/features/driver/application/device_telemetry_controller.dart';

import 'driver_test_support.dart';

void main() {
  final now = DateTime.utc(2026, 10, 1);
  const expectations = {
    SimulatedTelemetryScenario.operational: TelemetryHealth.operational,
    SimulatedTelemetryScenario.disconnected: TelemetryHealth.disconnected,
    SimulatedTelemetryScenario.noGps: TelemetryHealth.noGps,
    SimulatedTelemetryScenario.noServer: TelemetryHealth.noServer,
    SimulatedTelemetryScenario.stale: TelemetryHealth.stale,
    SimulatedTelemetryScenario.waiting: TelemetryHealth.waiting,
    SimulatedTelemetryScenario.syncing: TelemetryHealth.syncing,
    SimulatedTelemetryScenario.failure: TelemetryHealth.failure,
  };
  for (final entry in expectations.entries) {
    test('simulator exposes ${entry.key.name} honestly', () {
      final source = SimulatedDeviceTelemetrySource(scenario: entry.key);
      addTearDown(source.dispose);
      final sample = source.sampleAt(now);
      expect(sample.healthAt(now), entry.value);
      expect(sample.sourceType, TelemetrySourceType.simulated);
      expect(sample.unit.id, 'unit-demo-01');
      expect(sample.deviceId, 'ZTX-GPS-001');
    });
  }
  test('unchanged packet becomes stale; future timestamp cannot be live', () {
    final source = SimulatedDeviceTelemetrySource();
    addTearDown(source.dispose);
    final sample = source.sampleAt(now);
    expect(
      sample.healthAt(now.add(const Duration(seconds: 11))),
      TelemetryHealth.stale,
    );
    expect(
      sample.healthAt(now.subtract(const Duration(minutes: 1))),
      TelemetryHealth.stale,
    );
  });
  test('UTC timestamps preserve instants and packet reception cannot freshen an old fix', () {
    final source = SimulatedDeviceTelemetrySource();
    addTearDown(source.dispose);
    final sample = source.sampleAt(DateTime.parse('2026-09-30T18:00:00-06:00'));
    expect(sample.lastPacketAt, DateTime.utc(2026, 10, 1));
    expect(sample.lastPacketAt!.isUtc, isTrue);
    final oldFix = DeviceTelemetry(
      deviceId: 'hardware-test',
      unit: sample.unit,
      sourceType: TelemetrySourceType.hardware,
      sourceLabel: 'Test',
      signal: DeviceSignal.ready,
      connected: true,
      gpsAvailable: true,
      serverConnected: true,
      latitude: 19,
      longitude: -99,
      lastPacketAt: now,
      lastGpsFixAt: now.subtract(const Duration(seconds: 11)),
    );
    expect(oldFix.healthAt(now), TelemetryHealth.noGps);
    expect(
      sample.healthAt(now.add(const Duration(seconds: 10))),
      TelemetryHealth.operational,
    );
  });
  test('simulator has one timer and cancels it on pause and dispose', () {
    fakeAsync((async) {
      var time = now;
      final source = SimulatedDeviceTelemetrySource(clock: () => time);
      final packets = <DeviceTelemetry>[];
      var streamClosed = false;
      source.updates.listen(packets.add, onDone: () => streamClosed = true);
      source.start();
      source.start();
      async.flushMicrotasks();
      expect(packets.length, 1);
      expect(async.periodicTimerCount, 1);
      async.elapse(const Duration(seconds: 4));
      expect(packets.length, 3);
      source.pause();
      expect(async.periodicTimerCount, 0);
      async.elapse(const Duration(seconds: 20));
      expect(packets.length, 3);
      time = now.add(const Duration(seconds: 24));
      source.start();
      async.flushMicrotasks();
      expect(packets.length, 4);
      expect(packets.last.lastPacketAt, time);
      source.dispose();
      async.elapse(const Duration(seconds: 20));
      expect(packets.length, 4);
      expect(async.periodicTimerCount, 0);
      expect(streamClosed, isTrue);
      expect(async.pendingTimers, isEmpty);
    });
  });
  test(
    'source errors and stream completion become failure/disconnected states',
    () async {
      final source = FixedTelemetrySource(demoPacket());
      final controller = DeviceTelemetryController(source);
      source.events.addError(StateError('link failed'), StackTrace.current);
      await Future<void>.delayed(Duration.zero);
      expect(
        controller.state.healthAt(DateTime.now()),
        TelemetryHealth.failure,
      );
      await source.events.close();
      expect(
        controller.state.healthAt(DateTime.now()),
        TelemetryHealth.disconnected,
      );
      controller.dispose();
    },
  );
  test('invalid coordinates never count as an available GPS fix', () {
    final data = DeviceTelemetry(
      deviceId: 'test',
      unit: SimulatedDeviceTelemetrySource.unit,
      sourceType: TelemetrySourceType.hardware,
      sourceLabel: 'Test adapter',
      signal: DeviceSignal.ready,
      connected: true,
      gpsAvailable: true,
      serverConnected: true,
      latitude: double.nan,
      longitude: 250,
      accuracyMeters: -4,
      lastPacketAt: now,
      lastGpsFixAt: now,
    );
    expect(data.healthAt(now), TelemetryHealth.noGps);
    expect(data.validAccuracy, isFalse);
  });
}
