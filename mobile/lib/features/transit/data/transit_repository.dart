import 'package:zentryx_mobile/core/config/app_config.dart';
import 'package:zentryx_mobile/core/network/api_client.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';

class TransitRepository {
  TransitRepository(this._api);

  final ApiClient _api;

  RouteInfo? _routeCache;
  List<StationInfo>? _stationsCache;

  Future<RouteInfo> loadRoute({bool force = false}) async {
    if (!force && _routeCache != null) return _routeCache!;
    final route = await _api.fetchRoute(AppConfig.routeId);
    _routeCache = route;
    return route;
  }

  Future<List<StationInfo>> loadStations({bool force = false}) async {
    if (!force && _stationsCache != null) return _stationsCache!;
    final stations = await _api.fetchStations(AppConfig.routeId);
    _stationsCache = stations;
    return stations;
  }

  Future<VehicleInfo> loadVehicle() => _api.fetchVehicle(AppConfig.vehicleId);

  Future<List<AlertInfo>> loadAlerts() => _api.fetchAlerts(
        routeId: AppConfig.routeId,
        vehicleId: AppConfig.vehicleId,
      );

  Future<void> checkHealth() => _api.checkHealth();

  void clearStaticCache() {
    _routeCache = null;
    _stationsCache = null;
  }
}
