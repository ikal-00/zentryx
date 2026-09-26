import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:zentryx_mobile/core/config/app_config.dart';
import 'package:zentryx_mobile/core/network/api_client.dart';
import 'package:zentryx_mobile/features/transit/data/transit_repository.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';

class TransitState {
  const TransitState({
    this.route,
    this.stations = const [],
    this.vehicle,
    this.alerts = const [],
    this.loading = true,
    this.refreshing = false,
    this.stale = false,
    this.lastSuccess,
    this.error,
  });

  final RouteInfo? route;
  final List<StationInfo> stations;
  final VehicleInfo? vehicle;
  final List<AlertInfo> alerts;
  final bool loading;
  final bool refreshing;
  final bool stale;
  final DateTime? lastSuccess;
  final String? error;

  TransitState copyWith({
    RouteInfo? route,
    List<StationInfo>? stations,
    VehicleInfo? vehicle,
    List<AlertInfo>? alerts,
    bool? loading,
    bool? refreshing,
    bool? stale,
    DateTime? lastSuccess,
    String? error,
    bool clearError = false,
  }) {
    return TransitState(
      route: route ?? this.route,
      stations: stations ?? this.stations,
      vehicle: vehicle ?? this.vehicle,
      alerts: alerts ?? this.alerts,
      loading: loading ?? this.loading,
      refreshing: refreshing ?? this.refreshing,
      stale: stale ?? this.stale,
      lastSuccess: lastSuccess ?? this.lastSuccess,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

final apiClientProvider = Provider<ApiClient>(
  (ref) => ApiClient(AppConfig.apiBaseUrl),
);

final transitRepositoryProvider = Provider<TransitRepository>(
  (ref) => TransitRepository(ref.watch(apiClientProvider)),
);

final transitControllerProvider =
    StateNotifierProvider<TransitController, TransitState>((ref) {
  final controller = TransitController(ref.watch(transitRepositoryProvider));
  unawaited(controller.start());
  return controller;
});

class TransitController extends StateNotifier<TransitState> {
  TransitController(this._repository) : super(const TransitState());

  final TransitRepository _repository;
  Timer? _poller;
  bool _refreshInFlight = false;
  bool _closed = false;
  bool _paused = false;

  Future<void> start() async {
    await _ensureStaticData();
    if (_closed) return;
    await refresh();
    if (_closed || _paused) return;
    _schedulePoller();
  }

  Future<void> refresh() async {
    if (_refreshInFlight || _closed || _paused) return;
    _refreshInFlight = true;
    state = state.copyWith(refreshing: true);

    try {
      if (state.route == null || state.stations.isEmpty) {
        await _ensureStaticData();
      }

      final results = await Future.wait<Object>([
        _repository.loadVehicle(),
        _repository.loadAlerts(),
      ]);
      if (_closed) return;

      final vehicle = results[0] as VehicleInfo;
      final alerts = results[1] as List<AlertInfo>;
      state = state.copyWith(
        vehicle: vehicle,
        alerts: alerts,
        loading: false,
        refreshing: false,
        stale: false,
        lastSuccess: DateTime.now(),
        clearError: true,
      );
    } catch (error) {
      if (_closed) return;
      state = state.copyWith(
        loading: false,
        refreshing: false,
        stale: true,
        error: _message(error),
      );
    } finally {
      _refreshInFlight = false;
    }
  }

  void pause() {
    if (_closed || _paused) return;
    _paused = true;
    _poller?.cancel();
    _poller = null;
  }

  Future<void> resume() async {
    if (_closed) return;
    final wasPaused = _paused;
    _paused = false;
    if (wasPaused) {
      await refresh();
    }
    if (!_closed) _schedulePoller();
  }

  Future<void> reloadStaticData() async {
    _repository.clearStaticCache();
    await _ensureStaticData(force: true);
    await refresh();
  }

  Future<void> _ensureStaticData({bool force = false}) async {
    RouteInfo? route = state.route;
    List<StationInfo> stations = state.stations;
    Object? lastError;

    if (route == null || force) {
      try {
        route = await _repository.loadRoute(force: force);
      } catch (error) {
        lastError = error;
      }
    }

    if (stations.isEmpty || force) {
      try {
        stations = await _repository.loadStations(force: force);
      } catch (error) {
        lastError ??= error;
      }
    }

    if (_closed) return;
    state = state.copyWith(
      route: route,
      stations: stations,
      loading: false,
      error: lastError == null ? null : _message(lastError),
      clearError: lastError == null,
    );
  }

  void _schedulePoller() {
    if (_closed || _paused) return;
    _poller?.cancel();
    _poller = Timer.periodic(
      AppConfig.pollInterval,
      (_) => unawaited(refresh()),
    );
  }

  String _message(Object error) {
    final text = error.toString();
    if (text.length <= 140) return text;
    return '${text.substring(0, 137)}...';
  }

  @override
  void dispose() {
    _closed = true;
    _poller?.cancel();
    super.dispose();
  }
}
