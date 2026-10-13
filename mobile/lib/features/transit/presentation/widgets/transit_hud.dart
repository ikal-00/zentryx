import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:zentryx_mobile/design_system/zentryx_mark.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';
import 'glass_surface.dart';
import 'live_status_indicator.dart';

String occupancyLabel(String value) => switch (value.toLowerCase()) {
  'low' || 'baja' => 'Baja',
  'medium' || 'media' => 'Media',
  'high' || 'alta' => 'Alta',
  _ => 'Sin dato',
};

String etaLabel(double? seconds) {
  if (seconds == null || !seconds.isFinite || seconds < 0) return '—';
  if (seconds == 0) return 'Llegando';
  if (seconds < 60) return '<1 min';
  return '${(seconds / 60).ceil()} min';
}

bool _live(TransitState state) => !state.stale && state.vehicle?.isOnline == true;

class TransitHeaderCard extends StatelessWidget {
  const TransitHeaderCard({required this.state, super.key});
  final TransitState state;

  @override
  Widget build(BuildContext context) => GlassSurface(
    borderRadius: 22,
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
    child: Row(children: [
      const ZentryxMark(size: 32),
      const SizedBox(width: 12),
      Expanded(child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: ZentryxColors.brandStrong,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  state.route?.lineLabel ?? 'L2',
                  style: const TextStyle(
                    color: ZentryxColors.white,
                    fontWeight: FontWeight.w800,
                    fontSize: 10,
                  ),
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  state.route?.networkName ?? 'Mexibús',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Text(
            'Zentryx · Ruta y estaciones',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context),
              fontSize: 11,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      )),
      Icon(
        state.stale ? CupertinoIcons.wifi_slash : CupertinoIcons.chevron_down,
        size: 15,
        color: CupertinoDynamicColor.resolve(
          state.stale ? ZentryxColors.warning : ZentryxColors.muted,
          context,
        ),
      ),
    ]),
  );
}

class MapFollowButton extends StatelessWidget {
  const MapFollowButton({required this.following, required this.onPressed, super.key});
  final bool following;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    label: following ? 'Siguiendo unidad' : 'Volver a seguir la unidad',
    child: GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: () {
        HapticFeedback.selectionClick();
        onPressed();
      },
      child: GlassSurface(
        borderRadius: 22,
        padding: const EdgeInsets.all(15),
        child: Icon(
          following ? CupertinoIcons.location_fill : CupertinoIcons.location,
          size: 22,
          color: CupertinoDynamicColor.resolve(
            following ? ZentryxColors.action : ZentryxColors.muted,
            context,
          ),
        ),
      ),
    ),
  );
}

class TransitStatusCard extends StatelessWidget {
  const TransitStatusCard({required this.state, required this.onRefresh, super.key});
  final TransitState state;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final vehicle = state.vehicle;
    final live = _live(state);
    final muted = CupertinoDynamicColor.resolve(ZentryxColors.muted, context);
    final ink = CupertinoDynamicColor.resolve(ZentryxColors.ink, context);

    return GlassSurface(
      borderRadius: 26,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 7,
                height: 7,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: live ? ZentryxColors.success : ZentryxColors.warning,
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  vehicle == null ? 'Esperando unidad' : 'Unidad ${vehicle.vehicleId}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: muted),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(
                'PRÓXIMA ESTACIÓN',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                  color: muted,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                vehicle?.nextStationName ?? 'Esperando ubicación',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 21,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.6,
                  color: ink,
                ),
              ),
            ])),
            const SizedBox(width: 12),
            _EtaBadge(seconds: live ? vehicle?.etaSeconds : null),
          ]),
          const SizedBox(height: 6),
          Text(
            vehicle?.directionLabel.isNotEmpty == true
                ? vehicle!.directionLabel
                : 'Dirección por confirmar',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: muted),
          ),
          if (vehicle?.routeProgress != null && vehicle!.routeProgress! > 0) ...[
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(99),
              child: Container(
                height: 4,
                width: double.infinity,
                color: CupertinoDynamicColor.resolve(ZentryxColors.line, context),
                child: FractionallySizedBox(
                  alignment: Alignment.centerLeft,
                  widthFactor: vehicle.routeProgress!.clamp(0.0, 1.0),
                  child: Container(color: ZentryxColors.brandStrong),
                ),
              ),
            ),
          ],
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              _Pill(
                icon: CupertinoIcons.person_2_fill,
                label: 'Ocupación ${occupancyLabel(vehicle?.occupancyLevel ?? '')}',
                color: ZentryxColors.occupancy(vehicle?.occupancyLevel ?? ''),
              ),
              CupertinoButton(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                minimumSize: const Size(44, 32),
                onPressed: () {
                  HapticFeedback.selectionClick();
                  _showDetails(context, state);
                },
                child: const Text('Detalles', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          LiveStatusIndicator(state: state),
          if (state.alerts.isNotEmpty) _AlertsButton(state: state),
          if (state.stale || state.error != null) ...[
            const SizedBox(height: 6),
            Row(children: [
              Expanded(
                child: Text(
                  'Sin conexión · conservamos la última ubicación',
                  style: TextStyle(fontSize: 11, color: muted),
                ),
              ),
              CupertinoButton(
                padding: const EdgeInsets.only(left: 8),
                minimumSize: const Size(44, 44),
                onPressed: state.refreshing ? null : () {
                  HapticFeedback.lightImpact();
                  onRefresh();
                },
                child: state.refreshing
                    ? const CupertinoActivityIndicator(radius: 8)
                    : const Icon(CupertinoIcons.refresh, size: 18),
              ),
            ]),
          ],
        ],
      ),
    );
  }
}

class StationStatusCard extends StatelessWidget {
  const StationStatusCard({
    required this.station,
    required this.state,
    required this.onCenter,
    required this.onClose,
    super.key,
  });

  final StationInfo station;
  final TransitState state;
  final VoidCallback onCenter;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final vehicle = state.vehicle;
    final next = vehicle?.isNextStation(station) == true;
    final live = _live(state);
    final ink = CupertinoDynamicColor.resolve(ZentryxColors.ink, context);
    final muted = CupertinoDynamicColor.resolve(ZentryxColors.muted, context);

    return GlassSurface(
      borderRadius: 26,
      padding: const EdgeInsets.fromLTRB(16, 14, 12, 14),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: ZentryxColors.brandStrong,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      'ESTACIÓN #${station.order}',
                      style: const TextStyle(
                        fontSize: 9,
                        fontWeight: FontWeight.w800,
                        color: ZentryxColors.white,
                      ),
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    state.route?.lineLabel ?? 'L2',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: muted),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                station.name,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  fontSize: 21,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.6,
                  color: ink,
                ),
              ),
            ])),
            CupertinoButton(
              padding: EdgeInsets.zero,
              onPressed: () {
                HapticFeedback.selectionClick();
                onClose();
              },
              child: const Icon(
                CupertinoIcons.xmark_circle_fill,
                semanticLabel: 'Cerrar estación',
                size: 26,
              ),
            ),
          ]),
          const SizedBox(height: 8),
          if (next) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: CupertinoDynamicColor.resolve(ZentryxColors.selection, context),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  const Icon(CupertinoIcons.bus, size: 20, color: ZentryxColors.brandStrong),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Unidad ${vehicle!.vehicleId} · ${live ? etaLabel(vehicle.etaSeconds) : 'ETA no disponible'}',
                          style: TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 14,
                            color: CupertinoDynamicColor.resolve(ZentryxColors.onSelection, context),
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Ocupación ${occupancyLabel(vehicle.occupancyLevel)} · ${live ? 'En vivo' : 'Últimos datos'}',
                          style: TextStyle(fontSize: 12, color: muted),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ] else
            Text(
              'Llegadas a esta estación aún no disponibles.',
              style: TextStyle(fontSize: 13, color: muted),
            ),
          if (state.alerts.isNotEmpty) _AlertsButton(state: state),
          const SizedBox(height: 4),
          CupertinoButton(
            padding: const EdgeInsets.symmetric(vertical: 4),
            onPressed: () {
              HapticFeedback.lightImpact();
              onCenter();
            },
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(CupertinoIcons.scope, size: 16),
                SizedBox(width: 6),
                Text('Centrar estación', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _EtaBadge extends StatelessWidget {
  const _EtaBadge({required this.seconds});
  final double? seconds;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
    decoration: BoxDecoration(
      color: CupertinoDynamicColor.resolve(ZentryxColors.selection, context),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(
        color: CupertinoDynamicColor.resolve(ZentryxColors.line, context).withValues(alpha: 0.5),
        width: 0.75,
      ),
    ),
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      Text(
        etaLabel(seconds),
        style: TextStyle(
          color: CupertinoDynamicColor.resolve(ZentryxColors.onSelection, context),
          fontSize: 20,
          fontWeight: FontWeight.w800,
          letterSpacing: -0.5,
        ),
      ),
      Text(
        'LLEGADA EST.',
        style: TextStyle(
          color: CupertinoDynamicColor.resolve(ZentryxColors.onSelection, context),
          fontSize: 9,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.4,
        ),
      ),
    ]),
  );
}

class _Pill extends StatelessWidget {
  const _Pill({required this.icon, required this.label, required this.color});
  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final resolvedColor = CupertinoDynamicColor.resolve(color, context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: resolvedColor.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: resolvedColor.withValues(alpha: 0.22),
          width: 0.8,
        ),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 13, color: resolvedColor),
        const SizedBox(width: 5),
        Flexible(
          child: Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: resolvedColor,
            ),
          ),
        ),
      ]),
    );
  }
}

class _AlertsButton extends StatelessWidget {
  const _AlertsButton({required this.state});
  final TransitState state;

  @override
  Widget build(BuildContext context) {
    final alert = state.alerts.first;
    final color = CupertinoDynamicColor.resolve(
      ZentryxColors.alert(alert.severity),
      context,
    );
    return CupertinoButton(
      padding: const EdgeInsets.symmetric(vertical: 6),
      onPressed: () {
        HapticFeedback.lightImpact();
        _showDetails(context, state, alertsOnly: true);
      },
      child: Row(children: [
        Icon(CupertinoIcons.exclamationmark_triangle_fill, size: 15, color: color),
        const SizedBox(width: 7),
        Expanded(
          child: Text(
            '${state.alerts.length} alerta(s) · ${alert.message}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: color),
          ),
        ),
        Icon(CupertinoIcons.chevron_right, size: 13, color: color),
      ]),
    );
  }
}

void _showDetails(BuildContext context, TransitState state, {bool alertsOnly = false}) {
  final vehicle = state.vehicle;
  final speed = vehicle?.speedMps;
  final progress = vehicle?.routeProgress;
  final distance = vehicle?.distanceRemainingM;
  final updated = vehicle?.lastUpdate?.toLocal();

  showCupertinoModalPopup<void>(
    context: context,
    builder: (sheetContext) => CupertinoActionSheet(
      title: Text(alertsOnly ? 'Alertas del servicio' : 'Detalles de la unidad'),
      message: Column(mainAxisSize: MainAxisSize.min, children: [
        if (!alertsOnly) ...[
          Text('Unidad ${vehicle?.vehicleId ?? '—'}'),
          Text('Velocidad: ${speed != null && speed.isFinite ? (speed * 3.6).round() : '—'} km/h'),
          Text('Recorrido: ${progress != null && progress.isFinite ? (progress * 100).round() : '—'}%'),
          Text('Distancia a próxima estación: ${distance != null && distance.isFinite ? distance.round() : '—'} m'),
          Text('Actualización: ${updated ?? 'Sin hora'}'),
          if (state.error != null)
            Text(
              state.error!,
              style: TextStyle(
                color: CupertinoDynamicColor.resolve(ZentryxColors.danger, sheetContext),
              ),
            ),
          const SizedBox(height: 12),
        ],
        for (final alert in state.alerts)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Text(
              '${alert.severity == 'critical' ? 'Crítica' : alert.severity == 'warning' ? 'Aviso' : 'Información'} · ${alert.message}',
            ),
          ),
        if (alertsOnly && state.alerts.isEmpty) const Text('Sin alertas activas'),
      ]),
      cancelButton: CupertinoActionSheetAction(
        onPressed: () => Navigator.of(sheetContext).pop(),
        child: const Text('Cerrar'),
      ),
    ),
  );
}
