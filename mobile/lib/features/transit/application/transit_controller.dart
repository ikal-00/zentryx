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

  Future<void> start() async {
    try {
      final routeFuture = _repository.loadRoute();
      final stationsFuture = _repository.loadStations();
      final route = await routeFuture;
      final stations = await stationsFuture;
      if (_closed) return;
      state = state.copyWith(
        route: route,
        stations: stations,
        loading: false,
        clearError: true,
      );
    } catch (error) {
      if (_closed) return;
      state = state.copyWith(
        loading: false,
        stale: true,
        error: _message(error),
      );
    }

    await refresh();
    if (_closed) return;
    _poller = Timer.periodic(AppConfig.pollInterval, (_) => unawaited(refresh()));
  }

  Future<void> refresh() async {
    if (_refreshInFlight || _closed) return;
    _refreshInFlight = true;
    state = state.copyWith(refreshing: true);

    try {
      final vehicleFuture = _repository.loadVehicle();
      final alertsFuture = _repository.loadAlerts();
      final vehicle = await vehicleFuture;
      final alerts = await alertsFuture;
      if (_closed) return;
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
