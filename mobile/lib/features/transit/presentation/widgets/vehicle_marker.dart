import 'dart:math' as math;

import 'package:flutter/cupertino.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';

class AnimatedVehicleLayer extends StatefulWidget {
  const AnimatedVehicleLayer({
    required this.target,
    required this.headingDeg,
    required this.online,
    super.key,
  });

  final LatLng target;
  final double headingDeg;
  final bool online;

  @override
  State<AnimatedVehicleLayer> createState() => _AnimatedVehicleLayerState();
}

class _AnimatedVehicleLayerState extends State<AnimatedVehicleLayer>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late LatLng _fromPosition;
  late LatLng _toPosition;
  late double _fromHeading;
  late double _toHeading;

  @override
  void initState() {
    super.initState();
    _fromPosition = widget.target;
    _toPosition = widget.target;
    _fromHeading = widget.headingDeg;
    _toHeading = widget.headingDeg;
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1900),
      value: 1,
    );
  }

  @override
  void didUpdateWidget(covariant AnimatedVehicleLayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    final positionChanged = oldWidget.target != widget.target;
    final headingChanged = oldWidget.headingDeg != widget.headingDeg;
    if (!positionChanged && !headingChanged) return;

    final eased = Curves.easeOutCubic.transform(_controller.value);
    _fromPosition = _lerpPosition(_fromPosition, _toPosition, eased);
    _fromHeading = _lerpDouble(_fromHeading, _toHeading, eased);
    _toPosition = widget.target;
    _toHeading = _shortestHeadingTarget(_fromHeading, widget.headingDeg);
    _controller.forward(from: 0);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final t = Curves.easeOutCubic.transform(_controller.value);
        final point = _lerpPosition(_fromPosition, _toPosition, t);
        final heading = _lerpDouble(_fromHeading, _toHeading, t);
        return MarkerLayer(
          markers: [
            Marker(
              point: point,
              width: 58,
              height: 58,
              child: RepaintBoundary(
                child: Transform.rotate(
                  angle: heading * math.pi / 180,
                  child: Container(
                    decoration: BoxDecoration(
                      color: CupertinoDynamicColor.resolve(
                        ZentryxColors.ink,
                        context,
                      ),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: const Color(0xFFFFFFFF),
                        width: 3,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: widget.online
                              ? const Color(0x38000000)
                              : const Color(0x22000000),
                          blurRadius: widget.online ? 16 : 10,
                          offset: const Offset(0, 5),
                        ),
                      ],
                    ),
                    child: Stack(
                      alignment: Alignment.center,
                      children: [
                        const Icon(
                          CupertinoIcons.location_north_fill,
                          color: ZentryxColors.accent,
                          size: 26,
                        ),
                        if (!widget.online)
                          Positioned(
                            right: 5,
                            bottom: 5,
                            child: Container(
                              width: 9,
                              height: 9,
                              decoration: const BoxDecoration(
                                color: ZentryxColors.warning,
                                shape: BoxShape.circle,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  LatLng _lerpPosition(LatLng a, LatLng b, double t) {
    return LatLng(
      a.latitude + (b.latitude - a.latitude) * t,
      a.longitude + (b.longitude - a.longitude) * t,
    );
  }

  double _lerpDouble(double a, double b, double t) => a + (b - a) * t;

  double _shortestHeadingTarget(double from, double target) {
    final normalizedTarget = target % 360;
    final normalizedFrom = from % 360;
    var delta = normalizedTarget - normalizedFrom;
    if (delta > 180) delta -= 360;
    if (delta < -180) delta += 360;
    return from + delta;
  }
}
