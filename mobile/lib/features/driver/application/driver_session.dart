import 'package:flutter_riverpod/flutter_riverpod.dart';

enum IncidentType {
  traffic('Tráfico'),
  accident('Accidente'),
  stopped('Unidad detenida'),
  closedStation('Estación cerrada'),
  other('Otro');

  const IncidentType(this.label);
  final String label;
}

/// In-memory prototype only. Never sends telemetry or passenger alerts.
class DriverSession {
  const DriverSession({
    this.startedAt,
    this.lastIncident,
    this.reportedAt,
    this.reportCount = 0,
  });
  final DateTime? startedAt;
  final IncidentType? lastIncident;
  final DateTime? reportedAt;
  final int reportCount;
  bool get active => startedAt != null;
}

final driverSessionProvider =
    StateNotifierProvider<DriverSessionController, DriverSession>(
      (ref) => DriverSessionController(),
    );

class DriverSessionController extends StateNotifier<DriverSession> {
  DriverSessionController() : super(const DriverSession());

  void start() {
    if (state.active) return;
    state = DriverSession(
      startedAt: DateTime.now(),
      lastIncident: state.lastIncident,
      reportedAt: state.reportedAt,
      reportCount: state.reportCount,
    );
  }

  void stop() => state = DriverSession(
    lastIncident: state.lastIncident,
    reportedAt: state.reportedAt,
    reportCount: state.reportCount,
  );

  void report(IncidentType incident) => state = DriverSession(
    startedAt: state.startedAt,
    lastIncident: incident,
    reportedAt: DateTime.now(),
    reportCount: state.reportCount + 1,
  );
}
