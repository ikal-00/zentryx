import 'package:flutter/cupertino.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:zentryx_mobile/design_system/relative_time.dart';
import 'package:zentryx_mobile/design_system/system_status.dart';
import 'package:zentryx_mobile/design_system/zentryx_layout.dart';

import '../application/device_telemetry_controller.dart';
import '../domain/device_telemetry.dart';
import 'widgets/device_status.dart';

void showDeviceDiagnostics(BuildContext context) => Navigator.of(context)
    .push<void>(
      CupertinoPageRoute<void>(builder: (_) => const DeviceDiagnosticsScreen()),
    );

class DeviceDiagnosticsScreen extends ConsumerWidget {
  const DeviceDiagnosticsScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(deviceTelemetryProvider);
    return CupertinoPageScaffold(
      navigationBar: const CupertinoNavigationBar(
        middle: Text('Diagnóstico de unidad'),
        previousPageTitle: 'Conductor',
      ),
      child: SafeArea(
        child: Align(
          alignment: Alignment.topCenter,
          child: ConstrainedBox(
            constraints: const BoxConstraints(
              maxWidth: ZentryxLayout.maxContentWidth,
            ),
            child: TimeLabel(
              builder: (now) {
                final health = data.healthAt(now);
                return ListView(
                  padding: ZentryxLayout.pagePadding,
                  children: [
                    Align(
                      alignment: Alignment.centerLeft,
                      child: TelemetrySourceBadge(telemetry: data),
                    ),
                    const SizedBox(height: 20),
                    _Section(
                      title: 'Dispositivo',
                      rows: [
                        DriverDetailRow(
                          label: 'Device ID',
                          value: data.deviceId,
                        ),
                        DriverDetailRow(label: 'Unidad', value: data.unit.name),
                        DriverDetailRow(label: 'Línea', value: data.unit.line),
                        DriverDetailRow(
                          label: 'Firmware',
                          value: data.firmware ?? 'Sin datos',
                        ),
                        DriverDetailRow(
                          label: 'Fuente',
                          value: data.sourceLabel,
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    _Section(
                      title: 'Conectividad',
                      rows: [
                        DeviceChecks(telemetry: data, now: now),
                        DriverDetailRow(
                          label: 'Último paquete',
                          value: updatedAgo(data.lastPacketAt, now),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    _Section(
                      title: 'GPS',
                      rows: [
                        DriverDetailRow(
                          label: 'Estado',
                          value: data.signal == DeviceSignal.waiting
                              ? 'Esperando datos'
                              : data.signal == DeviceSignal.syncing
                              ? 'Sincronizando'
                              : data.signal == DeviceSignal.failure
                              ? 'Fallo del dispositivo'
                              : !data.connected ||
                                    data.signal == DeviceSignal.disconnected
                              ? 'Dispositivo desconectado'
                              : !data.fresh(data.lastPacketAt, now)
                              ? 'Datos antiguos'
                              : data.gpsAvailable &&
                                    data.validPosition &&
                                    data.fresh(data.lastGpsFixAt, now)
                              ? 'Activo'
                              : 'Sin fix reciente',
                        ),
                        DriverDetailRow(
                          label: 'Latitud',
                          value: data.validPosition
                              ? data.latitude!.toStringAsFixed(6)
                              : 'Sin datos',
                        ),
                        DriverDetailRow(
                          label: 'Longitud',
                          value: data.validPosition
                              ? data.longitude!.toStringAsFixed(6)
                              : 'Sin datos',
                        ),
                        DriverDetailRow(
                          label: 'Precisión',
                          value: data.validAccuracy
                              ? '± ${data.accuracyMeters!.toStringAsFixed(0)} m'
                              : 'Sin datos',
                        ),
                        DriverDetailRow(
                          label: 'Último fix',
                          value: updatedAgo(data.lastGpsFixAt, now),
                        ),
                        if (!data.fresh(data.lastGpsFixAt, now) &&
                            data.validPosition)
                          const Text(
                            'Coordenadas del último fix; no representan una posición actual.',
                            style: TextStyle(fontSize: 12),
                          ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    SystemStatusCard(
                      status: health.status,
                      title: health.label,
                      message: data.simulated
                          ? 'Fuente simulada. No hay un dispositivo físico conectado ni envío real de ubicación.'
                          : 'Los estados se calculan a partir de la fuente del dispositivo y la antigüedad de sus datos.',
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.rows});
  final String title;
  final List<Widget> rows;
  @override
  Widget build(BuildContext context) => ZentryxCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
        ),
        for (final row in rows) ...[const SizedBox(height: 16), row],
      ],
    ),
  );
}
