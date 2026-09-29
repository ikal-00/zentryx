import 'dart:math' as math;

import 'package:latlong2/latlong.dart';

/// Display-only state. Never feeds filtered coordinates back into API/ETA data.
class VehiclePose {
  const VehiclePose(this.position, this.heading);
  final LatLng position;
  final double heading;
}

double shortestHeadingDelta(double from, double to) =>
    ((to - from + 180) % 360) - 180;

LatLng interpolatePosition(LatLng a, LatLng b, double t) => LatLng(
      a.latitude + (b.latitude - a.latitude) * t,
      a.longitude + shortestHeadingDelta(a.longitude, b.longitude) * t,
    );

bool validPosition(LatLng point) =>
    point.latitude.isFinite &&
    point.longitude.isFinite &&
    point.latitude.abs() <= 90 &&
    point.longitude.abs() <= 180;

/// Interpolates from the currently displayed pose, including interrupted moves.
/// Cadence is measured at reception, independent of wall-clock adjustments.
class VehicleMotion {
  VehicleMotion(LatLng initial, double heading, {DateTime? timestamp})
      : _from = VehiclePose(initial, heading.isFinite ? heading % 360 : 0),
        _to = VehiclePose(initial, heading.isFinite ? heading % 360 : 0),
        _lastTimestamp = timestamp;

  static const _distance = Distance();
  VehiclePose _from;
  VehiclePose _to;
  LatLng? _candidate;
  DateTime? _candidateTimestamp;
  Duration? _lastReceived;
  DateTime? _lastTimestamp;
  Duration duration = const Duration(seconds: 2);

  VehiclePose sample(double fraction) {
    final t = fraction.clamp(0.0, 1.0).toDouble();
    return VehiclePose(
      interpolatePosition(_from.position, _to.position, t),
      (_from.heading + shortestHeadingDelta(_from.heading, _to.heading) * t) %
          360,
    );
  }

  bool retarget({
    required LatLng target,
    required double heading,
    required Duration receivedAt,
    required double fraction,
    DateTime? timestamp,
    double? accuracyM,
  }) {
    if (!validPosition(target)) return false;
    if (timestamp != null &&
        _lastTimestamp != null &&
        !timestamp.isAfter(_lastTimestamp!)) {
      return false;
    }
    final elapsed = _lastReceived == null
        ? 2.0
        : (receivedAt - _lastReceived!).inMicroseconds / 1000000;
    final meters = _distance.as(LengthUnit.Meter, _to.position, target);
    final accuracy = accuracyM != null && accuracyM.isFinite
        ? accuracyM.clamp(0.0, 80.0)
        : 15.0;
    final plausible = math.max(60.0, 55 * elapsed.clamp(0.5, 10.0) + accuracy);
    // A single bad fix must not drag the vehicle/camera across the city.
    // Two consistent distant fixes permit a bounded, animated reacquisition.
    if (meters > plausible) {
      final confirmed = _candidate != null &&
          (timestamp == null || _candidateTimestamp == null || timestamp.isAfter(_candidateTimestamp!)) &&
          _distance.as(LengthUnit.Meter, _candidate!, target) < 100;
      _candidate = target;
      _candidateTimestamp = timestamp;
      if (!confirmed) return false;
    }
    _candidate = null;
    _candidateTimestamp = null;
    _lastReceived = receivedAt;
    _lastTimestamp = timestamp ?? _lastTimestamp;
    final current = sample(fraction);
    final destination = meters < 1.5 ? _to.position : target;
    final resolvedHeading = heading.isFinite
        ? heading
        : meters >= 2
            ? _distance.bearing(_to.position, target)
            : _to.heading;
    if (destination == _to.position &&
        shortestHeadingDelta(_to.heading, resolvedHeading).abs() < 1) {
      return false;
    }
    _from = current;
    _to = VehiclePose(destination, resolvedHeading);
    // Linear motion avoids braking to zero at every polling boundary. Larger
    // reacquisitions take longer, while ordinary samples follow their cadence.
    final travelSeconds = _distance.as(
          LengthUnit.Meter, current.position, destination) /
        45;
    duration = Duration(
      milliseconds:
          (math.max(elapsed.clamp(0.8, 3.0), travelSeconds).clamp(0.8, 5.0) *
                  1000)
              .round(),
    );
    return true;
  }
}
