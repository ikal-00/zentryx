import 'package:flutter/cupertino.dart';

import 'zentryx_theme.dart';

abstract final class ZentryxLayout {
  static const pagePadding = EdgeInsets.all(24);
  static const cardPadding = EdgeInsets.all(20);
  static const cardRadius = BorderRadius.all(Radius.circular(26));
  static const controlRadius = BorderRadius.all(Radius.circular(18));
  static const motion = Duration(milliseconds: 240);
  static const maxContentWidth = 520.0;
  static const shadow = [
    BoxShadow(
      color: ZentryxColors.surfaceShadow,
      blurRadius: 24,
      offset: Offset(0, 8),
    ),
  ];
}

/// Opaque, inexpensive surface for screens outside the map.
class ZentryxCard extends StatelessWidget {
  const ZentryxCard({required this.child, this.color, super.key});
  final Widget child;
  final Color? color;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: ZentryxLayout.cardPadding,
    decoration: BoxDecoration(
      color: CupertinoDynamicColor.resolve(
        color ?? ZentryxColors.surface,
        context,
      ),
      borderRadius: ZentryxLayout.cardRadius,
      border: Border.all(
        color: CupertinoDynamicColor.resolve(ZentryxColors.line, context),
      ),
      boxShadow: ZentryxLayout.shadow,
    ),
    child: child,
  );
}

class ZentryxPrimaryButton extends StatelessWidget {
  const ZentryxPrimaryButton({
    required this.label,
    required this.icon,
    required this.onPressed,
    super.key,
  });
  final String label;
  final IconData icon;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => SizedBox(
    width: double.infinity,
    child: CupertinoButton(
      color: ZentryxColors.brandStrong,
      borderRadius: ZentryxLayout.controlRadius,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
      onPressed: onPressed,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: ZentryxColors.white, size: 21),
          const SizedBox(width: 10),
          Flexible(
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: ZentryxColors.white,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    ),
  );
}
