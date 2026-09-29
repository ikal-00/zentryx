import 'dart:math' as math;

import 'package:flutter/cupertino.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart' show LatLng;
import '../motion/vehicle_motion.dart';

class AnimatedVehicleLayer extends StatefulWidget {
  const AnimatedVehicleLayer({
    required this.target,
    required this.headingDeg,
    required this.online,
    required this.onVisualPosition,
    this.timestamp,
    this.accuracyM,
    super.key,
  });
  final LatLng target;
  final double headingDeg;
  final bool online;
  final DateTime? timestamp;
  final double? accuracyM;
  final ValueChanged<LatLng> onVisualPosition;

  @override
  State<AnimatedVehicleLayer> createState() => _AnimatedVehicleLayerState();
}

class _AnimatedVehicleLayerState extends State<AnimatedVehicleLayer>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final VehicleMotion _motion;
  final Stopwatch _clock = Stopwatch();

  @override
  void initState() {
    super.initState();
    _motion = VehicleMotion(widget.target, widget.headingDeg, timestamp: widget.timestamp);
    _clock.start();
    _controller = AnimationController(vsync: this, value: 1)
      ..addListener(_publishPosition);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _publishPosition();
    });
  }

  void _publishPosition() =>
      widget.onVisualPosition(_motion.sample(_controller.value).position);

  @override
  void didUpdateWidget(covariant AnimatedVehicleLayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.target == widget.target &&
        oldWidget.headingDeg == widget.headingDeg &&
        oldWidget.timestamp == widget.timestamp) {
      return;
    }
    if (_motion.retarget(
      target: widget.target,
      heading: widget.headingDeg,
      timestamp: widget.timestamp,
      accuracyM: widget.accuracyM,
      receivedAt: _clock.elapsed,
      fraction: _controller.value,
    )) {
      _controller.duration = _motion.duration;
      _controller.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _clock.stop();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: _controller,
        child: RepaintBoundary(
          child: CustomPaint(
            size: const Size(58, 58),
            painter: ZentryxBusPainter(online: widget.online),
          ),
        ),
        builder: (context, child) {
          final pose = _motion.sample(_controller.value);
          return IgnorePointer(child: MarkerLayer(markers: [
            Marker(
              point: pose.position,
              width: 58,
              height: 58,
              child: Semantics(
                label: widget.online ? 'Autobús en vivo' : 'Última ubicación del autobús',
                child: Transform.rotate(
                  angle: pose.heading * math.pi / 180,
                  child: child,
                ),
              ),
            ),
          ]));
        },
      );
}

/// Original north-facing vector bus; crisp at every device pixel ratio.
class ZentryxBusPainter extends CustomPainter {
  const ZentryxBusPainter({required this.online});
  final bool online;

  @override
  void paint(Canvas canvas, Size size) {
    canvas.save();
    canvas.scale(size.width / 58, size.height / 58);
    final body = RRect.fromRectAndRadius(
      const Rect.fromLTWH(14, 5, 30, 48), const Radius.circular(9));
    canvas.drawShadow(Path()..addRRect(body), ZentryxColors.busShadow, 5, true);
    final paint = Paint();
    // White separation, blue body, turquoise roof and unmistakable windshield.
    canvas.drawRRect(body.inflate(2.5), paint..color = ZentryxColors.white);
    canvas.drawRRect(body, paint..color = ZentryxColors.busBody);
    canvas.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(18, 8, 22, 40), const Radius.circular(6)),
      paint..color = online ? ZentryxColors.busRoof : ZentryxColors.busOffline);
    canvas.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(19, 12, 20, 9), const Radius.circular(3)),
      paint..color = ZentryxColors.busGlass);
    canvas.drawLine(const Offset(21, 14), const Offset(31, 14),
      paint..color = ZentryxColors.busReflection..strokeWidth = 2);
    canvas.drawRRect(
      RRect.fromRectAndRadius(const Rect.fromLTWH(23, 26, 12, 13), const Radius.circular(3)),
      paint..color = ZentryxColors.busRoofHighlight);
    for (final x in [11.0, 43.0]) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(Rect.fromLTWH(x, 15, 4, 7), const Radius.circular(2)),
        paint..color = ZentryxColors.busBody);
    }
    for (final x in [19.0, 36.0]) {
      canvas.drawCircle(Offset(x, 9), 1.5, paint..color = ZentryxColors.white);
      canvas.drawCircle(Offset(x, 49), 1.5, paint..color = ZentryxColors.busTailLight);
    }
    if (!online) {
      canvas.drawCircle(const Offset(44, 44), 5, paint..color = ZentryxColors.busOfflineBadge);
    }
    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant ZentryxBusPainter oldDelegate) => online != oldDelegate.online;
}
