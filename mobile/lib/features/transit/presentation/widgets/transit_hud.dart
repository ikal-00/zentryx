import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:zentryx_mobile/design_system/zentryx_mark.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';
import 'glass_surface.dart';

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
    borderRadius: 20,
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    child: Row(children: [
      const ZentryxMark(size: 29),
      const SizedBox(width: 10),
      Expanded(child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text('${state.route?.networkName ?? 'Mexibús'} · ${state.route?.lineLabel ?? 'L2'}',
              maxLines: 1, overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          Text('Zentryx · Ruta y estaciones',
              maxLines: 1, overflow: TextOverflow.ellipsis,
              style: TextStyle(color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context), fontSize: 11)),
        ],
      )),
      Icon(state.stale ? CupertinoIcons.wifi_slash : CupertinoIcons.chevron_down,
          size: 15, color: CupertinoDynamicColor.resolve(state.stale ? ZentryxColors.warning : ZentryxColors.muted, context)),
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
      onTap: () { HapticFeedback.selectionClick(); onPressed(); },
      child: GlassSurface(
        borderRadius: 20,
        padding: const EdgeInsets.all(15),
        child: Icon(following ? CupertinoIcons.location_fill : CupertinoIcons.location,
            size: 22, color: CupertinoDynamicColor.resolve(following ? ZentryxColors.action : ZentryxColors.muted, context)),
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
    return GlassSurface(
      borderRadius: 24,
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 10),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(vehicle == null ? 'Esperando unidad' : 'Unidad ${vehicle.vehicleId}',
              maxLines: 1, overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 11, color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context))),
          const SizedBox(height: 7),
          Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('PRÓXIMA ESTACIÓN', style: TextStyle(
                  fontSize: 10, fontWeight: FontWeight.w600, color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context))),
              const SizedBox(height: 2),
              Text(vehicle?.nextStationName ?? 'Esperando ubicación',
                  maxLines: 2, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w700, letterSpacing: -0.5)),
            ])),
            const SizedBox(width: 10),
            _EtaBadge(seconds: live ? vehicle?.etaSeconds : null),
          ]),
          const SizedBox(height: 6),
          Text(vehicle?.directionLabel.isNotEmpty == true
                  ? vehicle!.directionLabel : 'Dirección por confirmar',
              maxLines: 1, overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 12, color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context))),
          const SizedBox(height: 8),
          Wrap(spacing: 8, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              _Pill(icon: CupertinoIcons.person_2_fill,
                  label: 'Ocupación ${occupancyLabel(vehicle?.occupancyLevel ?? '')}',
                  color: ZentryxColors.occupancy(vehicle?.occupancyLevel ?? '')),
              Text(state.loading ? 'Conectando…' : live ? 'En vivo' : 'Últimos datos',
                  style: TextStyle(fontSize: 11,
                      color: CupertinoDynamicColor.resolve(live ? ZentryxColors.success : ZentryxColors.warning, context))),
              CupertinoButton(
                padding: const EdgeInsets.symmetric(horizontal: 6),
                minimumSize: const Size(44, 44),
                onPressed: () => _showDetails(context, state),
                child: const Text('Detalles', style: TextStyle(fontSize: 12)),
              ),
            ],
          ),
          if (state.alerts.isNotEmpty) _AlertsButton(state: state),
          if (state.stale || state.error != null) Row(children: [
            Expanded(child: Text('Sin conexión · conservamos la última ubicación',
                style: TextStyle(fontSize: 11, color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context)))),
            CupertinoButton(
              padding: const EdgeInsets.only(left: 8),
              minimumSize: const Size(44, 44),
              onPressed: state.refreshing ? null : onRefresh,
              child: state.refreshing ? const CupertinoActivityIndicator(radius: 8)
                  : const Icon(CupertinoIcons.refresh, size: 18),
            ),
          ]),
        ],
      ),
    );
  }
}

class StationStatusCard extends StatelessWidget {
  const StationStatusCard({required this.station, required this.state,
    required this.onCenter, required this.onClose, super.key});
  final StationInfo station;
  final TransitState state;
  final VoidCallback onCenter;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    final vehicle = state.vehicle;
    final next = vehicle?.isNextStation(station) == true;
    final live = _live(state);
    return GlassSurface(
      borderRadius: 24,
      padding: const EdgeInsets.fromLTRB(16, 10, 12, 12),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('ESTACIÓN · ${state.route?.lineLabel ?? 'L2'}',
                  style: TextStyle(fontSize: 10, color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context))),
              Text(station.name, maxLines: 2, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w700)),
            ])),
            CupertinoButton(padding: EdgeInsets.zero, onPressed: onClose,
                child: const Icon(CupertinoIcons.xmark_circle_fill,
                    semanticLabel: 'Cerrar estación', size: 25)),
          ]),
          const SizedBox(height: 7),
          if (next) ...[
            Text('Unidad ${vehicle!.vehicleId} · ${live ? etaLabel(vehicle.etaSeconds) : 'ETA no disponible'}',
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
            const SizedBox(height: 5),
            Text('Ocupación ${occupancyLabel(vehicle.occupancyLevel)} · ${live ? 'En vivo' : 'Últimos datos'}',
                style: TextStyle(fontSize: 12, color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context))),
          ] else
            Text('Llegadas a esta estación aún no disponibles.',
                style: TextStyle(fontSize: 13, color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context))),
          if (state.alerts.isNotEmpty) _AlertsButton(state: state),
          CupertinoButton(padding: const EdgeInsets.only(top: 8), onPressed: onCenter,
              child: const Text('Centrar estación', style: TextStyle(fontSize: 13))),
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
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
    decoration: BoxDecoration(color: CupertinoDynamicColor.resolve(ZentryxColors.selection, context), borderRadius: BorderRadius.circular(16)),
    child: Column(mainAxisSize: MainAxisSize.min, children: [
      Text(etaLabel(seconds), style: TextStyle(color: CupertinoDynamicColor.resolve(ZentryxColors.onSelection, context),
          fontSize: 20, fontWeight: FontWeight.w800)),
      Text('LLEGADA EST.', style: TextStyle(color: CupertinoDynamicColor.resolve(ZentryxColors.onSelection, context), fontSize: 9)),
    ]),
  );
}

class _Pill extends StatelessWidget {
  const _Pill({required this.icon, required this.label, required this.color});
  final IconData icon;
  final String label;
  final Color color;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
    decoration: BoxDecoration(color: CupertinoDynamicColor.resolve(ZentryxColors.line, context),
        borderRadius: BorderRadius.circular(12)),
    child: Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, size: 13, color: CupertinoDynamicColor.resolve(color, context)),
      const SizedBox(width: 5),
      Flexible(child: Text(label, style: TextStyle(fontSize: 11, color: CupertinoDynamicColor.resolve(color, context)))),
    ]),
  );
}

class _AlertsButton extends StatelessWidget {
  const _AlertsButton({required this.state});
  final TransitState state;
  @override
  Widget build(BuildContext context) {
    final alert = state.alerts.first;
    return CupertinoButton(
      padding: const EdgeInsets.symmetric(vertical: 6),
      onPressed: () => _showDetails(context, state, alertsOnly: true),
      child: Row(children: [
        Icon(CupertinoIcons.exclamationmark_triangle_fill, size: 15,
            color: CupertinoDynamicColor.resolve(ZentryxColors.alert(alert.severity), context)),
        const SizedBox(width: 7),
        Expanded(child: Text('${state.alerts.length} alerta(s) · ${alert.message}',
            maxLines: 1, overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 12))),
        const Icon(CupertinoIcons.chevron_right, size: 13),
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
  showCupertinoModalPopup<void>(context: context, builder: (sheetContext) => CupertinoActionSheet(
    title: Text(alertsOnly ? 'Alertas del servicio' : 'Detalles de la unidad'),
    message: Column(mainAxisSize: MainAxisSize.min, children: [
      if (!alertsOnly) ...[
        Text('Unidad ${vehicle?.vehicleId ?? '—'}'),
        Text('Velocidad: ${speed != null && speed.isFinite ? (speed * 3.6).round() : '—'} km/h'),
        Text('Recorrido: ${progress != null && progress.isFinite ? (progress * 100).round() : '—'}%'),
        Text('Distancia a próxima estación: ${distance != null && distance.isFinite ? distance.round() : '—'} m'),
        Text('Actualización: ${updated ?? 'Sin hora'}'),
        if (state.error != null) Text(state.error!, style: TextStyle(
            color: CupertinoDynamicColor.resolve(ZentryxColors.danger, sheetContext))),
        const SizedBox(height: 12),
      ],
      for (final alert in state.alerts) Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Text('${alert.severity == 'critical' ? 'Crítica' : alert.severity == 'warning' ? 'Aviso' : 'Información'} · ${alert.message}'),
      ),
      if (alertsOnly && state.alerts.isEmpty) const Text('Sin alertas activas'),
    ]),
    cancelButton: CupertinoActionSheetAction(onPressed: () => Navigator.of(sheetContext).pop(),
        child: const Text('Cerrar')),
  ));
}
