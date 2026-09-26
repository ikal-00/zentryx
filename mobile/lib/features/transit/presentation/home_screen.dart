import 'dart:math' as math;
import 'dart:ui';

import 'package:flutter/cupertino.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import 'package:zentryx_mobile/design_system/zentryx_mark.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';

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
    final vehiclePosition = state.vehicle?.position;

    return CupertinoPageScaffold(
      child: Stack(
        children: [
          Positioned.fill(
            child: FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: _initialCenter(state),
                initialZoom: _zoom,
                minZoom: 11,
                maxZoom: 19,
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
                        strokeWidth: 5,
                        color: CupertinoDynamicColor.resolve(
                          ZentryxColors.ink,
                          context,
                        ).withOpacity(0.88),
                      ),
                    ],
                  ),
                MarkerLayer(
                  markers: state.stations
                      .map(
                        (station) => Marker(
                          point: LatLng(station.position.lat, station.position.lon),
                          width: 34,
                          height: 34,
                          child: GestureDetector(
                            behavior: HitTestBehavior.opaque,
                            onTap: () => _showStation(station),
                            child: Center(
                              child: Container(
                                width: 13,
                                height: 13,
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
                      )
                      .toList(growable: false),
                ),
                if (vehiclePosition != null)
                  _AnimatedVehicleLayer(
                    target: LatLng(vehiclePosition.lat, vehiclePosition.lon),
                    headingDeg: state.vehicle?.headingDeg ?? 0,
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
                  Expanded(child: _HeaderCard(state: state)),
                  const SizedBox(width: 10),
                  _RoundButton(
                    icon: _followVehicle
                        ? CupertinoIcons.location_fill
                        : CupertinoIcons.location,
                    label: _followVehicle ? 'Siguiendo' : 'Centrar',
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
            child: _StatusCard(
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
    if (position == null) return;
    setState(() => _followVehicle = true);
    _lastCentered = position;
    _mapController.move(
      LatLng(position.lat, position.lon),
      _zoom.clamp(14.0, 18.0).toDouble(),
    );
  }

  void _showStation(StationInfo station) {
    showCupertinoModalPopup<void>(
      context: context,
      builder: (context) => CupertinoActionSheet(
        title: Text(station.name),
        message: Text('Orden ${station.order} · Mexibús Línea 2'),
        actions: [
          CupertinoActionSheetAction(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cerrar'),
          ),
        ],
      ),
    );
  }
}

class _HeaderCard extends StatelessWidget {
  const _HeaderCard({required this.state});

  final TransitState state;

  @override
  Widget build(BuildContext context) {
    final route = state.route;
    return _Glass(
      borderRadius: 22,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const ZentryxMark(size: 31),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Zentryx',
                  style: CupertinoTheme.of(context)
                      .textTheme
                      .textStyle
                      .copyWith(fontWeight: FontWeight.w700, fontSize: 17),
                ),
                const SizedBox(height: 1),
                Text(
                  route == null
                      ? 'Mexibús · Línea 2'
                      : '${route.networkName} · ${route.lineLabel}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: ZentryxColors.muted,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
          if (state.stale)
            const Padding(
              padding: EdgeInsets.only(left: 8),
              child: Icon(
                CupertinoIcons.wifi_slash,
                size: 17,
                color: ZentryxColors.warning,
              ),
            ),
        ],
      ),
    );
  }
}

class _RoundButton extends StatelessWidget {
  const _RoundButton({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: label,
      child: GestureDetector(
        onTap: onPressed,
        child: _Glass(
          borderRadius: 22,
          padding: const EdgeInsets.all(12),
          child: Icon(icon, size: 21, color: ZentryxColors.ink),
        ),
      ),
    );
  }
}

class _StatusCard extends StatelessWidget {
  const _StatusCard({required this.state, required this.onRefresh});

  final TransitState state;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final vehicle = state.vehicle;
    final alert = state.alerts.isEmpty ? null : state.alerts.first;
    final online = vehicle?.isOnline == true;

    return _Glass(
      borderRadius: 30,
      padding: const EdgeInsets.fromLTRB(18, 16, 14, 14),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: online
                                ? const Color(0xFF31B36B)
                                : ZentryxColors.warning,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 7),
                        Text(
                          state.loading
                              ? 'Conectando…'
                              : online
                                  ? 'Unidad en vivo'
                                  : 'Última ubicación conocida',
                          style: const TextStyle(
                            fontSize: 13,
                            color: ZentryxColors.muted,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      vehicle?.nextStationName ?? 'Esperando telemetría',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 23,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -0.6,
                        color: ZentryxColors.ink,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      _secondaryLine(vehicle),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        color: ZentryxColors.muted,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Container(
                constraints: const BoxConstraints(minWidth: 76),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                decoration: BoxDecoration(
                  color: CupertinoDynamicColor.resolve(
                    ZentryxColors.accent,
                    context,
                  ).withOpacity(0.92),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Column(
                  children: [
                    Text(
                      _eta(vehicle?.etaSeconds),
                      style: const TextStyle(
                        color: Color(0xFF153C34),
                        fontSize: 21,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.5,
                      ),
                    ),
                    const Text(
                      'ETA',
                      style: TextStyle(
                        color: Color(0xAA153C34),
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (alert != null) ...[
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
              decoration: BoxDecoration(
                color: _alertColor(alert.severity).withOpacity(0.11),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  Icon(
                    CupertinoIcons.exclamationmark_triangle_fill,
                    size: 16,
                    color: _alertColor(alert.severity),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      alert.message,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 12.5),
                    ),
                  ),
                ],
              ),
            ),
          ],
          if (state.stale || state.error != null) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Sin conexión al servidor compartido. Se conserva el último estado.',
                    style: TextStyle(
                      fontSize: 11.5,
                      color: ZentryxColors.muted,
                    ),
                  ),
                ),
                CupertinoButton(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  minSize: 30,
                  onPressed: onRefresh,
                  child: state.refreshing
                      ? const CupertinoActivityIndicator(radius: 8)
                      : const Icon(CupertinoIcons.refresh, size: 18),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  static String _secondaryLine(VehicleInfo? vehicle) {
    if (vehicle == null) return 'Conecta Tailscale para usar la API compartida';
    final direction = vehicle.directionLabel.isEmpty
        ? 'Dirección por confirmar'
        : vehicle.directionLabel;
    final distance = vehicle.distanceRemainingM;
    if (distance == null) return direction;
    final distanceText = distance >= 1000
        ? '${(distance / 1000).toStringAsFixed(1)} km'
        : '${distance.round()} m';
    return '$direction · $distanceText';
  }

  static String _eta(double? seconds) {
    if (seconds == null || !seconds.isFinite || seconds < 0) return '—';
    if (seconds < 60) return '<1 min';
    return '${(seconds / 60).ceil()} min';
  }

  static Color _alertColor(String severity) {
    return switch (severity) {
      'critical' => ZentryxColors.danger,
      'warning' => ZentryxColors.warning,
      _ => const Color(0xFF3C78D8),
    };
  }
}

class _Glass extends StatelessWidget {
  const _Glass({
    required this.child,
    required this.borderRadius,
    required this.padding,
  });

  final Widget child;
  final double borderRadius;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: CupertinoDynamicColor.resolve(
              ZentryxColors.surface,
              context,
            ).withOpacity(0.93),
            borderRadius: BorderRadius.circular(borderRadius),
            border: Border.all(
              color: CupertinoDynamicColor.resolve(
                ZentryxColors.line,
                context,
              ).withOpacity(0.9),
            ),
            boxShadow: const [
              BoxShadow(
                color: Color(0x18000000),
                blurRadius: 24,
                offset: Offset(0, 8),
              ),
            ],
          ),
          child: child,
        ),
      ),
    );
  }
}

class _AnimatedVehicleLayer extends StatefulWidget {
  const _AnimatedVehicleLayer({required this.target, required this.headingDeg});

  final LatLng target;
  final double headingDeg;

  @override
  State<_AnimatedVehicleLayer> createState() => _AnimatedVehicleLayerState();
}

class _AnimatedVehicleLayerState extends State<_AnimatedVehicleLayer>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late LatLng _from;
  late LatLng _to;

  @override
  void initState() {
    super.initState();
    _from = widget.target;
    _to = widget.target;
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1450),
      value: 1,
    );
  }

  @override
  void didUpdateWidget(covariant _AnimatedVehicleLayer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.target == widget.target) return;
    final current = _lerp(
      _from,
      _to,
      Curves.easeOutCubic.transform(_controller.value),
    );
    _from = current;
    _to = widget.target;
    _controller.forward(from: 0);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final t = Curves.easeOutCubic.transform(_controller.value);
        final point = _lerp(_from, _to, t);
        return MarkerLayer(
          markers: [
            Marker(
              point: point,
              width: 54,
              height: 54,
              child: Transform.rotate(
                angle: widget.headingDeg * math.pi / 180,
                child: Container(
                  decoration: BoxDecoration(
                    color: CupertinoDynamicColor.resolve(
                      ZentryxColors.ink,
                      context,
                    ),
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFFFFFFFF), width: 3),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x33000000),
                        blurRadius: 14,
                        offset: Offset(0, 5),
                      ),
                    ],
                  ),
                  child: const Icon(
                    CupertinoIcons.location_north_fill,
                    color: ZentryxColors.accent,
                    size: 25,
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  LatLng _lerp(LatLng a, LatLng b, double t) {
    return LatLng(
      a.latitude + (b.latitude - a.latitude) * t,
      a.longitude + (b.longitude - a.longitude) * t,
    );
  }
}
