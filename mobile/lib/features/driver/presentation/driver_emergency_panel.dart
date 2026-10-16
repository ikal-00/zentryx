import 'dart:async';

import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/driver/domain/driver_session.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';

class DriverEmergencyBanner extends StatelessWidget {
  const DriverEmergencyBanner({
    required this.alertMessage,
    required this.onDismiss,
    super.key,
  });

  final String alertMessage;
  final VoidCallback onDismiss;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: ZentryxColors.brandDark,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: ZentryxColors.brand, width: 1.5),
      ),
      child: Row(
        children: [
          const Icon(
            CupertinoIcons.exclamationmark_shield_fill,
            color: ZentryxColors.white,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Alerta enviada a Central con coordenadas actuales',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: ZentryxColors.white,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  alertMessage,
                  style: const TextStyle(
                    fontSize: 11,
                    color: ZentryxColors.brandSoft,
                  ),
                ),
              ],
            ),
          ),
          CupertinoButton(
            padding: EdgeInsets.zero,
            minimumSize: Size.zero,
            onPressed: onDismiss,
            child: const Icon(
              CupertinoIcons.xmark_circle_fill,
              color: ZentryxColors.white,
              size: 18,
            ),
          ),
        ],
      ),
    );
  }
}

class DriverEmergencyPanel extends StatefulWidget {
  const DriverEmergencyPanel({
    required this.session,
    required this.vehicle,
    required this.onEmergencyDispatched,
    super.key,
  });

  final DriverSession session;
  final VehicleInfo? vehicle;
  final ValueChanged<String> onEmergencyDispatched;

  @override
  State<DriverEmergencyPanel> createState() => _DriverEmergencyPanelState();
}

class _DriverEmergencyPanelState extends State<DriverEmergencyPanel> {
  Timer? _holdTimer;
  double _holdProgress = 0.0;
  double _sliderValue = 0.0;
  String _hintText =
      'Anti-toque accidental: mantén presionado 3s o desliza al 100%';
  bool _warningTap = false;

  @override
  void dispose() {
    _holdTimer?.cancel();
    super.dispose();
  }

  void _onSingleTapWarning() {
    HapticFeedback.lightImpact();
    setState(() {
      _warningTap = true;
      _hintText =
          '⚠ Toque simple bloqueado. Mantén presionado 3 segundos o desliza para confirmar.';
    });
  }

  void _startHold() {
    _holdTimer?.cancel();
    HapticFeedback.mediumImpact();
    setState(() {
      _warningTap = false;
      _holdProgress = 0.0;
    });
    const tick = Duration(milliseconds: 50);
    _holdTimer = Timer.periodic(tick, (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      setState(() {
        _holdProgress = (_holdProgress + (50 / 3000)).clamp(0.0, 1.0);
        final remaining = (3.0 * (1.0 - _holdProgress)).clamp(0.0, 3.0);
        _hintText = 'Activando SOS en ${remaining.toStringAsFixed(1)}s...';
      });
      if (_holdProgress >= 1.0) {
        timer.cancel();
        _dispatchAlert('Mantener 3s');
      }
    });
  }

  void _endHoldEarly() {
    if (_holdProgress >= 1.0) return;
    _holdTimer?.cancel();
    if (_holdProgress > 0) {
      setState(() {
        _holdProgress = 0.0;
        _hintText = 'Liberado antes de 3s: alarma cancelada por seguridad.';
      });
    }
  }

  void _dispatchAlert(String method) {
    HapticFeedback.heavyImpact();
    final lat = widget.vehicle?.position?.lat ?? 19.62211;
    final lon = widget.vehicle?.position?.lon ?? -99.16299;
    final station = widget.vehicle?.nextStationName ?? 'Corredor L2';
    final msg =
        'Op. #${widget.session.folio} · ${widget.session.unitPlate} (${widget.vehicle?.vehicleId ?? "unit-demo-01"}) · GPS (${lat.toStringAsFixed(4)}, ${lon.toStringAsFixed(4)}) · $station · Vía $method';
    setState(() {
      _holdProgress = 0.0;
      _sliderValue = 0.0;
      _hintText = '✓ Alerta enviada a Central C5 con coordenadas en vivo.';
    });
    widget.onEmergencyDispatched(msg);
  }

  @override
  Widget build(BuildContext context) {
    final surface = CupertinoDynamicColor.resolve(ZentryxColors.surface, context);
    final line = CupertinoDynamicColor.resolve(ZentryxColors.line, context);
    final ink = CupertinoDynamicColor.resolve(ZentryxColors.ink, context);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFFDCFCE7),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  'CONDUCTOR VERIFICADO · ${widget.session.unitPlate}',
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFF0F7644),
                  ),
                ),
              ),
              const Spacer(),
              Text(
                'Folio #${widget.session.folio}',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: ink,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          GestureDetector(
            onTap: _onSingleTapWarning,
            onTapDown: (_) => _startHold(),
            onTapUp: (_) => _endHoldEarly(),
            onTapCancel: _endHoldEarly,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: ZentryxColors.brand,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  SizedBox(
                    width: 34,
                    height: 34,
                    child: CustomPaint(
                      painter: _RingProgressPainter(progress: _holdProgress),
                      child: const Center(
                        child: Icon(
                          CupertinoIcons.exclamationmark_triangle_fill,
                          color: ZentryxColors.white,
                          size: 16,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'BOTÓN DE PÁNICO / EMERGENCIA SOS',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                            color: ZentryxColors.white,
                          ),
                        ),
                        Text(
                          'Mantener presionado por 3 segundos',
                          style: TextStyle(
                            fontSize: 11,
                            color: ZentryxColors.brandSoft,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Text(
                    _holdProgress > 0
                        ? '${(_holdProgress * 100).round()}%'
                        : '3.0s',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: ZentryxColors.white,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              const Icon(
                CupertinoIcons.arrow_right_circle_fill,
                size: 16,
                color: ZentryxColors.brandStrong,
              ),
              const SizedBox(width: 6),
              const Text(
                'Deslizar SOS:',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Expanded(
                child: CupertinoSlider(
                  value: _sliderValue,
                  min: 0.0,
                  max: 100.0,
                  activeColor: ZentryxColors.brandStrong,
                  thumbColor: ZentryxColors.brandDark,
                  onChanged: (val) => setState(() => _sliderValue = val),
                  onChangeEnd: (val) {
                    if (val >= 95.0) {
                      _dispatchAlert('Deslizar confirmación');
                    } else {
                      setState(() => _sliderValue = 0.0);
                    }
                  },
                ),
              ),
            ],
          ),
          Text(
            _hintText,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: _warningTap
                  ? const Color(0xFFB45309)
                  : CupertinoDynamicColor.resolve(ZentryxColors.muted, context),
            ),
          ),
        ],
      ),
    );
  }
}

class _RingProgressPainter extends CustomPainter {
  const _RingProgressPainter({required this.progress});
  final double progress;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width / 2) - 2;
    canvas.drawCircle(
      center,
      radius,
      Paint()
        ..color = ZentryxColors.brandDark
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3.5,
    );
    if (progress > 0) {
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        -1.5708,
        6.28318 * progress.clamp(0.0, 1.0),
        false,
        Paint()
          ..color = ZentryxColors.white
          ..style = PaintingStyle.stroke
          ..strokeWidth = 3.5
          ..strokeCap = StrokeCap.round,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _RingProgressPainter oldDelegate) =>
      oldDelegate.progress != progress;
}
