import 'package:dio/dio.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';

class ApiClient {
  ApiClient(String baseUrl)
      : _dio = Dio(
          BaseOptions(
            baseUrl: baseUrl.replaceFirst(RegExp(r'/+$'), ''),
            connectTimeout: const Duration(seconds: 4),
            receiveTimeout: const Duration(seconds: 4),
            headers: const {'Accept': 'application/json'},
          ),
        );

  final Dio _dio;

  Future<RouteInfo> fetchRoute(String routeId) async {
    final response = await _dio.get<Map<String, dynamic>>('/v1/routes/$routeId');
    return RouteInfo.fromJson(_requireMap(response.data));
  }

  Future<List<StationInfo>> fetchStations(String routeId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/v1/routes/$routeId/stations',
    );
    final data = _requireMap(response.data);
    return (data['stations'] as List<dynamic>? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(StationInfo.fromJson)
        .toList(growable: false);
  }

  Future<VehicleInfo> fetchVehicle(String vehicleId) async {
    final response = await _dio.get<Map<String, dynamic>>('/v1/vehicles/$vehicleId');
    return VehicleInfo.fromJson(_requireMap(response.data));
  }

  Future<List<AlertInfo>> fetchAlerts({String? routeId, String? vehicleId}) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/v1/alerts',
      queryParameters: {
        if (routeId != null) 'route_id': routeId,
        if (vehicleId != null) 'vehicle_id': vehicleId,
      },
    );
    final data = _requireMap(response.data);
    return (data['alerts'] as List<dynamic>? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(AlertInfo.fromJson)
        .toList(growable: false);
  }

  Map<String, dynamic> _requireMap(Map<String, dynamic>? data) {
    if (data == null) {
      throw const FormatException('Empty JSON response');
    }
    return data;
  }
}
