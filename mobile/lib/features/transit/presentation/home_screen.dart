import 'package:flutter/cupertino.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';
import 'package:zentryx_mobile/features/transit/presentation/widgets/route_sheet.dart';
import 'package:zentryx_mobile/features/transit/presentation/widgets/transit_hud.dart';
import 'package:zentryx_mobile/features/transit/presentation/widgets/vehicle_marker.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  static const _fallbackCenter = LatLng(19.62211, -99.16299);

  final MapController _mapController = MapController();
  bool _followVehicle = true;
  double _zoom = 15.2;
  GeoPoint? _lastCentered;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(transitControllerProvider);

    ref.listen<TransitState>(transitControllerProvider, (previous, next) {
      final position = next.vehicle?.position;
      if (!_followVehicle || position == null) return;
      if (_samePoint(position, _lastCentered)) return;
      _lastCentered = position;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        _mapController.move(LatLng(position.lat, position.lon), _zoom);
      });
    });

    final routePoints = state.route?.path
            .map((point) => LatLng(point.lat, point.lon))
            .toList(growable: false) ??
        const <LatLng>[];
    final vehicle = state.vehicle;
    final vehiclePosition = vehicle?.position;

    return CupertinoPageScaffold(
      child: Stack(
        fit: StackFit.expand,
        children: [
          Positioned.fill(
            child: FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: _initialCenter(state),
                initialZoom: _zoom,
                minZoom: 11,
                maxZoom: 19,
                interactionOptions: const InteractionOptions(
                  flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
                ),
                onPositionChanged: (camera, hasGesture) {
                  _zoom = camera.zoom;
                  if (hasGesture && _followVehicle) {
                    setState(() => _followVehicle = false);
                  }
                },
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'com.zentryx.mobile',
                  maxNativeZoom: 19,
                ),
                if (routePoints.length > 1)
                  PolylineLayer(
                    polylines: [
                      Polyline(
                        points: routePoints,
                        strokeWidth: 9,
                        color: CupertinoDynamicColor.resolve(
                          ZentryxColors.ink,
                          context,
                        ).withValues(alpha: 0.10),
                      ),
                      Polyline(
                        points: routePoints,
                        strokeWidth: 4.5,
                        color: CupertinoDynamicColor.resolve(
                          ZentryxColors.ink,
                          context,
                        ).withValues(alpha: 0.90),
                      ),
                    ],
                  ),
                MarkerLayer(
                  markers: state.stations
                      .map(
                        (station) => Marker(
                          point: LatLng(
                            station.position.lat,
                            station.position.lon,
                          ),
                          width: 38,
                          height: 38,
                          child: Semantics(
                            button: true,
                            label: station.name,
                            child: GestureDetector(
                              behavior: HitTestBehavior.opaque,
                              onTap: () => _showStation(station),
                              child: Center(
                                child: Container(
                                  width: 14,
                                  height: 14,
                                  decoration: BoxDecoration(
                                    color: CupertinoDynamicColor.resolve(
                                      ZentryxColors.surface,
                                      context,
                                    ),
                                    shape: BoxShape.circle,
                                    border: Border.all(
                                      color: CupertinoDynamicColor.resolve(
                                        ZentryxColors.ink,
                                        context,
                                      ),
                                      width: 3,
                                    ),
                                    boxShadow: const [
                                      BoxShadow(
                                        color: Color(0x22000000),
                                        blurRadius: 8,
                                        offset: Offset(0, 2),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      )
                      .toList(growable: false),
                ),
                if (vehiclePosition != null)
                  AnimatedVehicleLayer(
                    target: LatLng(vehiclePosition.lat, vehiclePosition.lon),
                    headingDeg: vehicle?.headingDeg ?? 0,
                    online: vehicle?.isOnline == true,
                  ),
                RichAttributionWidget(
                  attributions: const [
                    TextSourceAttribution('OpenStreetMap contributors'),
                  ],
                ),
              ],
            ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 10, 16, 0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Semantics(
                      button: true,
                      label: 'Ver ruta y estaciones',
                      child: GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: _showRoute,
                        child: TransitHeaderCard(state: state),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  MapFollowButton(
                    following: _followVehicle,
                    onPressed: _recenter,
                  ),
                ],
              ),
            ),
          ),
          Positioned(
            left: 14,
            right: 14,
            bottom: 14 + MediaQuery.paddingOf(context).bottom,
            child: TransitStatusCard(
              state: state,
              onRefresh: () =>
                  ref.read(transitControllerProvider.notifier).refresh(),
            ),
          ),
        ],
      ),
    );
  }

  LatLng _initialCenter(TransitState state) {
    final vehicle = state.vehicle?.position;
    if (vehicle != null) return LatLng(vehicle.lat, vehicle.lon);
    if (state.stations.isNotEmpty) {
      final station = state.stations.first;
      return LatLng(station.position.lat, station.position.lon);
    }
    return _fallbackCenter;
  }

  bool _samePoint(GeoPoint a, GeoPoint? b) {
    if (b == null) return false;
    return (a.lat - b.lat).abs() < 0.000001 &&
        (a.lon - b.lon).abs() < 0.000001;
  }

  void _recenter() {
    final position = ref.read(transitControllerProvider).vehicle?.position;
    if (position == null) {
      _mapController.move(_fallbackCenter, _zoom.clamp(14.0, 18.0).toDouble());
      return;
    }
    setState(() => _followVehicle = true);
    _lastCentered = position;
    _mapController.move(
      LatLng(position.lat, position.lon),
      _zoom.clamp(14.0, 18.0).toDouble(),
    );
  }

  void _showRoute() {
    final state = ref.read(transitControllerProvider);
    showTransitRouteSheet(
      context: context,
      route: state.route,
      stations: state.stations,
      onStationSelected: _focusStation,
    );
  }

  void _focusStation(StationInfo station) {
    if (!mounted) return;
    setState(() => _followVehicle = false);
    _mapController.move(
      LatLng(station.position.lat, station.position.lon),
      17,
    );
  }

  void _showStation(StationInfo station) {
    final vehicle = ref.read(transitControllerProvider).vehicle;
    final isNext = vehicle?.nextStationName == station.name;

    showCupertinoModalPopup<void>(
      context: context,
      builder: (sheetContext) => CupertinoActionSheet(
        title: Text(station.name),
        message: Text(
          isNext
              ? 'Próxima estación · ${_eta(vehicle?.etaSeconds)}'
              : 'Estación ${station.order} · Mexibús Línea 2',
        ),
        actions: [
          CupertinoActionSheetAction(
            onPressed: () {
              Navigator.of(sheetContext).pop();
              _focusStation(station);
            },
            child: const Text('Centrar en estación'),
          ),
        ],
        cancelButton: CupertinoActionSheetAction(
          onPressed: () => Navigator.of(sheetContext).pop(),
          child: const Text('Cerrar'),
        ),
      ),
    );
  }

  String _eta(double? seconds) {
    if (seconds == null || !seconds.isFinite || seconds < 0) {
      return 'ETA no disponible';
    }
    if (seconds < 60) return 'llega en menos de 1 min';
    return 'llega en ${(seconds / 60).ceil()} min';
  }
}
