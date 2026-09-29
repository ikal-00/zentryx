import 'package:flutter_test/flutter_test.dart';
import 'package:latlong2/latlong.dart';
import 'package:zentryx_mobile/features/transit/presentation/motion/vehicle_motion.dart';
import 'package:zentryx_mobile/features/transit/presentation/motion/follow_camera.dart';

void main() {
  const start = LatLng(19.62, -99.16);
  const east = LatLng(19.62, -99.1598);

  test('angular interpolation takes shortest path across north in both directions', () {
    expect(shortestHeadingDelta(350, 10), 20);
    expect(shortestHeadingDelta(10, 350), -20);
    expect(shortestHeadingDelta(359, 0), 1);
    final motion = VehicleMotion(start, 350);
    motion.retarget(target: east, heading: 10,
        receivedAt: const Duration(seconds: 2), fraction: 1);
    expect(motion.sample(0.5).heading, closeTo(0, 0.001));
  });

  test('position is linear and reaches both endpoints without overshoot', () {
    final motion = VehicleMotion(start, 90);
    motion.retarget(target: east, heading: 90,
        receivedAt: const Duration(seconds: 2), fraction: 1);
    expect(motion.sample(0).position, start);
    expect(motion.sample(0.5).position.longitude, closeTo(-99.1599, 1e-8));
    expect(motion.sample(2).position.longitude, closeTo(east.longitude, 1e-8));
  });

  test('retarget while moving starts at displayed position and heading', () {
    final motion = VehicleMotion(start, 350);
    motion.retarget(target: east, heading: 10,
        receivedAt: const Duration(seconds: 2), fraction: 1);
    final halfway = motion.sample(0.5);
    motion.retarget(target: const LatLng(19.6202, -99.1598), heading: 45,
        receivedAt: const Duration(seconds: 3), fraction: 0.5);
    expect(motion.sample(0).position, halfway.position);
    expect(motion.sample(0).heading, halfway.heading);
    expect(motion.duration.inMilliseconds, 1000);
  });

  test('one GPS jump is rejected, two fresh consistent fixes reacquire smoothly', () {
    final motion = VehicleMotion(start, 0);
    final timestamp = DateTime.utc(2026, 9, 28);
    const far = LatLng(19.72, -99.16);
    expect(motion.retarget(target: far, heading: 0, timestamp: timestamp,
        receivedAt: const Duration(seconds: 2), fraction: 1), isFalse);
    expect(motion.retarget(target: far, heading: 0, timestamp: timestamp,
        receivedAt: const Duration(seconds: 4), fraction: 1), isFalse);
    expect(motion.retarget(target: far, heading: 0, timestamp: timestamp.add(const Duration(seconds: 2)),
        receivedAt: const Duration(seconds: 6), fraction: 1), isTrue);
    expect(motion.sample(0).position, start);
    expect(motion.duration.inSeconds, 5);
  });

  test('invalid and out-of-order fixes cannot change the display target', () {
    final now = DateTime.utc(2026, 9, 28);
    final motion = VehicleMotion(start, 90, timestamp: now);
    expect(motion.retarget(target: east, heading: 0,
        timestamp: now.subtract(const Duration(seconds: 2)),
        receivedAt: const Duration(seconds: 2), fraction: 1), isFalse);
    expect(validPosition(const LatLng(91, 0)), isFalse);
    expect(motion.sample(1).position, start);
  });

  test('missing heading derives bearing and tiny GPS jitter is held', () {
    final motion = VehicleMotion(start, 0);
    expect(motion.retarget(target: const LatLng(19.620001, -99.16), heading: 0,
        receivedAt: const Duration(seconds: 2), fraction: 1), isFalse);
    motion.retarget(target: east, heading: double.nan,
        receivedAt: const Duration(seconds: 4), fraction: 1);
    expect(motion.sample(1).heading, closeTo(90, 0.1));
  });

  test('camera dead zone stops jitter, gestures pause, resume eases without teleport', () {
    final camera = FollowCamera();
    expect(camera.step(start, const LatLng(19.620001, -99.16), 16, 0.016), isNull);
    camera.explore();
    expect(camera.step(start, east, 16, 0.016), isNull);
    camera.resume();
    final point = camera.step(start, east, 16, 0.016)!;
    expect(point.longitude, greaterThan(start.longitude));
    expect(point.longitude, lessThan(east.longitude));
  });
}
