import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:zentryx_mobile/design_system/relative_time.dart';
import 'package:zentryx_mobile/design_system/system_status.dart';
import 'package:zentryx_mobile/design_system/zentryx_layout.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';

import '../application/driver_session.dart';
import '../application/device_telemetry_controller.dart';
import 'prepare_trip_screen.dart';
import 'device_diagnostics_screen.dart';
import 'widgets/device_status.dart';

class DriverScreen extends ConsumerWidget {
  const DriverScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(driverSessionProvider);
    if (!session.active) return const PrepareTripScreen();
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
                      Text(
                        session.unit!.name,
                        style: const TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        session.unit!.line,
                        style: TextStyle(fontSize: 15, color: muted),
                      ),
                      const SizedBox(height: 16),
                      Consumer(
                        builder: (context, ref, _) => Align(
                          alignment: Alignment.centerLeft,
                          child: TelemetrySourceBadge(
                            telemetry: ref.watch(deviceTelemetryProvider),
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),
                      ZentryxCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Semantics(
                              liveRegion: true,
                              child: const Text(
                                'Recorrido activo',
                                style: TextStyle(
                                  fontSize: 22,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            const SizedBox(height: 12),
                            TimeLabel(
                              builder: (now) {
                                final seconds = now
                                    .difference(session.startedAt!)
                                    .inSeconds
                                    .clamp(0, 9999999);
                                final clock =
                                    '${(seconds ~/ 3600).toString().padLeft(2, '0')}:${((seconds ~/ 60) % 60).toString().padLeft(2, '0')}:${(seconds % 60).toString().padLeft(2, '0')}';
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
                                          fontSize: 44,
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
                            const SizedBox(height: 20),
                            ZentryxPrimaryButton(
                              label: session.busy
                                  ? 'Guardando…'
                                  : 'Finalizar recorrido',
                              icon: CupertinoIcons.stop_fill,
                              onPressed: session.canEdit
                                  ? () => _stop(context, ref)
                                  : null,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),
                      Consumer(
                        builder: (context, ref, _) {
                          final device = ref.watch(deviceTelemetryProvider);
                          return device.unit.id == session.unit!.id
                              ? const DeviceStatusPanel()
                              : const SystemStatusCard(
                                  status: SystemStatus.warning,
                                  title: 'Dispositivo de otra unidad',
                                  message: 'La fuente actual no corresponde al recorrido guardado. Revisa el diagnóstico antes de usar sus datos.',
                                );
                        },
                      ),
                      CupertinoButton(
                        onPressed: () => showDeviceDiagnostics(context),
                        child: const Text('Ver diagnóstico'),
                      ),
                      if (session.storageError != null) ...[
                        SystemStatusCard(
                          status: SystemStatus.error,
                          title: 'Cambio sin guardar',
                          message: session.storageError!,
                        ),
                        const SizedBox(height: 20),
                      ],
                      if (session.lastIncident != null)
                        ZentryxCard(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Último reporte',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              const SizedBox(height: 10),
                              Text(session.lastIncident!.label),
                              const SizedBox(height: 8),
                              Text(
                                _reportTime(session.reportedAt!),
                                style: TextStyle(fontSize: 13, color: muted),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                'Reporte registrado localmente. Sin envío al servidor.',
                                style: TextStyle(
                                  fontSize: 12,
                                  height: 1.4,
                                  color: muted,
                                ),
                              ),
                            ],
                          ),
                        ),
                      const SizedBox(height: 20),
                      Text(
                        'El recorrido se recuperará al volver a abrir la app. Reporta únicamente con la unidad detenida.',
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
                          onPressed: session.canEdit
                              ? () => _report(context, ref)
                              : null,
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

  String _reportTime(DateTime value) {
    final local = value.toLocal();
    return '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')} · ${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}';
  }

  Future<void> _report(BuildContext context, WidgetRef ref) async {
    HapticFeedback.selectionClick();
    final incident = await showCupertinoModalPopup<IncidentType>(
      context: context,
      builder: (sheetContext) => CupertinoActionSheet(
        title: const Text('Reportar incidente'),
        message: const Text(
          'Se guardará en este dispositivo. No se enviará al servidor.',
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
    final saved = await ref
        .read(driverSessionProvider.notifier)
        .report(incident);
    if (saved) HapticFeedback.lightImpact();
  }

  Future<void> _stop(BuildContext context, WidgetRef ref) async {
    final confirmed = await showCupertinoDialog<bool>(
      context: context,
      builder: (dialogContext) => CupertinoAlertDialog(
        title: const Text('¿Finalizar recorrido?'),
        content: const Text(
          'El temporizador se detendrá. El último reporte seguirá guardado localmente.',
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
      await ref.read(driverSessionProvider.notifier).stop();
      HapticFeedback.selectionClick();
    }
  }
}
