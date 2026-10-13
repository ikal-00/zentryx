import 'dart:ui';

import 'package:flutter/cupertino.dart';
import 'package:zentryx_mobile/design_system/zentryx_layout.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';

class GlassSurface extends StatelessWidget {
  const GlassSurface({
    required this.child,
    required this.borderRadius,
    required this.padding,
    super.key,
    this.blur = 18,
  });

  final Widget child;
  final double borderRadius;
  final EdgeInsets padding;
  final double blur;

  @override
  Widget build(BuildContext context) {
    final surface = CupertinoDynamicColor.resolve(ZentryxColors.surface, context);
    final line = CupertinoDynamicColor.resolve(ZentryxColors.line, context);

    return RepaintBoundary(
      child: DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(borderRadius),
          boxShadow: ZentryxLayout.shadowSm,
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(borderRadius),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: blur, sigmaY: blur),
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: surface.withValues(alpha: 0.90),
                borderRadius: BorderRadius.circular(borderRadius),
                border: Border.all(
                  color: line.withValues(alpha: 0.65),
                  width: 0.75,
                ),
              ),
              child: Padding(padding: padding, child: child),
            ),
          ),
        ),
      ),
    );
  }
}
