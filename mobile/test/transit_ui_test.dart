import 'dart:convert';
import 'dart:io';
import 'dart:ui' as ui;

import 'package:flutter/cupertino.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:zentryx_mobile/core/network/api_client.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/transit/application/transit_controller.dart';
import 'package:zentryx_mobile/features/transit/data/transit_repository.dart';
import 'package:zentryx_mobile/features/transit/domain/models.dart';
import 'package:zentryx_mobile/features/transit/presentation/home_screen.dart';
import 'package:zentryx_mobile/features/transit/presentation/widgets/station_marker.dart';
import 'package:zentryx_mobile/features/transit/presentation/widgets/transit_hud.dart';

const station = StationInfo(stationId: 'bandera', name: 'Bandera Tultitlán',
    position: GeoPoint(19.62211, -99.16299), order: 2);
const other = StationInfo(stationId: 'other', name: 'Otra estación',
    position: GeoPoint(19.624, -99.16299), order: 3);
final vehicle = VehicleInfo.fromJson({
  'vehicle_id': 'unit-demo-01', 'status': 'online', 'heading_deg': 350,
  'position': {'lat': 19.6215, 'lon': -99.16299}, 'occupancy_level': 'medium',
  'navigation': {'next_station': {'station_id': 'bandera', 'name': station.name},
    'direction_label': 'La Quebrada → Las Américas', 'eta_seconds': 120},
});
final fixtureState = TransitState(route: RouteInfo.fromJson({
  'route_id': 'route-l2', 'service_id': 'l2-ordinary',
  'network_name': 'Mexibús', 'line_label': 'L2',
  'path': [
    {'lat': 19.617, 'lon': -99.16299},
    {'lat': 19.624, 'lon': -99.16299},
    {'lat': 19.626, 'lon': -99.161},
  ],
}), loading: false, vehicle: vehicle, stations: const [station, other],
    alerts: const [AlertInfo(alertId: 'a', message: 'Tráfico lento en el recorrido', severity: 'warning', type: 'traffic')]);

class _Controller extends TransitController {
  _Controller() : super(TransitRepository(ApiClient('http://localhost'))) {
    state = fixtureState;
  }
}

class _Tiles extends TileProvider {
  @override
  ImageProvider getImage(TileCoordinates coordinates, TileLayer options) => MemoryImage(
    base64Decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGN4/f75fwAJSwPBpz51PgAAAABJRU5ErkJggg=='));
}

void main() {
  setUpAll(() async {
    final root = Platform.environment['FLUTTER_ROOT'];
    if (root != null) {
      final font = File('$root/bin/cache/artifacts/material_fonts/Roboto-Regular.ttf');
      if (font.existsSync()) {
        final loader = FontLoader('ReviewFont')..addFont(Future.value(ByteData.sublistView(font.readAsBytesSync())));
        await loader.load();
        final icons = FontLoader('packages/cupertino_icons/CupertinoIcons')
          ..addFont(rootBundle.load('packages/cupertino_icons/assets/CupertinoIcons.ttf'));
        await icons.load();
      }
    }
  });

  test('station identity is preferred to duplicate names', () {
    expect(vehicle.isNextStation(station), isTrue);
    expect(vehicle.isNextStation(StationInfo(stationId: 'different', name: station.name,
        position: station.position, order: 4)), isFalse);
    expect(etaLabel(double.nan), '—');
  });

  for (final width in [360.0, 390.0, 430.0]) {
    for (final scale in [1.0, 1.6]) {
      testWidgets('HUD and station panel fit width $width text scale $scale', (tester) async {
        tester.view.physicalSize = Size(width, 844);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        await tester.pumpWidget(CupertinoApp(debugShowCheckedModeBanner: false, theme: zentryxTheme,
          home: MediaQuery(data: MediaQueryData(size: Size(width, 844), textScaler: TextScaler.linear(scale)),
            child: CupertinoPageScaffold(child: Align(alignment: Alignment.bottomCenter,
              child: Padding(padding: const EdgeInsets.all(14),
                child: TransitStatusCard(state: fixtureState, onRefresh: () {})))))));
        await tester.pump();
        expect(tester.takeException(), isNull);
        expect(find.text('2 min'), findsOneWidget);
        await tester.tap(find.textContaining('1 alerta(s)'));
        await tester.pumpAndSettle();
        expect(find.text('Alertas del servicio'), findsOneWidget);
        expect(find.textContaining('Aviso · Tráfico'), findsOneWidget);
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(CupertinoApp(home: StationStatusCard(station: other,
            state: fixtureState, onCenter: () {}, onClose: () {})));
        expect(find.text('Llegadas a esta estación aún no disponibles.'), findsOneWidget);
        expect(find.text('2 min'), findsNothing);
      });
    }
  }

  testWidgets('stale telemetry never presents a live ETA', (tester) async {
    await tester.pumpWidget(CupertinoApp(home: TransitStatusCard(
        state: fixtureState.copyWith(stale: true), onRefresh: () {})));
    expect(find.text('2 min'), findsNothing);
    expect(find.text('Últimos datos'), findsOneWidget);
  });

  testWidgets('station selection, switching, close, gestures and follow work on the map', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(ProviderScope(overrides: [
      transitControllerProvider.overrideWith((ref) => _Controller()),
    ], child: CupertinoApp(debugShowCheckedModeBanner: false, theme: zentryxTheme, home: HomeScreen(tileProvider: _Tiles()))));
    await tester.pumpAndSettle();
    expect(find.byType(StationMarker), findsNWidgets(2));
    await tester.tap(find.byWidgetPredicate((w) => w is StationMarker && w.name == station.name));
    await tester.pump();
    expect(find.byType(StationStatusCard), findsOneWidget);
    expect(tester.widget<MapFollowButton>(find.byType(MapFollowButton)).following, isFalse);
    await tester.tap(find.byWidgetPredicate((w) => w is StationMarker && w.name == other.name));
    await tester.pump();
    expect(tester.widget<StationStatusCard>(find.byType(StationStatusCard)).station.stationId, other.stationId);
    await tester.tap(find.byIcon(CupertinoIcons.xmark_circle_fill));
    await tester.pump();
    expect(find.byType(StationStatusCard), findsNothing);
    await tester.tap(find.byType(MapFollowButton));
    await tester.pumpAndSettle();
    expect(tester.widget<MapFollowButton>(find.byType(MapFollowButton)).following, isTrue);
    await tester.dragFrom(const Offset(100, 300), const Offset(80, 30));
    await tester.pumpAndSettle();
    expect(tester.widget<MapFollowButton>(find.byType(MapFollowButton)).following, isFalse);
    expect(tester.takeException(), isNull);
  });

  // Optional CI review artifacts; no generated images are checked into source.
  if (const bool.fromEnvironment('ZENTRYX_CAPTURE_REVIEW')) {
    for (final width in [360.0, 390.0, 430.0]) {
      testWidgets('capture actual Flutter UI at $width', (tester) async {
        tester.view.physicalSize = Size(width, 844);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        final key = GlobalKey();
        await tester.pumpWidget(ProviderScope(overrides: [
          transitControllerProvider.overrideWith((ref) => _Controller()),
        ], child: CupertinoApp(debugShowCheckedModeBanner: false, theme: zentryxTheme.copyWith(textTheme: const CupertinoTextThemeData(
            textStyle: TextStyle(fontFamily: 'ReviewFont', color: Color(0xFF153C34)),
            actionTextStyle: TextStyle(fontFamily: 'ReviewFont', color: Color(0xFF153C34)))),
          home: MediaQuery(data: MediaQueryData(size: Size(width, 844),
              padding: const EdgeInsets.only(top: 47, bottom: 34)),
              child: RepaintBoundary(key: key, child: HomeScreen(tileProvider: _Tiles()))))));
        await tester.pumpAndSettle();
        await tester.runAsync(() async {
          final image = await (key.currentContext!.findRenderObject() as RenderRepaintBoundary).toImage();
          final bytes = await image.toByteData(format: ui.ImageByteFormat.png);
          final file = File('build/visual-review/mobile-${width.toInt()}.png');
          await file.parent.create(recursive: true);
          await file.writeAsBytes(bytes!.buffer.asUint8List());
          image.dispose();
        });
        expect(tester.takeException(), isNull);
      });
    }
  }
}
