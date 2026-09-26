import 'package:flutter/cupertino.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';

Future<void> showTransitRouteSheet({
  required BuildContext context,
  required RouteInfo? route,
  required List<StationInfo> stations,
  required ValueChanged<StationInfo> onStationSelected,
}) {
  return showCupertinoModalPopup<void>(
    context: context,
    builder: (sheetContext) => _RouteSheet(
      route: route,
      stations: stations,
      onStationSelected: (station) {
        Navigator.of(sheetContext).pop();
        onStationSelected(station);
      },
    ),
  );
}

class _RouteSheet extends StatelessWidget {
  const _RouteSheet({
    required this.route,
    required this.stations,
    required this.onStationSelected,
  });

  final RouteInfo? route;
  final List<StationInfo> stations;
  final ValueChanged<StationInfo> onStationSelected;

  @override
  Widget build(BuildContext context) {
    final background = CupertinoDynamicColor.resolve(ZentryxColors.paper, context);
    final line = CupertinoDynamicColor.resolve(ZentryxColors.line, context);
    final height = MediaQuery.sizeOf(context).height * 0.74;

    return Container(
      height: height,
      decoration: BoxDecoration(
        color: background,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          children: [
            const SizedBox(height: 10),
            Container(
              width: 38,
              height: 5,
              decoration: BoxDecoration(
                color: line,
                borderRadius: BorderRadius.circular(99),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 12, 12),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          route == null
                              ? 'Mexibús · Línea 2'
                              : '${route!.networkName} · ${route!.lineLabel}',
                          style: const TextStyle(
                            color: ZentryxColors.ink,
                            fontSize: 23,
                            fontWeight: FontWeight.w700,
                            letterSpacing: -0.5,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _subtitle(),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: ZentryxColors.muted,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                  CupertinoButton(
                    padding: const EdgeInsets.all(8),
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Icon(CupertinoIcons.xmark_circle_fill),
                  ),
                ],
              ),
            ),
            Container(height: 1, color: line),
            Expanded(
              child: stations.isEmpty
                  ? const Center(child: CupertinoActivityIndicator())
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(12, 8, 12, 20),
                      itemCount: stations.length,
                      separatorBuilder: (_, __) => Container(
                        height: 1,
                        margin: const EdgeInsets.only(left: 48),
                        color: line.withValues(alpha: 0.75),
                      ),
                      itemBuilder: (context, index) {
                        final station = stations[index];
                        return CupertinoButton(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 11,
                          ),
                          onPressed: () => onStationSelected(station),
                          child: Row(
                            children: [
                              Container(
                                width: 30,
                                height: 30,
                                alignment: Alignment.center,
                                decoration: BoxDecoration(
                                  color: line.withValues(alpha: 0.65),
                                  shape: BoxShape.circle,
                                ),
                                child: Text(
                                  '${station.order}',
                                  style: const TextStyle(
                                    color: ZentryxColors.ink,
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  station.name,
                                  style: const TextStyle(
                                    color: ZentryxColors.ink,
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                              const Icon(
                                CupertinoIcons.chevron_forward,
                                size: 16,
                                color: ZentryxColors.muted,
                              ),
                            ],
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  String _subtitle() {
    if (route == null) return '${stations.length} estaciones';
    return '${route!.originName} → ${route!.destinationName} · '
        '${stations.length} estaciones';
  }
}
