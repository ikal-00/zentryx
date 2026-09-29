import 'package:flutter/cupertino.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';
import 'motion/follow_camera.dart';
import 'motion/vehicle_motion.dart';
import 'widgets/route_sheet.dart';
import 'widgets/station_marker.dart';
import 'widgets/transit_hud.dart';
import 'widgets/vehicle_marker.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({this.tileProvider, super.key});
  final TileProvider? tileProvider;
  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen>
    with SingleTickerProviderStateMixin {
  static const _fallbackCenter = LatLng(19.62211, -99.16299);
  final MapController _mapController = MapController();
  final FollowCamera _follow = FollowCamera();
  final FollowCamera _focusMotion = FollowCamera();
  late final Ticker _cameraTicker;
  bool _mapReady = false;
  LatLng? _visualPosition;
  LatLng? _cameraTarget;
  Duration _lastFrame = Duration.zero;
  StationInfo? _selectedStation;
  RouteInfo? _cachedRoute;
  List<LatLng> _routePoints = const [];

  @override
  void initState() {
    super.initState();
    _cameraTicker = createTicker(_stepCamera);
  }

  void _stepCamera(Duration elapsed) {
    final dt = (elapsed - _lastFrame).inMicroseconds / 1000000;
    _lastFrame = elapsed;
    final target = _cameraTarget;
    if (!_mapReady || target == null) {
      _cameraTicker.stop();
      return;
    }
    final camera = _mapController.camera;
    final position = _focusMotion.step(camera.center, target, camera.zoom, dt);
    if (position == null) {
      _cameraTicker.stop();
    } else {
      _mapController.move(position, camera.zoom);
    }
  }

  void _animateCameraTo(LatLng target) {
    _cameraTarget = target;
    if (_mapReady && !_cameraTicker.isActive) {
      _lastFrame = Duration.zero;
      _cameraTicker.start();
    }
  }

  void _onVisualPosition(LatLng position) {
    _visualPosition = position;
    if (_follow.following) _animateCameraTo(position);
  }

  void _explore() {
    _cameraTicker.stop();
    _cameraTarget = null;
    if (_follow.following) setState(_follow.explore);
  }

  @override
  void dispose() {
    _cameraTicker.dispose();
    _mapController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(transitControllerProvider);
    if (!identical(_cachedRoute, state.route)) {
      _cachedRoute = state.route;
      _routePoints = state.route?.path
              .map((point) => LatLng(point.lat, point.lon))
              .where(validPosition)
              .toList(growable: false) ?? const [];
    }
    final vehicle = state.vehicle;
    final position = vehicle?.position;
    final target = position == null ? null : LatLng(position.lat, position.lon);
    final selected = _selectedStation;
    return CupertinoPageScaffold(
      child: Stack(
        fit: StackFit.expand,
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: target != null && validPosition(target) ? target : _fallbackCenter,
              initialZoom: 15.2,
              minZoom: 11,
              maxZoom: 19,
              onMapReady: () {
                _mapReady = true;
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  if (mounted && _cameraTarget != null) _animateCameraTo(_cameraTarget!);
                });
              },
              interactionOptions: const InteractionOptions(
                flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
              ),
              onPositionChanged: (camera, hasGesture) {
                if (hasGesture) _explore();
              },
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                tileProvider: widget.tileProvider,
                userAgentPackageName: 'com.zentryx.mobile',
                maxNativeZoom: 19,
              ),
              if (_routePoints.length > 1)
                PolylineLayer(polylines: [
                  // OSM tiles remain light even when the surrounding UI is dark.
                  Polyline(points: _routePoints, strokeWidth: 12,
                      color: const Color(0xF2FFFFFF)),
                  Polyline(points: _routePoints, strokeWidth: 8,
                      color: const Color(0xFF153C34)),
                  Polyline(points: _routePoints, strokeWidth: 3,
                      color: const Color(0xFFD6F67A)),
                ]),
              MarkerLayer(markers: [
                for (final station in state.stations)
                  Marker(
                    point: LatLng(station.position.lat, station.position.lon),
                    width: 48,
                    height: 48,
                    child: StationMarker(
                      name: station.name,
                      isNext: vehicle?.isNextStation(station) == true,
                      selected: station.stationId == selected?.stationId,
                      onTap: () => _showStation(station),
                    ),
                  ),
              ]),
              if (target != null && validPosition(target))
                AnimatedVehicleLayer(
                  key: ValueKey(vehicle!.vehicleId),
                  target: target,
                  headingDeg: vehicle.headingDeg,
                  timestamp: vehicle.lastUpdate,
                  accuracyM: vehicle.accuracyM,
                  online: vehicle.isOnline && !state.stale,
                  onVisualPosition: _onVisualPosition,
                ),
            ],
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(14, 10, 14, 0),
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
                  MapFollowButton(following: _follow.following, onPressed: _recenter),
                ],
              ),
            ),
          ),
          Positioned(
            left: 14,
            right: 14,
            bottom: 8 + MediaQuery.paddingOf(context).bottom,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ConstrainedBox(
                  constraints: BoxConstraints(maxHeight: MediaQuery.sizeOf(context).height * 0.42),
                  child: SingleChildScrollView(
                    child: selected == null
                        ? TransitStatusCard(
                            state: state,
                            onRefresh: () => ref.read(transitControllerProvider.notifier).refresh(),
                          )
                        : StationStatusCard(
                            station: selected,
                            state: state,
                            onCenter: () => _animateCameraTo(LatLng(selected.position.lat, selected.position.lon)),
                            onClose: () => setState(() => _selectedStation = null),
                          ),
                  ),
                ),
                const SizedBox(height: 4),
                const Text('© OpenStreetMap contributors',
                    style: TextStyle(fontSize: 10, color: Color(0xFF153C34),
                        backgroundColor: Color(0xEFFFFFFF))),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _recenter() {
    setState(() {
      _follow.resume();
      _selectedStation = null;
    });
    final target = _visualPosition;
    if (target != null) _animateCameraTo(target);
  }

  void _showRoute() {
    final state = ref.read(transitControllerProvider);
    showTransitRouteSheet(
      context: context,
      route: state.route,
      stations: state.stations,
      onStationSelected: (station) {
        _showStation(station);
        _animateCameraTo(LatLng(station.position.lat, station.position.lon));
      },
    );
  }

  void _showStation(StationInfo station) {
    if (!mounted) return;
    _cameraTicker.stop();
    _cameraTarget = null;
    setState(() {
      _follow.explore();
      _selectedStation = station;
    });
  }
}
