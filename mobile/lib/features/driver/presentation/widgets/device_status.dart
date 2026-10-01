import 'package:flutter/cupertino.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:zentryx_mobile/design_system/relative_time.dart';
import 'package:zentryx_mobile/design_system/system_status.dart';
import 'package:zentryx_mobile/design_system/zentryx_layout.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';

import '../../application/device_telemetry_controller.dart';
import '../../domain/device_telemetry.dart';

extension TelemetryHealthPresentation on TelemetryHealth {
  SystemStatus get status => switch (this) {
    TelemetryHealth.operational => SystemStatus.connected,
    TelemetryHealth.waiting => SystemStatus.noData,
    TelemetryHealth.syncing => SystemStatus.syncing,
    TelemetryHealth.disconnected => SystemStatus.disconnected,
    TelemetryHealth.noGps || TelemetryHealth.noServer => SystemStatus.warning,
    TelemetryHealth.stale => SystemStatus.stale,
    TelemetryHealth.failure => SystemStatus.error,
  };
  String get label => switch (this) {
    TelemetryHealth.operational => 'Operativo',
    TelemetryHealth.waiting => 'Esperando primer paquete',
    TelemetryHealth.syncing => 'Sincronizando',
    TelemetryHealth.disconnected => 'Dispositivo desconectado',
    TelemetryHealth.noGps => 'GPS sin señal',
    TelemetryHealth.noServer => 'Servidor desconectado',
    TelemetryHealth.stale => 'Telemetría atrasada',
    TelemetryHealth.failure => 'Fallo del dispositivo',
  };
}

class TelemetrySourceBadge extends StatelessWidget {
  const TelemetrySourceBadge({required this.telemetry, super.key});
  final DeviceTelemetry telemetry;
  @override
  Widget build(BuildContext context) => SystemStatusBadge(
    status: SystemStatus.syncing,
    label: telemetry.simulated
        ? 'Entorno de simulación'
        : 'Fuente: ${telemetry.sourceLabel}',
  );
}

class DeviceChecks extends StatelessWidget {
  const DeviceChecks({required this.telemetry, required this.now, super.key});
  final DeviceTelemetry telemetry;
  final DateTime now;
  @override
  Widget build(BuildContext context) {
    final health = telemetry.healthAt(now);
    final pending =
        health == TelemetryHealth.waiting || health == TelemetryHealth.syncing;
    final packetFresh = telemetry.fresh(telemetry.lastPacketAt, now);
    final deviceStatus = health == TelemetryHealth.failure
        ? SystemStatus.error
        : pending
        ? health.status
        : !telemetry.connected
        ? SystemStatus.disconnected
        : !packetFresh
        ? SystemStatus.stale
        : SystemStatus.connected;
    final gpsStatus = deviceStatus != SystemStatus.connected
        ? deviceStatus
        : telemetry.gpsAvailable &&
              telemetry.validPosition &&
              telemetry.fresh(telemetry.lastGpsFixAt, now)
        ? SystemStatus.connected
        : SystemStatus.warning;
    final serverStatus = deviceStatus != SystemStatus.connected
        ? deviceStatus
        : telemetry.serverConnected
        ? SystemStatus.connected
        : SystemStatus.warning;
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        SystemStatusBadge(
          status: deviceStatus,
          label:
              'Dispositivo · ${deviceStatus == SystemStatus.connected ? 'Conectado' : deviceStatus.label}',
        ),
        SystemStatusBadge(
          status: gpsStatus,
          label:
              'GPS · ${gpsStatus == SystemStatus.connected
                  ? 'Disponible'
                  : gpsStatus == SystemStatus.warning
                  ? 'Sin señal'
                  : gpsStatus.label}',
        ),
        SystemStatusBadge(
          status: serverStatus,
          label:
              'Servidor · ${serverStatus == SystemStatus.connected
                  ? 'Disponible'
                  : serverStatus == SystemStatus.warning
                  ? 'Sin conexión'
                  : serverStatus.label}',
        ),
        SystemStatusBadge(
          status: health.status,
          label: 'Telemetría · ${health.label}',
        ),
      ],
    );
  }
}

/// Only telemetry consumers rebuild on packets; the trip controls remain stable.
class DeviceStatusPanel extends ConsumerWidget {
  const DeviceStatusPanel({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final data = ref.watch(deviceTelemetryProvider);
    return TimeLabel(
      builder: (now) => ZentryxCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Estado del sistema',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 14),
            DeviceChecks(telemetry: data, now: now),
            const SizedBox(height: 16),
            DriverDetailRow(
              label: 'Última telemetría',
              value: updatedAgo(data.lastPacketAt, now),
            ),
            const SizedBox(height: 10),
            DriverDetailRow(
              label: 'Precisión GPS',
              value: data.validAccuracy
                  ? '± ${data.accuracyMeters!.toStringAsFixed(0)} m'
                  : 'Sin datos',
            ),
          ],
        ),
      ),
    );
  }
}

class DriverDetailRow extends StatelessWidget {
  const DriverDetailRow({required this.label, required this.value, super.key});
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
        style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
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
          const SizedBox(width: 14),
          Flexible(
            child: Align(alignment: Alignment.centerRight, child: detail),
          ),
        ],
      );
    },
  );
}
