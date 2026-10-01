import 'dart:async';

import '../domain/device_telemetry.dart';
import '../domain/device_telemetry_source.dart';

enum SimulatedTelemetryScenario {
  operational,
  disconnected,
  noGps,
  noServer,
  stale,
  waiting,
  syncing,
  failure,
}

/// Standalone chip simulator. Never reads/writes the passenger map or API.
class SimulatedDeviceTelemetrySource implements DeviceTelemetrySource {
  SimulatedDeviceTelemetrySource({
    this.scenario = SimulatedTelemetryScenario.operational,
    this.interval = const Duration(seconds: 2),
    DateTime Function()? clock,
  }) : _clock = clock ?? DateTime.now;
  final SimulatedTelemetryScenario scenario;
  final Duration interval;
  final DateTime Function() _clock;
  final _events = StreamController<DeviceTelemetry>.broadcast();
  Timer? _timer;
  bool _closed = false;
  static const unit = DriverUnit(
    id: 'unit-demo-01',
    name: 'Unidad 01',
    line: 'Mexibús Línea 2',
  );

  @override
  DeviceTelemetry get initial => const DeviceTelemetry(
    deviceId: 'ZTX-GPS-001',
    unit: unit,
    sourceType: TelemetrySourceType.simulated,
    sourceLabel: 'Simulador',
    firmware: 'SIM 1.0',
  );
  @override
  Stream<DeviceTelemetry> get updates => _events.stream;

  /// Deterministic sample allows tests to exercise faults without UI debug controls.
  DeviceTelemetry sampleAt(DateTime instant) {
    final now = instant.toUtc();
    final waiting = scenario == SimulatedTelemetryScenario.waiting;
    final connected = ![
      SimulatedTelemetryScenario.disconnected,
      SimulatedTelemetryScenario.failure,
      SimulatedTelemetryScenario.waiting,
    ].contains(scenario);
    final gps =
        connected &&
        scenario != SimulatedTelemetryScenario.noGps &&
        scenario != SimulatedTelemetryScenario.syncing;
    final stale = scenario == SimulatedTelemetryScenario.stale;
    return DeviceTelemetry(
      deviceId: initial.deviceId,
      unit: unit,
      sourceType: initial.sourceType,
      sourceLabel: initial.sourceLabel,
      firmware: initial.firmware,
      signal: switch (scenario) {
        SimulatedTelemetryScenario.disconnected => DeviceSignal.disconnected,
        SimulatedTelemetryScenario.waiting => DeviceSignal.waiting,
        SimulatedTelemetryScenario.syncing => DeviceSignal.syncing,
        SimulatedTelemetryScenario.failure => DeviceSignal.failure,
        _ => DeviceSignal.ready,
      },
      connected: connected,
      gpsAvailable: gps,
      serverConnected:
          connected && scenario != SimulatedTelemetryScenario.noServer,
      latitude: gps ? 19.62211 : null,
      longitude: gps ? -99.16299 : null,
      accuracyMeters: gps ? 4.0 + (now.second % 3) : null,
      lastPacketAt: (waiting || !connected)
          ? null
          : stale
          ? now.subtract(const Duration(seconds: 30))
          : now,
      lastGpsFixAt: !gps
          ? null
          : stale
          ? now.subtract(const Duration(seconds: 30))
          : now,
    );
  }

  @override
  void start() {
    if (_closed || _timer != null) return;
    _events.add(sampleAt(_clock()));
    _timer = Timer.periodic(interval, (_) => _events.add(sampleAt(_clock())));
  }

  @override
  void pause() {
    _timer?.cancel();
    _timer = null;
  }

  @override
  void dispose() {
    if (_closed) return;
    _closed = true;
    pause();
    unawaited(_events.close());
  }
}
