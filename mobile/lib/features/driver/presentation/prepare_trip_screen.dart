import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:zentryx_mobile/design_system/system_status.dart';
import 'package:zentryx_mobile/design_system/zentryx_layout.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';

import '../application/device_telemetry_controller.dart';
import '../application/driver_session.dart';
import 'device_diagnostics_screen.dart';
import 'widgets/device_status.dart';

class PrepareTripScreen extends ConsumerWidget {
  const PrepareTripScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(driverSessionProvider);
    final device = ref.watch(deviceTelemetryProvider);
    final muted = CupertinoDynamicColor.resolve(ZentryxColors.muted, context);
    return CupertinoPageScaffold(
      navigationBar: const CupertinoNavigationBar(
        middle: Text('Preparar recorrido'),
        previousPageTitle: 'Inicio',
      ),
      child: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(
              maxWidth: ZentryxLayout.maxContentWidth,
            ),
            child: ListView(
              padding: ZentryxLayout.pagePadding,
              children: [
                const Text(
                  'Antes de salir,\ntodo en su lugar.',
                  style: TextStyle(
                    fontSize: 30,
                    fontWeight: FontWeight.w700,
                    height: 1.1,
                    letterSpacing: -0.8,
                  ),
                ),
                const SizedBox(height: 16),
                Align(
                  alignment: Alignment.centerLeft,
                  child: TelemetrySourceBadge(telemetry: device),
                ),
                const SizedBox(height: 24),
                ZentryxCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        device.unit.name,
                        style: const TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        device.unit.line,
                        style: TextStyle(color: muted, fontSize: 15),
                      ),
                      const SizedBox(height: 20),
                      DriverDetailRow(
                        label: 'Dispositivo',
                        value: device.deviceId,
                      ),
                      const SizedBox(height: 12),
                      DriverDetailRow(
                        label: 'Fuente',
                        value: device.sourceLabel,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                const DeviceStatusPanel(),
                const SizedBox(height: 12),
                CupertinoButton(
                  onPressed: () => showDeviceDiagnostics(context),
                  child: const Text('Ver diagnóstico'),
                ),
                if (session.storageError != null) ...[
                  SystemStatusCard(
                    status: SystemStatus.error,
                    title: 'Sesión sin guardar',
                    message: session.storageError!,
                  ),
                  if (!session.restored)
                    CupertinoButton(
                      onPressed: () => ref
                          .read(driverSessionProvider.notifier)
                          .retryRestore(),
                      child: const Text('Reintentar recuperación'),
                    ),
                  const SizedBox(height: 16),
                ],
                if (!session.restored && session.storageError == null) ...[
                  const SystemStatusBadge(
                    status: SystemStatus.syncing,
                    label: 'Recuperando recorrido guardado',
                  ),
                  const SizedBox(height: 16),
                ],
                ZentryxPrimaryButton(
                  label: session.busy
                      ? 'Guardando recorrido…'
                      : 'Iniciar recorrido',
                  icon: CupertinoIcons.play_fill,
                  onPressed: !session.canEdit
                      ? null
                      : () async {
                          HapticFeedback.mediumImpact();
                          await ref
                              .read(driverSessionProvider.notifier)
                              .start(device.unit);
                        },
                ),
                const SizedBox(height: 16),
                Text(
                  device.simulated
                      ? 'La telemetría es simulada. El recorrido se guarda en este dispositivo.'
                      : 'Revisa las comprobaciones antes de iniciar. El recorrido se guarda en este dispositivo.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, height: 1.5, color: muted),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
