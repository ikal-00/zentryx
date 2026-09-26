import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:zentryx_mobile/design_system/zentryx_mark.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';
import 'package:zentryx_mobile/features/transit/presentation/widgets/glass_surface.dart';

class TransitHeaderCard extends StatelessWidget {
  const TransitHeaderCard({required this.state, super.key});

  final TransitState state;

  @override
  Widget build(BuildContext context) {
    final route = state.route;
    return GlassSurface(
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
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 220),
            child: state.stale
                ? const Padding(
                    key: ValueKey('offline'),
                    padding: EdgeInsets.only(left: 8),
                    child: Icon(
                      CupertinoIcons.wifi_slash,
                      size: 17,
                      color: ZentryxColors.warning,
                    ),
                  )
                : const SizedBox(key: ValueKey('online'), width: 0, height: 0),
          ),
        ],
      ),
    );
  }
}

class MapFollowButton extends StatelessWidget {
  const MapFollowButton({
    required this.following,
    required this.onPressed,
    super.key,
  });

  final bool following;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final label = following ? 'Siguiendo unidad' : 'Centrar unidad';
    return Semantics(
      button: true,
      label: label,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () {
          HapticFeedback.selectionClick();
          onPressed();
        },
        child: AnimatedScale(
          scale: following ? 1 : 0.96,
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeOutBack,
          child: GlassSurface(
            borderRadius: 22,
            padding: const EdgeInsets.all(12),
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 180),
              child: Icon(
                following
                    ? CupertinoIcons.location_fill
                    : CupertinoIcons.location,
                key: ValueKey(following),
                size: 21,
                color: ZentryxColors.ink,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class TransitStatusCard extends StatelessWidget {
  const TransitStatusCard({
    required this.state,
    required this.onRefresh,
    super.key,
  });

  final TransitState state;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final vehicle = state.vehicle;
    final alert = state.alerts.isEmpty ? null : state.alerts.first;
    final online = vehicle?.isOnline == true;

    return GlassSurface(
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
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 250),
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
                        Flexible(
                          child: Text(
                            state.loading
                                ? 'Conectando…'
                                : online
                                    ? 'Unidad en vivo'
                                    : 'Última ubicación conocida',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 13,
                              color: ZentryxColors.muted,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 260),
                      transitionBuilder: (child, animation) => FadeTransition(
                        opacity: animation,
                        child: SlideTransition(
                          position: Tween<Offset>(
                            begin: const Offset(0, 0.08),
                            end: Offset.zero,
                          ).animate(animation),
                          child: child,
                        ),
                      ),
                      child: Text(
                        vehicle?.nextStationName ?? 'Esperando telemetría',
                        key: ValueKey(vehicle?.nextStationName),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 23,
                          fontWeight: FontWeight.w700,
                          letterSpacing: -0.6,
                          color: ZentryxColors.ink,
                        ),
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
              _EtaBadge(seconds: vehicle?.etaSeconds),
            ],
          ),
          if (vehicle != null) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                _InfoPill(
                  icon: CupertinoIcons.person_2_fill,
                  label: _occupancy(vehicle.occupancyLevel),
                ),
                const SizedBox(width: 8),
                _InfoPill(
                  icon: CupertinoIcons.speedometer,
                  label: _speed(vehicle.speedMps),
                ),
                const Spacer(),
                Text(
                  _freshness(vehicle.lastUpdate),
                  style: const TextStyle(
                    color: ZentryxColors.muted,
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
            if (vehicle.routeProgress case final progress?) ...[
              const SizedBox(height: 11),
              _RouteProgress(progress: progress),
            ],
          ],
          if (alert != null) ...[
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
              decoration: BoxDecoration(
                color: _alertColor(alert.severity).withValues(alpha: 0.11),
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
                      state.alerts.length > 1
                          ? '${alert.message}  +${state.alerts.length - 1}'
                          : alert.message,
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
                Expanded(
                  child: Text(
                    state.error ??
                        'Sin conexión al servidor compartido. Se conserva el último estado.',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 11.5,
                      color: ZentryxColors.muted,
                    ),
                  ),
                ),
                CupertinoButton(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  minimumSize: const Size(30, 30),
                  onPressed: () {
                    HapticFeedback.selectionClick();
                    onRefresh();
                  },
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

  static String _occupancy(String value) {
    return switch (value.toLowerCase()) {
      'low' || 'baja' => 'Baja',
      'medium' || 'media' => 'Media',
      'high' || 'alta' => 'Alta',
      _ => 'Sin dato',
    };
  }

  static String _speed(double metersPerSecond) {
    if (!metersPerSecond.isFinite || metersPerSecond <= 0) return '0 km/h';
    return '${(metersPerSecond * 3.6).round()} km/h';
  }

  static String _freshness(DateTime? value) {
    if (value == null) return 'Sin hora';
    final age = DateTime.now().difference(value.toLocal());
    if (age.inSeconds < 15) return 'Ahora';
    if (age.inMinutes < 1) return '${age.inSeconds}s';
    if (age.inHours < 1) return '${age.inMinutes} min';
    return '${age.inHours} h';
  }

  static Color _alertColor(String severity) {
    return switch (severity) {
      'critical' => ZentryxColors.danger,
      'warning' => ZentryxColors.warning,
      _ => const Color(0xFF3C78D8),
    };
  }
}

class _EtaBadge extends StatelessWidget {
  const _EtaBadge({required this.seconds});

  final double? seconds;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 260),
      constraints: const BoxConstraints(minWidth: 76),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: CupertinoDynamicColor.resolve(
          ZentryxColors.accent,
          context,
        ).withValues(alpha: 0.94),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: [
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 220),
            child: Text(
              _eta(seconds),
              key: ValueKey(_eta(seconds)),
              style: const TextStyle(
                color: Color(0xFF153C34),
                fontSize: 21,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.5,
              ),
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
    );
  }

  static String _eta(double? seconds) {
    if (seconds == null || !seconds.isFinite || seconds < 0) return '—';
    if (seconds < 60) return '<1 min';
    return '${(seconds / 60).ceil()} min';
  }
}

class _InfoPill extends StatelessWidget {
  const _InfoPill({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(
        color: CupertinoDynamicColor.resolve(ZentryxColors.line, context)
            .withValues(alpha: 0.55),
        borderRadius: BorderRadius.circular(13),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: ZentryxColors.muted),
          const SizedBox(width: 5),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              color: ZentryxColors.muted,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _RouteProgress extends StatelessWidget {
  const _RouteProgress({required this.progress});

  final double progress;

  @override
  Widget build(BuildContext context) {
    final value = progress.clamp(0.0, 1.0).toDouble();
    return Column(
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            return Container(
              height: 4,
              width: double.infinity,
              decoration: BoxDecoration(
                color: CupertinoDynamicColor.resolve(ZentryxColors.line, context),
                borderRadius: BorderRadius.circular(99),
              ),
              alignment: Alignment.centerLeft,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 700),
                curve: Curves.easeOutCubic,
                width: constraints.maxWidth * value,
                decoration: BoxDecoration(
                  color: CupertinoDynamicColor.resolve(
                    ZentryxColors.accent,
                    context,
                  ),
                  borderRadius: BorderRadius.circular(99),
                ),
              ),
            );
          },
        ),
        const SizedBox(height: 5),
        Row(
          children: [
            const Text(
              'Recorrido',
              style: TextStyle(fontSize: 10.5, color: ZentryxColors.muted),
            ),
            const Spacer(),
            Text(
              '${(value * 100).round()}%',
              style: const TextStyle(
                fontSize: 10.5,
                color: ZentryxColors.muted,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ],
    );
  }
}
