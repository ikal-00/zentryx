class AppConfig {
  const AppConfig._();

  static const apiBaseUrl = String.fromEnvironment(
    'ZENTRYX_API_BASE_URL',
    defaultValue: 'http://localhost:5050',
  );

  static const routeId = String.fromEnvironment(
    'ZENTRYX_ROUTE_ID',
    defaultValue: 'route-l2',
  );

  static const vehicleId = String.fromEnvironment(
    'ZENTRYX_VEHICLE_ID',
    defaultValue: 'unit-demo-01',
  );

  static const pollInterval = Duration(seconds: 2);
}
