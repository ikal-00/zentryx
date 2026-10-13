import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';

import 'zentryx_theme.dart';

abstract final class ZentryxLayout {
  static const pagePadding = EdgeInsets.symmetric(horizontal: 20, vertical: 24);
  static const cardPadding = EdgeInsets.all(20);
  static const cardRadius = BorderRadius.all(Radius.circular(22));
  static const controlRadius = BorderRadius.all(Radius.circular(16));
  static const pillRadius = BorderRadius.all(Radius.circular(99));
  static const motion = Duration(milliseconds: 220);
  static const motionSpring = Duration(milliseconds: 320);
  static const maxContentWidth = 540.0;

  // Ultra-refined Uber-grade layered drop shadows
  static const shadow = [
    BoxShadow(
      color: Color(0x0D000000),
      blurRadius: 10,
      offset: Offset(0, 3),
    ),
    BoxShadow(
      color: Color(0x12000000),
      blurRadius: 28,
      spreadRadius: -4,
      offset: Offset(0, 12),
    ),
  ];

  static const shadowSm = [
    BoxShadow(
      color: Color(0x0A000000),
      blurRadius: 6,
      offset: Offset(0, 2),
    ),
    BoxShadow(
      color: Color(0x0D000000),
      blurRadius: 14,
      offset: Offset(0, 6),
    ),
  ];

  static const shadowLg = [
    BoxShadow(
      color: Color(0x14000000),
      blurRadius: 20,
      offset: Offset(0, 8),
    ),
    BoxShadow(
      color: Color(0x1F000000),
      blurRadius: 44,
      spreadRadius: -6,
      offset: Offset(0, 20),
    ),
  ];
}

/// Tier-1 Minimalist Card with subtle border and layered elevation.
class ZentryxCard extends StatelessWidget {
  const ZentryxCard({
    required this.child,
    this.color,
    this.padding = ZentryxLayout.cardPadding,
    this.radius = ZentryxLayout.cardRadius,
    this.border,
    super.key,
  });

  final Widget child;
  final Color? color;
  final EdgeInsets padding;
  final BorderRadius radius;
  final BoxBorder? border;

  @override
  Widget build(BuildContext context) {
    final surfaceColor = CupertinoDynamicColor.resolve(
      color ?? ZentryxColors.surface,
      context,
    );
    final borderColor = CupertinoDynamicColor.resolve(
      ZentryxColors.line,
      context,
    );

    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: surfaceColor,
        borderRadius: radius,
        border: border ?? Border.all(color: borderColor, width: 0.8),
        boxShadow: ZentryxLayout.shadow,
      ),
      child: child,
    );
  }
}

/// Tier-1 Primary Action Button with Uber-style micro-interactions.
class ZentryxPrimaryButton extends StatefulWidget {
  const ZentryxPrimaryButton({
    required this.label,
    required this.icon,
    required this.onPressed,
    this.color,
    this.textColor,
    this.loading = false,
    super.key,
  });

  final String label;
  final IconData icon;
  final VoidCallback? onPressed;
  final Color? color;
  final Color? textColor;
  final bool loading;

  @override
  State<ZentryxPrimaryButton> createState() => _ZentryxPrimaryButtonState();
}

class _ZentryxPrimaryButtonState extends State<ZentryxPrimaryButton> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final bgColor = widget.color ?? ZentryxColors.brandStrong;
    final fgColor = widget.textColor ?? ZentryxColors.white;

    return GestureDetector(
      onTapDown: widget.onPressed == null
          ? null
          : (_) {
              setState(() => _pressed = true);
              HapticFeedback.lightImpact();
            },
      onTapUp: widget.onPressed == null
          ? null
          : (_) => setState(() => _pressed = false),
      onTapCancel: () => setState(() => _pressed = false),
      onTap: widget.loading ? null : widget.onPressed,
      child: AnimatedScale(
        scale: _pressed ? 0.98 : 1.0,
        duration: const Duration(milliseconds: 120),
        curve: Curves.easeInOut,
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 18),
          decoration: BoxDecoration(
            color: widget.onPressed == null
                ? bgColor.withValues(alpha: 0.45)
                : bgColor,
            borderRadius: ZentryxLayout.controlRadius,
            boxShadow: widget.onPressed == null ? null : ZentryxLayout.shadowSm,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (widget.loading) ...[
                const CupertinoActivityIndicator(color: ZentryxColors.white),
                const SizedBox(width: 12),
              ] else ...[
                Icon(widget.icon, color: fgColor, size: 20),
                const SizedBox(width: 10),
              ],
              Flexible(
                child: Text(
                  widget.label,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: fgColor,
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.3,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
