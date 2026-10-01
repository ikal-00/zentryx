import 'dart:async';
import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/driver_session_store.dart';
import '../domain/device_telemetry.dart';

enum IncidentType {
  traffic('Tráfico'),
  accident('Accidente'),
  stopped('Unidad detenida'),
  closedStation('Estación cerrada'),
  other('Otro');

  const IncidentType(this.label);
  final String label;
}

class DriverSession {
  const DriverSession({
    this.startedAt,
    this.unit,
    this.lastIncident,
    this.reportedAt,
    this.reportCount = 0,
    this.restored = false,
    this.busy = false,
    this.storageError,
  });
  final DateTime? startedAt;
  final DriverUnit? unit;
  final IncidentType? lastIncident;
  final DateTime? reportedAt;
  final int reportCount;
  final bool restored;
  final bool busy;
  final String? storageError;
  bool get active => startedAt != null;
  bool get canEdit => restored && !busy;
  DriverSession status({
    required bool restored,
    bool busy = false,
    String? error,
  }) => DriverSession(
    startedAt: startedAt,
    unit: unit,
    lastIncident: lastIncident,
    reportedAt: reportedAt,
    reportCount: reportCount,
    restored: restored,
    busy: busy,
    storageError: error,
  );

  String encode() => jsonEncode({
    'version': 1,
    'startedAt': startedAt?.toUtc().toIso8601String(),
    'unit': unit?.toJson(),
    'lastIncident': lastIncident?.name,
    'reportedAt': reportedAt?.toUtc().toIso8601String(),
    'reportCount': reportCount,
  });

  factory DriverSession.decode(String raw) {
    final json = jsonDecode(raw);
    if (json is! Map<String, dynamic> || json['version'] != 1) {
      throw const FormatException('Unsupported session');
    }
    DateTime? stamp(String key) {
      if (json[key] == null) return null;
      final parsed = json[key] is String
          ? DateTime.tryParse(json[key] as String)
          : null;
      if (parsed == null ||
          parsed.isAfter(DateTime.now().add(const Duration(minutes: 2)))) {
        throw const FormatException('Invalid timestamp');
      }
      return parsed.toUtc();
    }

    final started = stamp('startedAt');
    final unit = json['unit'] == null
        ? null
        : DriverUnit.fromJson(Map<String, dynamic>.from(json['unit'] as Map));
    if (started != null && unit == null) {
      throw const FormatException('Active trip without unit');
    }
    final incident = json['lastIncident'] == null
        ? null
        : IncidentType.values.byName(json['lastIncident'] as String);
    final reported = stamp('reportedAt');
    if ((incident == null) != (reported == null)) {
      throw const FormatException('Invalid report');
    }
    final count = json['reportCount'];
    if (count is! int || count < 0) {
      throw const FormatException('Invalid count');
    }
    return DriverSession(
      startedAt: started,
      unit: unit,
      lastIncident: incident,
      reportedAt: reported,
      reportCount: count,
      restored: true,
    );
  }
}

final driverSessionProvider =
    StateNotifierProvider<DriverSessionController, DriverSession>(
      (ref) => DriverSessionController(ref.watch(driverSessionStoreProvider)),
    );

/// Serializes writes, restores before commands, and only confirms saved changes.
class DriverSessionController extends StateNotifier<DriverSession> {
  DriverSessionController(this._store) : super(const DriverSession()) {
    ready = _restore();
  }
  final DriverSessionStore _store;
  late Future<void> ready;
  Future<void> _queue = Future<void>.value();

  Future<void> _restore() async {
    try {
      final raw = await _store.read();
      final restored = raw == null
          ? const DriverSession(restored: true)
          : DriverSession.decode(raw);
      if (mounted) state = restored;
    } catch (_) {
      if (mounted) {
        state = state.status(
          restored: false,
          error: 'No se pudo recuperar la sesión guardada. Reintenta antes de iniciar.',
        );
      }
    }
  }

  Future<void> retryRestore() {
    if (state.restored) return Future<void>.value();
    ready = _restore();
    return ready;
  }

  Future<bool> _save(DriverSession Function(DriverSession) change) {
    final result = Completer<bool>();
    _queue = _queue.then((_) async {
      await ready;
      if (!mounted || !state.restored) {
        result.complete(false);
        return;
      }
      final previous = state;
      final next = change(previous);
      state = previous.status(restored: true, busy: true);
      try {
        await _store.write(next.encode());
        if (mounted) state = next.status(restored: true);
        result.complete(true);
      } catch (_) {
        if (mounted) {
          state = previous.status(
            restored: true,
            error: 'No se pudo guardar el cambio. El estado anterior se conserva; vuelve a intentarlo.',
          );
        }
        result.complete(false);
      }
    });
    return result.future;
  }

  Future<bool> start(DriverUnit unit) => _save(
    (current) => current.active
        ? current
        : DriverSession(
            startedAt: DateTime.now().toUtc(),
            unit: unit,
            lastIncident: current.lastIncident,
            reportedAt: current.reportedAt,
            reportCount: current.reportCount,
            restored: true,
          ),
  );
  Future<bool> stop() => _save(
    (current) => DriverSession(
      unit: current.unit,
      lastIncident: current.lastIncident,
      reportedAt: current.reportedAt,
      reportCount: current.reportCount,
      restored: true,
    ),
  );
  Future<bool> report(IncidentType incident) => _save(
    (current) => DriverSession(
      startedAt: current.startedAt,
      unit: current.unit,
      lastIncident: incident,
      reportedAt: DateTime.now().toUtc(),
      reportCount: current.reportCount + 1,
      restored: true,
    ),
  );
}
