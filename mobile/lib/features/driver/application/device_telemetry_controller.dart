import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/simulated_device_telemetry_source.dart';
import '../domain/device_telemetry.dart';
import '../domain/device_telemetry_source.dart';

/// Composition point for a future hardware/phone/API adapter.
final deviceTelemetrySourceProvider =
    Provider.autoDispose<DeviceTelemetrySource>((ref) {
      final source = SimulatedDeviceTelemetrySource();
      ref.onDispose(source.dispose);
      return source;
    });
final deviceTelemetryProvider =
    StateNotifierProvider.autoDispose<
      DeviceTelemetryController,
      DeviceTelemetry
    >(
      (ref) =>
          DeviceTelemetryController(ref.watch(deviceTelemetrySourceProvider)),
    );

class DeviceTelemetryController extends StateNotifier<DeviceTelemetry> {
  DeviceTelemetryController(this._source) : super(_source.initial) {
    _subscription = _source.updates.listen(
      (packet) {
        if (mounted) state = packet;
      },
      onError: (Object error, StackTrace trace) {
        if (mounted) state = state.withSignal(DeviceSignal.failure);
      },
      onDone: () {
        if (mounted) state = state.withSignal(DeviceSignal.disconnected);
      },
    );
    resume();
  }
  final DeviceTelemetrySource _source;
  late final StreamSubscription<DeviceTelemetry> _subscription;
  void pause() => _source.pause();
  void resume() {
    try {
      _source.start();
    } catch (_) {
      state = state.withSignal(DeviceSignal.failure);
    }
  }

  @override
  void dispose() {
    unawaited(_subscription.cancel());
    _source.pause();
    super.dispose();
  }
}
