import 'package:flutter_test/flutter_test.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';

void main() {
  test('parses complete vehicle navigation from API v1', () {
    final vehicle = VehicleInfo.fromJson({
      'vehicle_id': 'unit-demo-01',
      'route_id': 'route-l2',
      'status': 'online',
      'position': {'lat': 19.62211, 'lon': -99.16299},
      'speed_mps': 8.3,
      'accuracy_m': 4.7,
      'heading_deg': 124.5,
      'occupancy_level': 'medium',
      'last_update': '2026-09-25T20:31:22Z',
      'navigation': {
        'direction': 'forward',
        'direction_source': 'history',
        'direction_label': 'La Quebrada → Las Américas',
        'progress_m': 3250.2,
        'route_length_m': 22193.9,
        'next_station': {
          'station_id': 'node/4332377599',
          'name': 'Bandera Tultitlán',
        },
        'distance_remaining_m': 184.6,
        'eta_seconds': 24.4,
        'eta_speed_mps': 7.57,
      },
    });

    expect(vehicle.vehicleId, 'unit-demo-01');
    expect(vehicle.position?.lat, closeTo(19.62211, 0.000001));
    expect(vehicle.accuracyM, closeTo(4.7, 0.01));
    expect(vehicle.nextStationName, 'Bandera Tultitlán');
    expect(vehicle.directionSource, 'history');
    expect(vehicle.etaSeconds, closeTo(24.4, 0.01));
    expect(vehicle.etaSpeedMps, closeTo(7.57, 0.01));
    expect(vehicle.routeProgress, closeTo(3250.2 / 22193.9, 0.0001));
    expect(vehicle.isOnline, isTrue);
  });

  test('route progress is clamped and unavailable without a valid length', () {
    final complete = VehicleInfo.fromJson({
      'navigation': {'progress_m': 120, 'route_length_m': 100},
    });
    final incomplete = VehicleInfo.fromJson({
      'navigation': {'progress_m': 20, 'route_length_m': 0},
    });

    expect(complete.routeProgress, 1.0);
    expect(incomplete.routeProgress, isNull);
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
