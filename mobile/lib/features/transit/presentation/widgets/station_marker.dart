import 'package:flutter/cupertino.dart';

class StationMarker extends StatelessWidget {
  const StationMarker({required this.name, required this.isNext,
    required this.selected, required this.onTap, super.key});
  final String name;
  final bool isNext;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final prominent = selected || isNext;
    return Semantics(
      button: true,
      selected: selected,
      label: '$name${isNext ? ', próxima estación' : ''}',
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onTap,
        child: Center(
          child: Container(
            width: prominent ? 30 : 19,
            height: prominent ? 30 : 19,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: selected ? const Color(0xFF153C34) : const Color(0xFFFFFFFF),
              border: Border.all(color: const Color(0xFF153C34), width: 3),
              boxShadow: [
                BoxShadow(
                  color: prominent ? const Color(0x99D6F67A) : const Color(0xBBFFFFFF),
                  spreadRadius: prominent ? 5 : 2,
                  blurRadius: prominent ? 2 : 0,
                ),
                const BoxShadow(color: Color(0x33000000), blurRadius: 4, offset: Offset(0, 2)),
              ],
            ),
            child: prominent
                ? Icon(selected ? CupertinoIcons.checkmark : CupertinoIcons.arrow_down,
                    size: 16, color: selected ? const Color(0xFFD6F67A) : const Color(0xFF153C34))
                : null,
          ),
        ),
      ),
    );
  }
}
