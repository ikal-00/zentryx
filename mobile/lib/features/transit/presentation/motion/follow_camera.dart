import 'package:latlong2/latlong.dart';
import 'vehicle_motion.dart';

/// Pure camera policy, separate from telemetry and map rendering.
class FollowCamera {
  bool following = true;
  void explore() => following = false;
  void resume() => following = true;

  LatLng? step(LatLng center, LatLng target, double zoom, double elapsedSeconds) {
    if (!following) return null;
    final distance = const Distance().as(LengthUnit.Meter, center, target);
    // About two screen pixels at the current zoom near the pilot's latitude.
    final threshold = 2 * 147000 / (1 << zoom.floor().clamp(0, 22));
    if (distance <= threshold) return null;
    // Stable exponential response; no per-GPS recenter and no zoom changes.
    final t = 1 - _decay(elapsedSeconds.clamp(0.0, 0.1));
    return interpolatePosition(center, target, t);
  }

  double _decay(double seconds) {
    // Rational approximation is stable even after a background/resume gap.
    return 1 / (1 + seconds * 7);
  }
}
