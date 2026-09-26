import 'package:dio/dio.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';

class ZentryxApiException implements Exception {
  const ZentryxApiException(this.message, {this.statusCode, this.code});

  final String message;
  final int? statusCode;
  final String? code;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient(String baseUrl)
      : _dio = Dio(
          BaseOptions(
            baseUrl: baseUrl.replaceFirst(RegExp(r'/+$'), ''),
            connectTimeout: const Duration(seconds: 4),
            receiveTimeout: const Duration(seconds: 4),
            sendTimeout: const Duration(seconds: 4),
            headers: const {'Accept': 'application/json'},
          ),
        );

  final Dio _dio;

  Future<RouteInfo> fetchRoute(String routeId) => _guard(() async {
        final response =
            await _dio.get<Map<String, dynamic>>('/v1/routes/$routeId');
        return RouteInfo.fromJson(_requireMap(response.data));
      });

  Future<List<StationInfo>> fetchStations(String routeId) => _guard(() async {
        final response = await _dio.get<Map<String, dynamic>>(
          '/v1/routes/$routeId/stations',
        );
        final data = _requireMap(response.data);
        return (data['stations'] as List<dynamic>? ?? const [])
            .whereType<Map<String, dynamic>>()
            .map(StationInfo.fromJson)
            .toList(growable: false);
      });

  Future<VehicleInfo> fetchVehicle(String vehicleId) => _guard(() async {
        final response =
            await _dio.get<Map<String, dynamic>>('/v1/vehicles/$vehicleId');
        return VehicleInfo.fromJson(_requireMap(response.data));
      });

  Future<List<AlertInfo>> fetchAlerts({String? routeId, String? vehicleId}) =>
      _guard(() async {
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
      });

  Future<void> checkHealth() => _guard(() async {
        final response = await _dio.get<Map<String, dynamic>>('/v1/health');
        final data = _requireMap(response.data);
        if (data['status'] != 'ok') {
          throw const ZentryxApiException('El servidor respondió sin estar saludable.');
        }
      });

  Future<T> _guard<T>(Future<T> Function() request) async {
    try {
      return await request();
    } on ZentryxApiException {
      rethrow;
    } on DioException catch (error) {
      final type = error.type;
      if (type == DioExceptionType.connectionTimeout ||
          type == DioExceptionType.sendTimeout ||
          type == DioExceptionType.receiveTimeout ||
          type == DioExceptionType.connectionError) {
        throw const ZentryxApiException(
          'No se pudo conectar con Zentryx. Revisa Tailscale y el servidor.',
        );
      }

      final statusCode = error.response?.statusCode;
      final data = error.response?.data;
      String? apiCode;
      if (data is Map) {
        apiCode = data['error']?.toString();
      }

      if (statusCode == 404) {
        throw ZentryxApiException(
          'El recurso solicitado no está disponible.',
          statusCode: statusCode,
          code: apiCode,
        );
      }
      if (statusCode == 503) {
        throw ZentryxApiException(
          'Zentryx está iniciando o la base de datos no está disponible.',
          statusCode: statusCode,
          code: apiCode,
        );
      }

      throw ZentryxApiException(
        'No se pudo completar la solicitud al servidor.',
        statusCode: statusCode,
        code: apiCode,
      );
    }
  }

  Map<String, dynamic> _requireMap(Map<String, dynamic>? data) {
    if (data == null) {
      throw const FormatException('Empty JSON response');
    }
    return data;
  }
}
