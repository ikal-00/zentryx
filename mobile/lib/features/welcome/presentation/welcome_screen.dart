import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:zentryx_mobile/design_system/zentryx_layout.dart';
import 'package:zentryx_mobile/design_system/zentryx_mark.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({
    required this.onPassenger,
    this.onDriver,
    super.key,
  });
  final VoidCallback onPassenger;
  final VoidCallback? onDriver;

  @override
  Widget build(BuildContext context) {
    final muted = CupertinoDynamicColor.resolve(ZentryxColors.muted, context);
    return CupertinoPageScaffold(
      child: Stack(
        children: [
          Positioned.fill(
            child: IgnorePointer(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topRight,
                    end: Alignment.bottomLeft,
                    colors: [
                      CupertinoDynamicColor.resolve(
                        ZentryxColors.selection,
                        context,
                      ),
                      CupertinoDynamicColor.resolve(
                        ZentryxColors.paper,
                        context,
                      ),
                    ],
                    stops: const [0, 0.6],
                  ),
                ),
              ),
            ),
          ),
          Positioned(
            top: -100,
            right: -150,
            child: IgnorePointer(
              child: Container(
                width: 390,
                height: 390,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: ZentryxColors.brand.withValues(alpha: 0.07),
                    width: 54,
                  ),
                ),
              ),
            ),
          ),
          SafeArea(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  maxWidth: ZentryxLayout.maxContentWidth,
                ),
                child: SingleChildScrollView(
                  padding: ZentryxLayout.pagePadding,
                  child: TweenAnimationBuilder<double>(
                    tween: Tween(begin: 0, end: 1),
                    duration: MediaQuery.disableAnimationsOf(context)
                        ? Duration.zero
                        : ZentryxLayout.motion,
                    builder: (context, value, child) => Opacity(
                      opacity: value,
                      child: Transform.translate(
                        offset: Offset(0, 8 * (1 - value)),
                        child: child,
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const ZentryxMark(size: 40),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'ZENTRYX',
                                    style: TextStyle(
                                      fontSize: 21,
                                      fontWeight: FontWeight.w800,
                                      letterSpacing: 3,
                                    ),
                                  ),
                                  Text(
                                    'Movilidad en tiempo real',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: muted,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 32),
                        const Text(
                          'Tu ciudad.\nA tu ritmo.',
                          style: TextStyle(
                            fontSize: 38,
                            height: 1.05,
                            letterSpacing: -1.6,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'Muévete con más claridad.',
                          style: TextStyle(fontSize: 16, color: muted),
                        ),
                        const SizedBox(height: 24),
                        const _LineHero(),
                        const SizedBox(height: 28),
                        Text(
                          'MOVILIDAD EN TIEMPO REAL',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.5,
                            color: muted,
                          ),
                        ),
                        const SizedBox(height: 12),
                        _ModeCard(
                          title: 'Ver mapa y unidades',
                          subtitle: 'Consulta estaciones, tiempos de llegada y seguimiento en vivo',
                          icon: CupertinoIcons.map_fill,
                          primary: true,
                          onPressed: onPassenger,
                        ),
                        if (onDriver != null) ...[
                          const SizedBox(height: 12),
                          _ModeCard(
                            title: 'Modo conductor',
                            subtitle: 'Verificación de operador e INE, seguimiento de unidad y botón de emergencia',
                            icon: CupertinoIcons.shield_lefthalf_fill,
                            primary: false,
                            onPressed: onDriver!,
                          ),
                        ],
                        const SizedBox(height: 24),
                        Center(
                          child: Text(
                            'Menos incertidumbre. Más camino.',
                            textAlign: TextAlign.center,
                            style: TextStyle(fontSize: 12, color: muted),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ModeCard extends StatelessWidget {
  const _ModeCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onPressed,
    this.primary = false,
  });
  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback onPressed;
  final bool primary;

  @override
  Widget build(BuildContext context) {
    final foreground = primary
        ? ZentryxColors.white
        : CupertinoDynamicColor.resolve(ZentryxColors.ink, context);
    return Semantics(
      button: true,
      onTap: onPressed,
      label: '$title. $subtitle',
      child: ExcludeSemantics(
        child: CupertinoButton(
          padding: EdgeInsets.zero,
          onPressed: () {
            HapticFeedback.selectionClick();
            onPressed();
          },
          child: Container(
            padding: ZentryxLayout.cardPadding,
            decoration: BoxDecoration(
              color: primary
                  ? ZentryxColors.brandStrong
                  : CupertinoDynamicColor.resolve(
                      ZentryxColors.surface,
                      context,
                    ),
              borderRadius: ZentryxLayout.cardRadius,
              border: primary
                  ? null
                  : Border.all(
                      color: CupertinoDynamicColor.resolve(
                        ZentryxColors.line,
                        context,
                      ),
                    ),
              boxShadow: ZentryxLayout.shadow,
            ),
            child: Row(
              children: [
                Icon(icon, size: 27, color: foreground),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: TextStyle(
                          fontSize: 19,
                          fontWeight: FontWeight.w700,
                          color: foreground,
                        ),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        subtitle,
                        style: TextStyle(
                          fontSize: 12,
                          height: 1.4,
                          color: primary
                              ? foreground
                              : CupertinoDynamicColor.resolve(
                                  ZentryxColors.muted,
                                  context,
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                Icon(
                  CupertinoIcons.arrow_up_right,
                  size: 19,
                  color: foreground,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _LineHero extends StatelessWidget {
  const _LineHero();
  @override
  Widget build(BuildContext context) => ZentryxCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
              decoration: const BoxDecoration(
                color: ZentryxColors.brandSoft,
                borderRadius: BorderRadius.all(Radius.circular(10)),
              ),
              child: const Text(
                'L2',
                style: TextStyle(
                  color: ZentryxColors.brandDark,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            const SizedBox(width: 10),
            const Expanded(
              child: Text(
                'Mexibús Línea 2',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        const ExcludeSemantics(
          child: SizedBox(
            height: 78,
            width: double.infinity,
            child: CustomPaint(painter: _RoutePreviewPainter()),
          ),
        ),
        Text(
          'Información de transporte en tiempo real',
          style: TextStyle(
            fontSize: 12,
            height: 1.4,
            color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context),
          ),
        ),
      ],
    ),
  );
}

/// Decorative route, not a geographical map or a live vehicle.
class _RoutePreviewPainter extends CustomPainter {
  const _RoutePreviewPainter();
  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..moveTo(4, 56)
      ..lineTo(size.width * .3, 56)
      ..cubicTo(size.width * .46, 56, size.width * .42, 24, size.width * .6, 24)
      ..lineTo(size.width - 4, 24);
    canvas.drawPath(
      path,
      Paint()
        ..color = ZentryxColors.brandSoft
        ..style = PaintingStyle.stroke
        ..strokeWidth = 18
        ..strokeCap = StrokeCap.round,
    );
    canvas.drawPath(
      path,
      Paint()
        ..color = ZentryxColors.route
        ..style = PaintingStyle.stroke
        ..strokeWidth = 4
        ..strokeCap = StrokeCap.round,
    );
    for (final point in [
      Offset(10, 56),
      Offset(size.width * .29, 56),
      Offset(size.width - 10, 24),
    ]) {
      canvas.drawCircle(point, 6, Paint()..color = ZentryxColors.brandStrong);
      canvas.drawCircle(point, 3, Paint()..color = ZentryxColors.white);
    }
    final bus = RRect.fromRectAndRadius(
      Rect.fromCenter(
        center: Offset(size.width * .67, 24),
        width: 48,
        height: 26,
      ),
      const Radius.circular(8),
    );
    canvas.drawShadow(
      Path()..addRRect(bus),
      ZentryxColors.markerShadow,
      4,
      true,
    );
    canvas.drawRRect(bus, Paint()..color = ZentryxColors.busBody);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        bus.outerRect.deflate(3),
        const Radius.circular(5),
      ),
      Paint()..color = ZentryxColors.busRoof,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(bus.right - 12, bus.top + 4, 7, 18),
        const Radius.circular(3),
      ),
      Paint()..color = ZentryxColors.busGlass,
    );
    canvas.drawLine(
      Offset(bus.left + 9, bus.top + 7),
      Offset(bus.left + 24, bus.top + 7),
      Paint()
        ..color = ZentryxColors.busRoofHighlight
        ..strokeWidth = 3
        ..strokeCap = StrokeCap.round,
    );
  }

  @override
  bool shouldRepaint(covariant _RoutePreviewPainter oldDelegate) => false;
}
