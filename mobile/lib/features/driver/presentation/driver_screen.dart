import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:zentryx_mobile/design_system/relative_time.dart';
import 'package:zentryx_mobile/design_system/system_status.dart';
import 'package:zentryx_mobile/design_system/zentryx_layout.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';

import '../application/driver_session.dart';

class DriverScreen extends ConsumerWidget {
  const DriverScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(driverSessionProvider);
    final muted = CupertinoDynamicColor.resolve(ZentryxColors.muted, context);
    return CupertinoPageScaffold(
      navigationBar: const CupertinoNavigationBar(
        middle: Text('Modo conductor'),
        previousPageTitle: 'Inicio',
      ),
      child: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: Align(
                alignment: Alignment.topCenter,
                child: ConstrainedBox(
                  constraints: const BoxConstraints(
                    maxWidth: ZentryxLayout.maxContentWidth,
                  ),
                  child: ListView(
                    padding: ZentryxLayout.pagePadding,
                    children: [
                      const Text(
                        'Tu ruta, bajo control.',
                        style: TextStyle(
                          fontSize: 29,
                          height: 1.1,
                          fontWeight: FontWeight.w700,
                          letterSpacing: -0.8,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          const SystemStatusBadge(
                            status: SystemStatus.syncing,
                            label: 'Simulación local',
                          ),
                          SystemStatusBadge(
                            status: session.active
                                ? SystemStatus.connected
                                : SystemStatus.disconnected,
                            label: session.active
                                ? 'Conexión simulada'
                                : 'Sin conexión al chip',
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      ZentryxCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: CupertinoDynamicColor.resolve(
                                      ZentryxColors.selection,
                                      context,
                                    ),
                                    borderRadius: ZentryxLayout.controlRadius,
                                  ),
                                  child: Icon(
                                    CupertinoIcons.bus,
                                    size: 28,
                                    color: CupertinoDynamicColor.resolve(
                                      ZentryxColors.action,
                                      context,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      const Text(
                                        'Unidad 01',
                                        style: TextStyle(
                                          fontSize: 23,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                      Text(
                                        'Mexibús Línea 2',
                                        style: TextStyle(
                                          fontSize: 13,
                                          color: muted,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 20),
                            _DetailRow(
                              label: 'Estado GPS',
                              value: session.active
                                  ? 'Activo · simulado'
                                  : 'Pendiente de chip',
                            ),
                            const SizedBox(height: 12),
                            _DetailRow(
                              label: 'Conexión',
                              value: session.active
                                  ? 'Local · sin envío real'
                                  : 'Sin conectar',
                            ),
                            const SizedBox(height: 12),
                            const _DetailRow(
                              label: 'Última actualización GPS',
                              value: 'Sin telemetría real',
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),
                      ZentryxCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'RECORRIDO',
                              style: TextStyle(
                                fontSize: 11,
                                letterSpacing: 1.4,
                                fontWeight: FontWeight.w700,
                                color: muted,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Semantics(
                              liveRegion: true,
                              child: Text(
                                session.active
                                    ? 'Recorrido activo'
                                    : 'Tu recorrido comienza aquí',
                                style: const TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: -0.5,
                                ),
                              ),
                            ),
                            const SizedBox(height: 12),
                            if (session.active) ...[
                              TimeLabel(
                                builder: (now) {
                                  final seconds = now
                                      .difference(session.startedAt!)
                                      .inSeconds
                                      .clamp(0, 999999);
                                  final hours = seconds ~/ 3600;
                                  final minutes = (seconds ~/ 60) % 60;
                                  final clock =
                                      '${hours.toString().padLeft(2, '0')}:${minutes.toString().padLeft(2, '0')}:${(seconds % 60).toString().padLeft(2, '0')}';
                                  return Semantics(
                                    label: 'Tiempo de recorrido: $clock',
                                    child: ExcludeSemantics(
                                      child: FittedBox(
                                        fit: BoxFit.scaleDown,
                                        alignment: Alignment.centerLeft,
                                        child: Text(
                                          clock,
                                          maxLines: 1,
                                          softWrap: false,
                                          style: const TextStyle(
                                            fontSize: 40,
                                            fontWeight: FontWeight.w600,
                                            letterSpacing: -1,
                                            fontFeatures: [
                                              FontFeature.tabularFigures(),
                                            ],
                                          ),
                                        ),
                                      ),
                                    ),
                                  );
                                },
                              ),
                              const SizedBox(height: 12),
                              const SystemStatusBadge(
                                status: SystemStatus.connected,
                                label: 'GPS activo · simulado',
                              ),
                              const SizedBox(height: 8),
                              Text(
                                'Enviando ubicación · simulación',
                                style: TextStyle(fontSize: 13, color: muted),
                              ),
                              const SizedBox(height: 20),
                              ZentryxPrimaryButton(
                                label: 'Finalizar recorrido',
                                icon: CupertinoIcons.stop_fill,
                                onPressed: () => _stop(context, ref),
                              ),
                            ] else ...[
                              Text(
                                'Activa una sesión de prueba para conocer los controles.',
                                style: TextStyle(
                                  fontSize: 14,
                                  height: 1.4,
                                  color: muted,
                                ),
                              ),
                              const SizedBox(height: 20),
                              ZentryxPrimaryButton(
                                label: 'Iniciar recorrido',
                                icon: CupertinoIcons.play_fill,
                                onPressed: () {
                                  HapticFeedback.mediumImpact();
                                  ref
                                      .read(driverSessionProvider.notifier)
                                      .start();
                                },
                              ),
                            ],
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),
                      ZentryxCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Incidencias',
                              style: TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Reporta en dos toques. Hazlo con la unidad detenida.',
                              style: TextStyle(
                                fontSize: 13,
                                height: 1.4,
                                color: muted,
                              ),
                            ),
                            if (session.lastIncident != null) ...[
                              const SizedBox(height: 14),
                              Semantics(
                                liveRegion: true,
                                child: SystemStatusBadge(
                                  status: SystemStatus.connected,
                                  label:
                                      'Último incidente: ${session.lastIncident!.label}',
                                ),
                              ),
                              const SizedBox(height: 6),
                              TimeLabel(
                                builder: (now) => Text(
                                  updatedAgo(session.reportedAt, now),
                                  style: TextStyle(fontSize: 12, color: muted),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),
                      Text(
                        'Modo de prueba: no envía ubicación ni reportes. La sesión se conserva al volver al inicio y se borra al cerrar la app.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 12,
                          height: 1.5,
                          color: muted,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            Align(
              child: ConstrainedBox(
                constraints: const BoxConstraints(
                  maxWidth: ZentryxLayout.maxContentWidth,
                ),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(24, 10, 24, 12),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (session.lastIncident != null) ...[
                        Semantics(
                          liveRegion: true,
                          child: SystemStatusBadge(
                            status: SystemStatus.connected,
                            label:
                                'Registrado localmente: ${session.lastIncident!.label}',
                          ),
                        ),
                        const SizedBox(height: 8),
                      ],
                      SizedBox(
                        width: double.infinity,
                        child: CupertinoButton(
                          color: CupertinoDynamicColor.resolve(
                            ZentryxColors.selection,
                            context,
                          ),
                          borderRadius: ZentryxLayout.controlRadius,
                          onPressed: () => _report(context, ref),
                          child: Text(
                            'Reportar incidente',
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                              color: CupertinoDynamicColor.resolve(
                                ZentryxColors.onSelection,
                                context,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _report(BuildContext context, WidgetRef ref) async {
    HapticFeedback.selectionClick();
    final incident = await showCupertinoModalPopup<IncidentType>(
      context: context,
      builder: (sheetContext) => CupertinoActionSheet(
        title: const Text('Reportar incidente'),
        message: const Text(
          'Selecciona el tipo. Se registrará solo en esta sesión.',
        ),
        actions: [
          for (final type in IncidentType.values)
            CupertinoActionSheetAction(
              onPressed: () => Navigator.of(sheetContext).pop(type),
              child: Text(type.label),
            ),
        ],
        cancelButton: CupertinoActionSheetAction(
          onPressed: () => Navigator.of(sheetContext).pop(),
          child: const Text('Cancelar'),
        ),
      ),
    );
    if (incident == null || !context.mounted) return;
    ref.read(driverSessionProvider.notifier).report(incident);
    HapticFeedback.lightImpact();
  }

  Future<void> _stop(BuildContext context, WidgetRef ref) async {
    final confirmed = await showCupertinoDialog<bool>(
      context: context,
      builder: (dialogContext) => CupertinoAlertDialog(
        title: const Text('¿Finalizar recorrido?'),
        content: const Text(
          'El temporizador se detendrá. Tus reportes locales se conservan durante esta sesión.',
        ),
        actions: [
          CupertinoDialogAction(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Continuar'),
          ),
          CupertinoDialogAction(
            isDefaultAction: true,
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Finalizar'),
          ),
        ],
      ),
    );
    if (confirmed == true && context.mounted) {
      ref.read(driverSessionProvider.notifier).stop();
      HapticFeedback.selectionClick();
    }
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final title = Text(
        label,
        style: TextStyle(
          fontSize: 13,
          color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context),
        ),
      );
      final detail = Text(
        value,
        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
      );
      if (MediaQuery.textScalerOf(context).scale(13) > 18 ||
          constraints.maxWidth < 280) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [title, const SizedBox(height: 4), detail],
        );
      }
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(child: title),
          const SizedBox(width: 12),
          Flexible(
            child: Align(alignment: Alignment.centerRight, child: detail),
          ),
        ],
      );
    },
  );
}
