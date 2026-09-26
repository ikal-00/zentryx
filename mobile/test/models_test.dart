import 'package:flutter_test/flutter_test.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';

void main() {
  test('parses vehicle navigation from API v1', () {
    final vehicle = VehicleInfo.fromJson({
      'vehicle_id': 'unit-demo-01',
      'route_id': 'route-l2',
      'status': 'online',
      'position': {'lat': 19.62211, 'lon': -99.16299},
      'speed_mps': 8.3,
      'heading_deg': 124.5,
      'occupancy_level': 'unknown',
      'last_update': '2026-09-25T20:31:22Z',
      'navigation': {
        'direction': 'forward',
        'direction_label': 'La Quebrada → Las Américas',
        'next_station': {
          'station_id': 'node/4332377599',
          'name': 'Bandera Tultitlán',
        },
        'distance_remaining_m': 184.6,
        'eta_seconds': 24.4,
      },
    });

    expect(vehicle.vehicleId, 'unit-demo-01');
    expect(vehicle.position?.lat, closeTo(19.62211, 0.000001));
    expect(vehicle.nextStationName, 'Bandera Tultitlán');
    expect(vehicle.etaSeconds, closeTo(24.4, 0.01));
    expect(vehicle.isOnline, isTrue);
  });

  test('route path remains ordered', () {
    final route = RouteInfo.fromJson({
      'route_id': 'route-l2',
      'service_id': 'l2-ordinary',
      'path': [
        {'lat': 19.1, 'lon': -99.1},
        {'lat': 19.2, 'lon': -99.2},
      ],
    });

    expect(route.path, hasLength(2));
    expect(route.path.first.lat, 19.1);
    expect(route.path.last.lon, -99.2);
  });
}
