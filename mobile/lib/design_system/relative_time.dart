import 'dart:async';

import 'package:flutter/cupertino.dart';

String updatedAgo(DateTime? timestamp, DateTime now) {
  if (timestamp == null) return 'Sin actualización';
  final age = now.difference(timestamp);
  if (age.isNegative || age.inSeconds < 1) return 'Actualizado ahora';
  if (age.inSeconds < 60) return 'Actualizado hace ${age.inSeconds} s';
  if (age.inMinutes < 60) return 'Actualizado hace ${age.inMinutes} min';
  if (age.inHours < 24) return 'Actualizado hace ${age.inHours} h';
  return 'Actualizado hace ${age.inDays} d';
}

/// Only its small subtree ticks. No map/provider rebuilds, no background timer.
class TimeLabel extends StatefulWidget {
  const TimeLabel({required this.builder, super.key});
  final Widget Function(DateTime now) builder;
  @override
  State<TimeLabel> createState() => _TimeLabelState();
}

class _TimeLabelState extends State<TimeLabel> with WidgetsBindingObserver {
  Timer? _timer;
  bool _foreground = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _schedule();
  }

  void _schedule() {
    _timer?.cancel();
    if (_foreground && TickerMode.valuesOf(context).enabled) {
      _timer = Timer.periodic(const Duration(seconds: 1), (_) {
        if (mounted) setState(() {});
      });
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _foreground = state == AppLifecycleState.resumed;
    _schedule();
    if (_foreground && mounted) setState(() {});
  }

  @override
  void dispose() {
    _timer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.builder(DateTime.now());
}
