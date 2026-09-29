import 'package:flutter/cupertino.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';

class ZentryxMark extends StatelessWidget {
  const ZentryxMark({super.key, this.size = 34});

  final double size;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size.square(size),
      painter: _ZentryxMarkPainter(
        ink: ZentryxColors.brandDark,
        accent: ZentryxColors.brand,
      ),
    );
  }
}

class _ZentryxMarkPainter extends CustomPainter {
  const _ZentryxMarkPainter({required this.ink, required this.accent});

  final Color ink;
  final Color accent;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    final front = Path()
      ..moveTo(size.width * 0.50, size.height * 0.08)
      ..lineTo(size.width * 0.90, size.height * 0.82)
      ..lineTo(size.width * 0.16, size.height * 0.70)
      ..close();

    final side = Path()
      ..moveTo(size.width * 0.16, size.height * 0.70)
      ..lineTo(size.width * 0.90, size.height * 0.82)
      ..lineTo(size.width * 0.76, size.height * 0.94)
      ..lineTo(size.width * 0.22, size.height * 0.82)
      ..close();

    canvas.drawShadow(front, ZentryxColors.markShadow, size.width * 0.09, true);

    canvas.drawPath(
      side,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            ink.withValues(alpha: 0.95),
            ink.withValues(alpha: 0.55),
          ],
        ).createShader(rect),
    );

    canvas.drawPath(
      front,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomRight,
          colors: [accent, ink],
          stops: const [0.0, 1.0],
        ).createShader(rect),
    );

    final highlight = Path()
      ..moveTo(size.width * 0.50, size.height * 0.12)
      ..lineTo(size.width * 0.82, size.height * 0.72)
      ..lineTo(size.width * 0.72, size.height * 0.69)
      ..close();
    canvas.drawPath(highlight, Paint()..color = ZentryxColors.markHighlight);
  }

  @override
  bool shouldRepaint(covariant _ZentryxMarkPainter oldDelegate) {
    return oldDelegate.ink != ink || oldDelegate.accent != accent;
  }
}
