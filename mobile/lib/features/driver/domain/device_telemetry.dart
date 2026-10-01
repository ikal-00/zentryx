/// Internal app values, not a wire protocol or a replacement for contracts/.
enum TelemetrySourceType { simulated, hardware, phone, remote, unknown }

enum DeviceSignal { waiting, syncing, ready, disconnected, failure }

enum TelemetryHealth {
  operational,
  waiting,
  syncing,
  disconnected,
  noGps,
  noServer,
  stale,
  failure,
}

class DriverUnit {
  const DriverUnit({required this.id, required this.name, required this.line});
  final String id;
  final String name;
  final String line;
  Map<String, Object> toJson() => {'id': id, 'name': name, 'line': line};
  factory DriverUnit.fromJson(Map<String, dynamic> json) {
    for (final key in ['id', 'name', 'line']) {
      if (json[key] is! String || (json[key] as String).trim().isEmpty) {
        throw const FormatException('Invalid unit');
      }
    }
    return DriverUnit(
      id: json['id'] as String,
      name: json['name'] as String,
      line: json['line'] as String,
    );
  }
}

class DeviceTelemetry {
  const DeviceTelemetry({
    required this.deviceId,
    required this.unit,
    required this.sourceType,
    required this.sourceLabel,
    this.firmware,
    this.signal = DeviceSignal.waiting,
    this.connected = false,
    this.gpsAvailable = false,
    this.serverConnected = false,
    this.latitude,
    this.longitude,
    this.accuracyMeters,
    this.lastPacketAt,
    this.lastGpsFixAt,
  });

  final String deviceId;
  final DriverUnit unit;
  final TelemetrySourceType sourceType;
  final String sourceLabel;
  final String? firmware;
  final DeviceSignal signal;
  final bool connected;
  final bool gpsAvailable;
  final bool serverConnected;
  final double? latitude;
  final double? longitude;
  final double? accuracyMeters;

  /// UTC instants. Adapters must convert device clocks to trustworthy instants.
  final DateTime? lastPacketAt;
  final DateTime? lastGpsFixAt;
  static const staleAfter = Duration(seconds: 10);
  bool get simulated => sourceType == TelemetrySourceType.simulated;
  bool get validPosition =>
      latitude != null &&
      longitude != null &&
      latitude!.isFinite &&
      longitude!.isFinite &&
      latitude!.abs() <= 90 &&
      longitude!.abs() <= 180;
  bool get validAccuracy =>
      accuracyMeters != null &&
      accuracyMeters!.isFinite &&
      accuracyMeters! >= 0;

  bool fresh(DateTime? stamp, DateTime now) =>
      stamp != null &&
      now.difference(stamp) <= staleAfter &&
      !stamp.isAfter(now.add(const Duration(seconds: 2)));

  TelemetryHealth healthAt(DateTime now) {
    if (signal == DeviceSignal.failure) return TelemetryHealth.failure;
    if (signal == DeviceSignal.disconnected) {
      return TelemetryHealth.disconnected;
    }
    if (signal == DeviceSignal.waiting) return TelemetryHealth.waiting;
    if (signal == DeviceSignal.syncing) return TelemetryHealth.syncing;
    if (!connected) return TelemetryHealth.disconnected;
    if (lastPacketAt == null) return TelemetryHealth.waiting;
    if (!fresh(lastPacketAt, now)) return TelemetryHealth.stale;
    if (!gpsAvailable || !validPosition || !fresh(lastGpsFixAt, now)) {
      return TelemetryHealth.noGps;
    }
    if (!serverConnected) return TelemetryHealth.noServer;
    return TelemetryHealth.operational;
  }

  DeviceTelemetry withSignal(DeviceSignal value) => DeviceTelemetry(
    deviceId: deviceId,
    unit: unit,
    sourceType: sourceType,
    sourceLabel: sourceLabel,
    firmware: firmware,
    signal: value,
    connected: false,
    latitude: latitude,
    longitude: longitude,
    accuracyMeters: accuracyMeters,
    lastPacketAt: lastPacketAt,
    lastGpsFixAt: lastGpsFixAt,
  );
}
