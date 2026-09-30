import 'package:flutter/cupertino.dart';
import 'package:zentryx_mobile/design_system/relative_time.dart';
import 'package:zentryx_mobile/design_system/system_status.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';

/// Presentation-only interpretation. Never changes polling, ETA or motion.
SystemStatus transitSystemStatus(TransitState state, DateTime now) {
  if (state.vehicle != null && !state.vehicle!.isOnline) {
    return SystemStatus.disconnected;
  }
  if (state.error != null && state.vehicle == null) return SystemStatus.error;
  if (state.stale || state.error != null) {
    return state.vehicle == null
        ? SystemStatus.disconnected
        : SystemStatus.stale;
  }
  if (state.loading || state.refreshing) return SystemStatus.syncing;
  final timestamp = state.vehicle?.lastUpdate ?? state.lastSuccess;
  if (timestamp != null &&
      now.difference(timestamp) > const Duration(seconds: 30)) {
    return SystemStatus.stale;
  }
  return state.vehicle == null
      ? SystemStatus.disconnected
      : SystemStatus.connected;
}

class LiveStatusIndicator extends StatelessWidget {
  const LiveStatusIndicator({required this.state, super.key});
  final TransitState state;

  @override
  Widget build(BuildContext context) => TimeLabel(
    builder: (now) {
      final status = transitSystemStatus(state, now);
      final timestamp = state.vehicle?.lastUpdate ?? state.lastSuccess;
      return Wrap(
        spacing: 8,
        runSpacing: 6,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          SystemStatusBadge(
            status: status,
            label: status == SystemStatus.connected ? 'En vivo' : null,
          ),
          Text(
            updatedAgo(timestamp, now),
            style: TextStyle(
              fontSize: 11,
              color: CupertinoDynamicColor.resolve(
                ZentryxColors.muted,
                context,
              ),
            ),
          ),
        ],
      );
    },
  );
}
