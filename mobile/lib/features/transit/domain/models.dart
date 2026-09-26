double _asDouble(Object? value, [double fallback = 0]) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? fallback;
}

int _asInt(Object? value, [int fallback = 0]) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? fallback;
}

class GeoPoint {
  const GeoPoint(this.lat, this.lon);

  final double lat;
  final double lon;

  factory GeoPoint.fromJson(Map<String, dynamic> json) {
    return GeoPoint(_asDouble(json['lat']), _asDouble(json['lon']));
  }
}

class RouteInfo {
  const RouteInfo({
    required this.routeId,
    required this.serviceId,
    required this.lineLabel,
    required this.networkName,
    required this.originName,
    required this.destinationName,
    required this.forwardLabel,
    required this.reverseLabel,
    required this.path,
  });

  final String routeId;
  final String serviceId;
  final String lineLabel;
  final String networkName;
  final String originName;
  final String destinationName;
  final String forwardLabel;
  final String reverseLabel;
  final List<GeoPoint> path;

  factory RouteInfo.fromJson(Map<String, dynamic> json) {
    final path = (json['path'] as List<dynamic>? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(GeoPoint.fromJson)
        .toList(growable: false);

    return RouteInfo(
      routeId: json['route_id']?.toString() ?? '',
      serviceId: json['service_id']?.toString() ?? '',
      lineLabel: json['line_label']?.toString() ?? 'L2',
      networkName: json['network_name']?.toString() ?? 'Mexibús',
      originName: json['origin_name']?.toString() ?? 'La Quebrada',
      destinationName: json['destination_name']?.toString() ?? 'Las Américas',
      forwardLabel: json['direction_forward_label']?.toString() ?? '',
      reverseLabel: json['direction_reverse_label']?.toString() ?? '',
      path: path,
    );
  }
}

class StationInfo {
  const StationInfo({
    required this.stationId,
    required this.name,
    required this.position,
    required this.order,
  });

  final String stationId;
  final String name;
  final GeoPoint position;
  final int order;

  factory StationInfo.fromJson(Map<String, dynamic> json) {
    return StationInfo(
      stationId: json['station_id']?.toString() ?? '',
      name: json['name']?.toString() ?? 'Estación',
      position: GeoPoint.fromJson(
        (json['position'] as Map?)?.cast<String, dynamic>() ?? const {},
      ),
      order: _asInt(json['order']),
    );
  }
}

class VehicleInfo {
  const VehicleInfo({
    required this.vehicleId,
    required this.routeId,
    required this.status,
    required this.position,
    required this.speedMps,
    required this.headingDeg,
    required this.occupancyLevel,
    required this.direction,
    required this.directionLabel,
    required this.nextStationName,
    required this.distanceRemainingM,
    required this.etaSeconds,
    required this.lastUpdate,
  });

  final String vehicleId;
  final String routeId;
  final String status;
  final GeoPoint? position;
  final double speedMps;
  final double headingDeg;
  final String occupancyLevel;
  final String direction;
  final String directionLabel;
  final String? nextStationName;
  final double? distanceRemainingM;
  final double? etaSeconds;
  final DateTime? lastUpdate;

  bool get isOnline => status == 'online';

  factory VehicleInfo.fromJson(Map<String, dynamic> json) {
    final positionJson = (json['position'] as Map?)?.cast<String, dynamic>();
    final navigation = (json['navigation'] as Map?)?.cast<String, dynamic>() ?? const {};
    final nextStation =
        (navigation['next_station'] as Map?)?.cast<String, dynamic>();
    final lastUpdateRaw = json['last_update']?.toString();

    return VehicleInfo(
      vehicleId: json['vehicle_id']?.toString() ?? '',
      routeId: json['route_id']?.toString() ?? '',
      status: json['status']?.toString() ?? 'unknown',
      position: positionJson == null ? null : GeoPoint.fromJson(positionJson),
      speedMps: _asDouble(json['speed_mps']),
      headingDeg: _asDouble(json['heading_deg']),
      occupancyLevel: json['occupancy_level']?.toString() ?? 'unknown',
      direction: navigation['direction']?.toString() ?? 'unknown',
      directionLabel: navigation['direction_label']?.toString() ?? '',
      nextStationName: nextStation?['name']?.toString(),
      distanceRemainingM: navigation['distance_remaining_m'] == null
          ? null
          : _asDouble(navigation['distance_remaining_m']),
      etaSeconds: navigation['eta_seconds'] == null
          ? null
          : _asDouble(navigation['eta_seconds']),
      lastUpdate: lastUpdateRaw == null ? null : DateTime.tryParse(lastUpdateRaw),
    );
  }
}

class AlertInfo {
  const AlertInfo({
    required this.alertId,
    required this.message,
    required this.severity,
    required this.type,
  });

  final String alertId;
  final String message;
  final String severity;
  final String type;

  factory AlertInfo.fromJson(Map<String, dynamic> json) {
    return AlertInfo(
      alertId: json['alert_id']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      severity: json['severity']?.toString() ?? 'info',
      type: json['type']?.toString() ?? 'service',
    );
  }
}
