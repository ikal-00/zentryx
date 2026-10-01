import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// One versioned document; no GPS positions, credentials or personal data.
abstract interface class DriverSessionStore {
  Future<String?> read();
  Future<void> write(String value);
}

final driverSessionStoreProvider = Provider<DriverSessionStore>(
  (ref) => PreferencesDriverSessionStore(),
);

class PreferencesDriverSessionStore implements DriverSessionStore {
  PreferencesDriverSessionStore({SharedPreferencesAsync? preferences})
    : _preferences = preferences ?? SharedPreferencesAsync();
  final SharedPreferencesAsync _preferences;
  static const key = 'zentryx.driver.session.v1';
  @override
  Future<String?> read() => _preferences.getString(key);
  @override
  Future<void> write(String value) => _preferences.setString(key, value);
}
