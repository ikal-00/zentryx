import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';

class StationMarker extends StatelessWidget {
  const StationMarker({
    required this.name,
    required this.isNext,
    required this.selected,
    required this.onTap,
    super.key,
  });

  final String name;
  final bool isNext;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final prominent = selected || isNext;

    return Semantics(
      button: true,
      selected: selected,
      label: '$name${isNext ? ', próxima estación' : ''}',
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () {
          HapticFeedback.selectionClick();
          onTap();
        },
        child: Center(
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            curve: Curves.easeOutCubic,
            width: prominent ? 32 : 18,
            height: prominent ? 32 : 18,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: selected
                  ? ZentryxColors.stationSelected
                  : (isNext ? ZentryxColors.brandSoft : ZentryxColors.white),
              border: Border.all(
                color: ZentryxColors.stationBorder,
                width: prominent ? 3.0 : 2.5,
              ),
              boxShadow: [
                BoxShadow(
                  color: prominent
                      ? ZentryxColors.stationHalo
                      : ZentryxColors.stationNormalHalo,
                  spreadRadius: prominent ? 5 : 2,
                  blurRadius: prominent ? 6 : 2,
                ),
                const BoxShadow(
                  color: ZentryxColors.markerShadow,
                  blurRadius: 6,
                  offset: Offset(0, 2),
                ),
              ],
            ),
            child: prominent
                ? Center(
                    child: Icon(
                      selected
                          ? CupertinoIcons.checkmark
                          : CupertinoIcons.arrow_down,
                      size: 15,
                      color: selected
                          ? ZentryxColors.white
                          : ZentryxColors.stationBorder,
                    ),
                  )
                : null,
          ),
        ),
      ),
    );
  }
}
