import 'device_telemetry.dart';

/// A single owner subscribes before start. start/resume are idempotent.
/// Implementations report async failures through the stream, never the UI.
abstract interface class DeviceTelemetrySource {
  DeviceTelemetry get initial;
  Stream<DeviceTelemetry> get updates;
  void start();
  void pause();
  void dispose();
}
