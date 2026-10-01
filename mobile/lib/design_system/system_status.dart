import 'package:flutter/cupertino.dart';

import 'zentryx_layout.dart';
import 'zentryx_theme.dart';

enum SystemStatus {
  connected,
  disconnected,
  syncing,
  error,
  stale,
  warning,
  noData,
}

extension SystemStatusStyle on SystemStatus {
  String get label => switch (this) {
    SystemStatus.connected => 'Conectado',
    SystemStatus.disconnected => 'Sin conexión',
    SystemStatus.syncing => 'Actualizando',
    SystemStatus.error => 'Error',
    SystemStatus.stale => 'Datos antiguos',
    SystemStatus.warning => 'Advertencia',
    SystemStatus.noData => 'Sin datos',
  };
  Color get color => switch (this) {
    SystemStatus.connected => ZentryxColors.success,
    SystemStatus.syncing => ZentryxColors.info,
    SystemStatus.error => ZentryxColors.danger,
    SystemStatus.stale || SystemStatus.warning => ZentryxColors.warning,
    SystemStatus.noData => ZentryxColors.muted,
    SystemStatus.disconnected => ZentryxColors.muted,
  };
  IconData get icon => switch (this) {
    SystemStatus.connected => CupertinoIcons.checkmark_circle_fill,
    SystemStatus.disconnected => CupertinoIcons.wifi_slash,
    SystemStatus.syncing => CupertinoIcons.arrow_2_circlepath,
    SystemStatus.error => CupertinoIcons.exclamationmark_circle_fill,
    SystemStatus.stale => CupertinoIcons.clock_fill,
    SystemStatus.warning => CupertinoIcons.exclamationmark_triangle_fill,
    SystemStatus.noData => CupertinoIcons.minus_circle,
  };
}

class SystemStatusBadge extends StatelessWidget {
  const SystemStatusBadge({required this.status, this.label, super.key});
  final SystemStatus status;
  final String? label;

  @override
  Widget build(BuildContext context) {
    final color = CupertinoDynamicColor.resolve(status.color, context);
    return Semantics(
      label: label ?? status.label,
      child: ExcludeSemantics(
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.09),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(status.icon, size: 13, color: color),
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  label ?? status.label,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: color,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class SystemStatusCard extends StatelessWidget {
  const SystemStatusCard({
    required this.status,
    required this.title,
    required this.message,
    super.key,
  });
  final SystemStatus status;
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) => ZentryxCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SystemStatusBadge(status: status, label: title),
        const SizedBox(height: 10),
        Text(
          message,
          style: TextStyle(
            fontSize: 13,
            height: 1.4,
            color: CupertinoDynamicColor.resolve(ZentryxColors.muted, context),
          ),
        ),
      ],
    ),
  );
}
