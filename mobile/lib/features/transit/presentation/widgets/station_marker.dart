import 'package:flutter/cupertino.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';

class StationMarker extends StatelessWidget {
  const StationMarker({required this.name, required this.isNext,
    required this.selected, required this.onTap, super.key});
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
        onTap: onTap,
        child: Center(
          child: Container(
            width: prominent ? 30 : 19,
            height: prominent ? 30 : 19,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: selected ? ZentryxColors.stationSelected : ZentryxColors.white,
              border: Border.all(color: ZentryxColors.stationBorder, width: 3),
              boxShadow: [
                BoxShadow(
                  color: prominent ? ZentryxColors.stationHalo : ZentryxColors.stationNormalHalo,
                  spreadRadius: prominent ? 5 : 2,
                  blurRadius: prominent ? 2 : 0,
                ),
                const BoxShadow(color: ZentryxColors.markerShadow, blurRadius: 4, offset: Offset(0, 2)),
              ],
            ),
            child: prominent
                ? Icon(selected ? CupertinoIcons.checkmark : CupertinoIcons.arrow_down,
                    size: 16, color: selected ? ZentryxColors.white : ZentryxColors.stationBorder)
                : null,
          ),
        ),
      ),
    );
  }
}
