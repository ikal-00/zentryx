import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:zentryx_mobile/design_system/zentryx_layout.dart';
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

class _RouteSheet extends StatefulWidget {
  const _RouteSheet({
    required this.route,
    required this.stations,
    required this.onStationSelected,
  });

  final RouteInfo? route;
  final List<StationInfo> stations;
  final ValueChanged<StationInfo> onStationSelected;

  @override
  State<_RouteSheet> createState() => _RouteSheetState();
}

class _RouteSheetState extends State<_RouteSheet> {
  String _searchQuery = '';

  List<StationInfo> get _filteredStations {
    if (_searchQuery.trim().isEmpty) return widget.stations;
    final query = _searchQuery.trim().toLowerCase();
    return widget.stations.where((s) {
      return s.name.toLowerCase().contains(query) ||
          s.order.toString().contains(query);
    }).toList(growable: false);
  }

  @override
  Widget build(BuildContext context) {
    final background = CupertinoDynamicColor.resolve(ZentryxColors.paper, context);
    final surface = CupertinoDynamicColor.resolve(ZentryxColors.surface, context);
    final line = CupertinoDynamicColor.resolve(ZentryxColors.line, context);
    final ink = CupertinoDynamicColor.resolve(ZentryxColors.ink, context);
    final muted = CupertinoDynamicColor.resolve(ZentryxColors.muted, context);
    final height = MediaQuery.sizeOf(context).height * 0.78;
    final filtered = _filteredStations;

    return Container(
      height: height,
      decoration: BoxDecoration(
        color: background,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
        boxShadow: ZentryxLayout.shadowLg,
      ),
      child: SafeArea(
        top: false,
        child: Column(
          children: [
            const SizedBox(height: 10),
            // Sheet drag handle
            Container(
              width: 40,
              height: 5,
              decoration: BoxDecoration(
                color: line,
                borderRadius: BorderRadius.circular(99),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 14, 12, 10),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: ZentryxColors.brandStrong,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                widget.route?.lineLabel ?? 'L2',
                                style: const TextStyle(
                                  color: ZentryxColors.white,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                widget.route == null
                                    ? 'Mexibús · Línea 2'
                                    : widget.route!.networkName,
                                style: TextStyle(
                                  color: ink,
                                  fontSize: 21,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: -0.5,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 5),
                        Text(
                          _subtitle(),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: muted,
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                  CupertinoButton(
                    padding: const EdgeInsets.all(8),
                    onPressed: () => Navigator.of(context).pop(),
                    child: const Icon(CupertinoIcons.xmark_circle_fill, size: 28),
                  ),
                ],
              ),
            ),
            // Search Input
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              child: CupertinoSearchTextField(
                placeholder: 'Buscar estación o parada...',
                style: TextStyle(color: ink, fontSize: 14),
                placeholderStyle: TextStyle(color: muted, fontSize: 14),
                backgroundColor: surface,
                borderRadius: BorderRadius.circular(12),
                onChanged: (value) => setState(() => _searchQuery = value),
              ),
            ),
            const SizedBox(height: 6),
            Container(height: 1, color: line.withValues(alpha: 0.6)),
            // Station List with Timeline
            Expanded(
              child: widget.stations.isEmpty
                  ? const Center(child: CupertinoActivityIndicator())
                  : filtered.isEmpty
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.all(24),
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(CupertinoIcons.search, size: 36, color: muted),
                                const SizedBox(height: 12),
                                Text(
                                  'No se encontraron estaciones para "$_searchQuery"',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(color: muted, fontSize: 14),
                                ),
                              ],
                            ),
                          ),
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 10, 16, 24),
                          itemCount: filtered.length,
                          itemBuilder: (context, index) {
                            final station = filtered[index];
                            final isFirst = index == 0 && _searchQuery.isEmpty;
                            final isLast = index == filtered.length - 1 && _searchQuery.isEmpty;

                            return CupertinoButton(
                              padding: EdgeInsets.zero,
                              onPressed: () {
                                HapticFeedback.selectionClick();
                                widget.onStationSelected(station);
                              },
                              child: Container(
                                padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
                                child: Row(
                                  children: [
                                    // Visual Timeline Node
                                    _TimelineNode(
                                      order: station.order,
                                      isFirst: isFirst,
                                      isLast: isLast,
                                    ),
                                    const SizedBox(width: 14),
                                    // Station Information
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            station.name,
                                            style: TextStyle(
                                              color: ink,
                                              fontSize: 16,
                                              fontWeight: FontWeight.w600,
                                              letterSpacing: -0.2,
                                            ),
                                          ),
                                          if (isFirst || isLast) ...[
                                            const SizedBox(height: 2),
                                            Text(
                                              isFirst ? 'Terminal de salida' : 'Terminal de destino',
                                              style: TextStyle(
                                                color: ZentryxColors.brandStrong,
                                                fontSize: 11,
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                          ],
                                        ],
                                      ),
                                    ),
                                    Icon(
                                      CupertinoIcons.chevron_forward,
                                      size: 16,
                                      color: muted,
                                    ),
                                  ],
                                ),
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
    if (widget.route == null) return '${widget.stations.length} estaciones';
    return '${widget.route!.originName} → ${widget.route!.destinationName} · ${widget.stations.length} estaciones';
  }
}

class _TimelineNode extends StatelessWidget {
  const _TimelineNode({
    required this.order,
    required this.isFirst,
    required this.isLast,
  });

  final int order;
  final bool isFirst;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 32,
      height: 32,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: isFirst || isLast
            ? ZentryxColors.brandStrong
            : CupertinoDynamicColor.resolve(ZentryxColors.selection, context),
        shape: BoxShape.circle,
        border: Border.all(
          color: isFirst || isLast
              ? ZentryxColors.white
              : CupertinoDynamicColor.resolve(ZentryxColors.line, context),
          width: 1.5,
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0x12000000),
            blurRadius: 4,
            offset: Offset(0, 1),
          ),
        ],
      ),
      child: Text(
        '$order',
        style: TextStyle(
          color: isFirst || isLast
              ? ZentryxColors.white
              : CupertinoDynamicColor.resolve(ZentryxColors.onSelection, context),
          fontSize: 12,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
