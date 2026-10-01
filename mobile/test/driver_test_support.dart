import 'dart:async';

import 'package:zentryx_mobile/features/driver/data/driver_session_store.dart';
import 'package:zentryx_mobile/features/driver/domain/device_telemetry.dart';
import 'package:zentryx_mobile/features/driver/domain/device_telemetry_source.dart';
import 'package:zentryx_mobile/features/driver/data/simulated_device_telemetry_source.dart';

class MemorySessionStore implements DriverSessionStore {
  MemorySessionStore([this.value]);
  String? value;
  bool failRead = false;
  bool failWrite = false;
  int writes = 0;
  @override
  Future<String?> read() async {
    if (failRead) throw StateError('read failed');
    return value;
  }

  @override
  Future<void> write(String data) async {
    if (failWrite) throw StateError('write failed');
    value = data;
    writes++;
  }
}

class FixedTelemetrySource implements DeviceTelemetrySource {
  FixedTelemetrySource(this.initial);
  @override
  final DeviceTelemetry initial;
  final events = StreamController<DeviceTelemetry>.broadcast();
  @override
  Stream<DeviceTelemetry> get updates => events.stream;
  @override
  void start() {}
  @override
  void pause() {}
  @override
  void dispose() {
    unawaited(events.close());
  }
}

DeviceTelemetry demoPacket([
  SimulatedTelemetryScenario scenario = SimulatedTelemetryScenario.operational,
]) {
  final source = SimulatedDeviceTelemetrySource(scenario: scenario);
  final sample = source.sampleAt(DateTime.now());
  source.dispose();
  return sample;
}
