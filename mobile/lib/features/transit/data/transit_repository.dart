import 'package:zentryx_mobile/core/config/app_config.dart';
import 'package:zentryx_mobile/core/network/api_client.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';

class TransitRepository {
  TransitRepository(this._api);

  final ApiClient _api;

  Future<RouteInfo> loadRoute() => _api.fetchRoute(AppConfig.routeId);

  Future<List<StationInfo>> loadStations() => _api.fetchStations(AppConfig.routeId);

  Future<VehicleInfo> loadVehicle() => _api.fetchVehicle(AppConfig.vehicleId);

  Future<List<AlertInfo>> loadAlerts() => _api.fetchAlerts(
        routeId: AppConfig.routeId,
        vehicleId: AppConfig.vehicleId,
      );
}
