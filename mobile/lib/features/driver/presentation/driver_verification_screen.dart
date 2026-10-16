import 'dart:async';

import 'package:flutter/cupertino.dart';
import 'package:flutter/services.dart';
import 'package:zentryx_mobile/design_system/zentryx_layout.dart';
import 'package:zentryx_mobile/design_system/zentryx_theme.dart';
import 'package:zentryx_mobile/features/driver/domain/driver_session.dart';

class DriverVerificationScreen extends StatefulWidget {
  const DriverVerificationScreen({
    required this.onVerified,
    super.key,
  });

  final ValueChanged<DriverSession> onVerified;

  @override
  State<DriverVerificationScreen> createState() =>
      _DriverVerificationScreenState();
}

class _DriverVerificationScreenState extends State<DriverVerificationScreen> {
  final TextEditingController _folioCtrl = TextEditingController();
  final TextEditingController _plateCtrl = TextEditingController();

  int _step = 1; // 1: Login & QR, 2: INE Capture & Skeleton Verification
  String _authMethod = 'manual';

  // Step 2 INE state
  bool _frontCaptured = false;
  bool _backCaptured = false;
  String _frontSource = '';
  String _backSource = '';
  bool _verifyingIne = false;
  double _verifyProgress = 0;
  String _verifyStatusLabel = 'Analizando biometría y hologramas INE...';

  static final RegExp _folioRegex = RegExp(r'^\d{4,8}$');
  static final RegExp _plateRegex = RegExp(r'^[A-Z]{3}-\d{3,4}[A-Z]?$');

  static const Map<String, String> _officialOperators = {
    '84021': 'Carlos Eduardo Mendoza Rojas',
    '10492': 'Roberto Hernández Villaseñor',
    '55210': 'Miguel Ángel Vargas Gómez',
  };

  @override
  void dispose() {
    _folioCtrl.dispose();
    _plateCtrl.dispose();
    super.dispose();
  }

  String get _normalizedPlate {
    final raw = _plateCtrl.text.trim().toUpperCase().replaceAll(' ', '');
    if (RegExp(r'^[A-Z]{3}\d{3,4}[A-Z]?$').hasMatch(raw)) {
      return '${raw.substring(0, 3)}-${raw.substring(3)}';
    }
    return raw;
  }

  bool get _isValidCredentials {
    final folio = _folioCtrl.text.trim();
    final plate = _normalizedPlate;
    return _folioRegex.hasMatch(folio) && _plateRegex.hasMatch(plate);
  }

  String get _operatorName {
    final folio = _folioCtrl.text.trim();
    return _officialOperators[folio] ?? 'Operador Cert. #$folio';
  }

  String get _economicNumber {
    final plate = _normalizedPlate;
    if (plate == 'MEX-1234') return 'unit-demo-01 (U-042)';
    if (plate == 'MEX-2048') return 'unit-demo-01 (U-108)';
    return 'unit-demo-01';
  }

  void _applyPreset(String folio, String plate, {String method = 'manual'}) {
    HapticFeedback.selectionClick();
    setState(() {
      _folioCtrl.text = folio;
      _plateCtrl.text = plate;
      _authMethod = method;
    });
  }

  Future<void> _openQrScannerModal() async {
    HapticFeedback.mediumImpact();
    await showCupertinoModalPopup<void>(
      context: context,
      builder: (modalContext) => _QrScannerSheet(
        onScanned: (folio, plate) {
          Navigator.of(modalContext).pop();
          _applyPreset(folio, plate, method: 'qr');
        },
      ),
    );
  }

  Future<void> _openCameraCaptureModal(String side) async {
    HapticFeedback.selectionClick();
    final sideTitle =
        side == 'front' ? 'Anverso de INE (Frente)' : 'Reverso de INE (MRZ / QR)';
    await showCupertinoModalPopup<void>(
      context: context,
      builder: (modalContext) => _CameraCaptureSheet(
        sideTitle: sideTitle,
        isFront: side == 'front',
        onCaptured: () {
          Navigator.of(modalContext).pop();
          setState(() {
            if (side == 'front') {
              _frontCaptured = true;
              _frontSource = 'Cámara HD';
            } else {
              _backCaptured = true;
              _backSource = 'Cámara HD';
            }
          });
        },
      ),
    );
  }

  void _uploadFromGallery(String side) {
    HapticFeedback.selectionClick();
    setState(() {
      if (side == 'front') {
        _frontCaptured = true;
        _frontSource = 'Galería';
      } else {
        _backCaptured = true;
        _backSource = 'Galería';
      }
    });
  }

  Future<void> _startIneVerification() async {
    if (!_frontCaptured || !_backCaptured || _verifyingIne) return;
    HapticFeedback.mediumImpact();
    setState(() {
      _verifyingIne = true;
      _verifyProgress = 0.25;
      _verifyStatusLabel = 'Extrayendo biometría facial y hologramas del anverso...';
    });

    await Future<void>.delayed(const Duration(milliseconds: 420));
    if (!mounted) return;
    setState(() {
      _verifyProgress = 0.65;
      _verifyStatusLabel =
          'Validando código CIC y zona de lectura mecánica (MRZ)...';
    });

    await Future<void>.delayed(const Duration(milliseconds: 420));
    if (!mounted) return;
    setState(() {
      _verifyProgress = 1.0;
      _verifyStatusLabel =
          '✓ Identidad verificada. Abriendo mapa de unidad en vivo...';
    });

    await Future<void>.delayed(const Duration(milliseconds: 260));
    if (!mounted) return;

    widget.onVerified(
      DriverSession(
        folio: _folioCtrl.text.trim(),
        unitPlate: _normalizedPlate,
        operatorName: _operatorName,
        economicNumber: _economicNumber,
        authMethod: _authMethod,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final surface = CupertinoDynamicColor.resolve(ZentryxColors.surface, context);
    final ink = CupertinoDynamicColor.resolve(ZentryxColors.ink, context);
    final muted = CupertinoDynamicColor.resolve(ZentryxColors.muted, context);
    final line = CupertinoDynamicColor.resolve(ZentryxColors.line, context);

    return CupertinoPageScaffold(
      navigationBar: CupertinoNavigationBar(
        transitionBetweenRoutes: false,
        middle: Text(
          _step == 1
              ? 'Verificación de Operador'
              : 'Verificación de Identidad (INE)',
        ),
        previousPageTitle: 'Inicio',
      ),
      child: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(
              maxWidth: ZentryxLayout.maxContentWidth,
            ),
            child: SingleChildScrollView(
              padding: ZentryxLayout.pagePadding,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _StepHeader(currentStep: _step),
                  const SizedBox(height: 16),
                  if (_step == 1)
                    _buildStep1AuthCard(context, surface, ink, muted, line)
                  else
                    _buildStep2IneCard(context, surface, ink, muted, line),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStep1AuthCard(
    BuildContext context,
    Color surface,
    Color ink,
    Color muted,
    Color line,
  ) {
    final hasAnyInput =
        _folioCtrl.text.trim().isNotEmpty || _plateCtrl.text.trim().isNotEmpty;
    final valid = _isValidCredentials;

    return ZentryxCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: ZentryxColors.brandSoft,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  CupertinoIcons.person_badge_plus_fill,
                  color: ZentryxColors.brandStrong,
                  size: 21,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'PASO 1 · AUTENTICACIÓN DE OPERADOR',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.1,
                        color: ZentryxColors.brandStrong,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Vinculación con Unidad Activa',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: ink,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            'Ingresa tu Folio Único y la matrícula de la unidad para enlazar la telemetría en vivo y los controles de seguridad.',
            style: TextStyle(fontSize: 13, color: muted, height: 1.35),
          ),
          const SizedBox(height: 16),
          Text(
            'Folio Único de Operador / No. de Empleado',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: ink,
            ),
          ),
          const SizedBox(height: 6),
          CupertinoTextField(
            controller: _folioCtrl,
            placeholder: 'Ej. 84021',
            keyboardType: TextInputType.number,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            style: TextStyle(
              fontSize: 21,
              fontWeight: FontWeight.w800,
              color: ink,
              letterSpacing: 1.2,
            ),
            decoration: BoxDecoration(
              color: CupertinoDynamicColor.resolve(ZentryxColors.paper, context),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: line),
            ),
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 14),
          Text(
            'Matrícula de la Unidad (Placas)',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: ink,
            ),
          ),
          const SizedBox(height: 6),
          CupertinoTextField(
            controller: _plateCtrl,
            placeholder: 'Ej. MEX-1234',
            textCapitalization: TextCapitalization.characters,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: ink,
              letterSpacing: 0.8,
            ),
            decoration: BoxDecoration(
              color: CupertinoDynamicColor.resolve(ZentryxColors.paper, context),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: line),
            ),
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text(
                'Datos de prueba:',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: muted,
                ),
              ),
              _QuickPresetChip(
                label: 'Folio 84021 · MEX-1234',
                onTap: () => _applyPreset('84021', 'MEX-1234'),
              ),
              _QuickPresetChip(
                label: 'Folio 10492 · MEX-2048',
                onTap: () => _applyPreset('10492', 'MEX-2048'),
              ),
            ],
          ),
          const SizedBox(height: 14),
          AnimatedOpacity(
            duration: const Duration(milliseconds: 260),
            opacity: hasAnyInput ? 1.0 : 0.0,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 280),
              curve: Curves.easeOutCubic,
              padding: hasAnyInput
                  ? const EdgeInsets.symmetric(horizontal: 14, vertical: 12)
                  : EdgeInsets.zero,
              height: hasAnyInput ? null : 0,
              decoration: BoxDecoration(
                color: valid
                    ? const Color(0xFFECFDF5)
                    : const Color(0xFFFFFBEB),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: valid
                      ? const Color(0xFF10B981)
                      : const Color(0xFFF59E0B),
                ),
              ),
              child: hasAnyInput
                  ? Row(
                      children: [
                        Icon(
                          valid
                              ? CupertinoIcons.checkmark_shield_fill
                              : CupertinoIcons.info_circle_fill,
                          color: valid
                              ? const Color(0xFF0F7644)
                              : const Color(0xFFB45309),
                          size: 22,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                valid
                                    ? 'Operador Vigente y Asignado'
                                    : 'Validando formato de credenciales...',
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w800,
                                  color: valid
                                      ? const Color(0xFF0F7644)
                                      : const Color(0xFFB45309),
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                valid
                                    ? '$_operatorName · Unidad $_economicNumber ($_normalizedPlate)'
                                    : 'Usa un folio de 4-8 dígitos (ej. 84021) y placa tipo MEX-1234.',
                                style: const TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: Color(0xFF111217),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    )
                  : const SizedBox.shrink(),
            ),
          ),
          const SizedBox(height: 16),
          CupertinoButton(
            padding: const EdgeInsets.symmetric(vertical: 14),
            color: valid ? ZentryxColors.brandStrong : line,
            borderRadius: BorderRadius.circular(14),
            onPressed: () {
              if (!valid) return;
              HapticFeedback.mediumImpact();
              setState(() => _step = 2);
            },
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  CupertinoIcons.shield_fill,
                  size: 18,
                  color: ZentryxColors.white,
                ),
                SizedBox(width: 8),
                Flexible(
                  child: Text(
                    'Continuar a Verificación de INE',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: ZentryxColors.white,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          CupertinoButton(
            padding: const EdgeInsets.symmetric(vertical: 12),
            color: ZentryxColors.brandSoft,
            borderRadius: BorderRadius.circular(14),
            onPressed: _openQrScannerModal,
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  CupertinoIcons.qrcode_viewfinder,
                  size: 20,
                  color: ZentryxColors.brandStrong,
                ),
                SizedBox(width: 8),
                Flexible(
                  child: Text(
                    'Escanear Código QR',
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: ZentryxColors.brandStrong,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep2IneCard(
    BuildContext context,
    Color surface,
    Color ink,
    Color muted,
    Color line,
  ) {
    final ready = _frontCaptured && _backCaptured;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ZentryxCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: ZentryxColors.brandSoft,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      'PASO 2 DE 2 · IDENTIDAD',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        color: ZentryxColors.brandStrong,
                      ),
                    ),
                  ),
                  const Spacer(),
                  CupertinoButton(
                    padding: EdgeInsets.zero,
                    minimumSize: Size.zero,
                    onPressed: () => setState(() => _step = 1),
                    child: const Text(
                      'Editar folio/placa',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: ZentryxColors.brandStrong,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                'Toma una foto del anverso y reverso de tu INE',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  color: ink,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Operador $_operatorName (#${_folioCtrl.text.trim()}) · Unidad $_normalizedPlate. Al terminar, entrarás al mapa en vivo con la misma unidad y el módulo de emergencias.',
                style: TextStyle(fontSize: 12, color: muted, height: 1.35),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        _IneCaptureCard(
          title: '1. Anverso de tu INE (Frente)',
          subtitle: 'Fotografía mostrando rostro, nombre y clave de elector',
          captured: _frontCaptured,
          sourceLabel: _frontSource,
          operatorName: _operatorName,
          folio: _folioCtrl.text.trim(),
          isFront: true,
          onCamera: () => _openCameraCaptureModal('front'),
          onGallery: () => _uploadFromGallery('front'),
        ),
        const SizedBox(height: 12),
        _IneCaptureCard(
          title: '2. Reverso de tu INE (Atrás)',
          subtitle: 'Fotografía mostrando códigos QR y zona de lectura MRZ',
          captured: _backCaptured,
          sourceLabel: _backSource,
          operatorName: _operatorName,
          folio: _folioCtrl.text.trim(),
          isFront: false,
          onCamera: () => _openCameraCaptureModal('back'),
          onGallery: () => _uploadFromGallery('back'),
        ),
        if (_verifyingIne) ...[
          const SizedBox(height: 12),
          _IneSkeletonLoader(
            progress: _verifyProgress,
            statusLabel: _verifyStatusLabel,
          ),
        ],
        const SizedBox(height: 14),
        CupertinoButton(
          padding: const EdgeInsets.symmetric(vertical: 15),
          color: ready && !_verifyingIne ? ZentryxColors.brandStrong : line,
          borderRadius: BorderRadius.circular(14),
          onPressed: _startIneVerification,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                CupertinoIcons.checkmark_seal_fill,
                size: 18,
                color: ZentryxColors.white,
              ),
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  _verifyingIne
                      ? 'Verificando identidad...'
                      : 'Verificar INE y Abrir Mapa de Unidad',
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                    color: ZentryxColors.white,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _StepHeader extends StatelessWidget {
  const _StepHeader({required this.currentStep});
  final int currentStep;

  @override
  Widget build(BuildContext context) {
    final line = CupertinoDynamicColor.resolve(ZentryxColors.line, context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: CupertinoDynamicColor.resolve(ZentryxColors.surface, context),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: line),
      ),
      child: Row(
        children: [
          _StepBadge(
            number: '1',
            label: 'Datos de Operador',
            active: currentStep == 1,
            done: currentStep > 1,
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 8),
            child: Icon(CupertinoIcons.chevron_right, size: 14),
          ),
          _StepBadge(
            number: '2',
            label: 'Captura INE',
            active: currentStep == 2,
            done: false,
          ),
        ],
      ),
    );
  }
}

class _StepBadge extends StatelessWidget {
  const _StepBadge({
    required this.number,
    required this.label,
    required this.active,
    required this.done,
  });

  final String number;
  final String label;
  final bool active;
  final bool done;

  @override
  Widget build(BuildContext context) {
    final bg = done
        ? const Color(0xFF0F7644)
        : (active ? ZentryxColors.brandStrong : ZentryxColors.brandSoft);
    final fg = (done || active) ? ZentryxColors.white : ZentryxColors.brandDark;
    return Expanded(
      child: Row(
        children: [
          Container(
            width: 22,
            height: 22,
            alignment: Alignment.center,
            decoration: BoxDecoration(color: bg, shape: BoxShape.circle),
            child: Text(
              done ? '✓' : number,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w800,
                color: fg,
              ),
            ),
          ),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              label,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 12,
                fontWeight: active ? FontWeight.w800 : FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickPresetChip extends StatelessWidget {
  const _QuickPresetChip({required this.label, required this.onTap});
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return CupertinoButton(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      minimumSize: Size.zero,
      color: ZentryxColors.brandSoft,
      borderRadius: BorderRadius.circular(999),
      onPressed: onTap,
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: ZentryxColors.brandDark,
        ),
      ),
    );
  }
}

class _IneCaptureCard extends StatelessWidget {
  const _IneCaptureCard({
    required this.title,
    required this.subtitle,
    required this.captured,
    required this.sourceLabel,
    required this.operatorName,
    required this.folio,
    required this.isFront,
    required this.onCamera,
    required this.onGallery,
  });

  final String title;
  final String subtitle;
  final bool captured;
  final String sourceLabel;
  final String operatorName;
  final String folio;
  final bool isFront;
  final VoidCallback onCamera;
  final VoidCallback onGallery;

  @override
  Widget build(BuildContext context) {
    final ink = CupertinoDynamicColor.resolve(ZentryxColors.ink, context);
    final muted = CupertinoDynamicColor.resolve(ZentryxColors.muted, context);
    final line = CupertinoDynamicColor.resolve(ZentryxColors.line, context);

    return ZentryxCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  title,
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: ink,
                  ),
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: captured
                      ? const Color(0xFFDCFCE7)
                      : ZentryxColors.brandSoft,
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  captured ? 'CAPTURADO ($sourceLabel)' : 'PENDIENTE',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    color: captured
                        ? const Color(0xFF0F7644)
                        : ZentryxColors.brandDark,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          if (captured)
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF111217),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF10B981), width: 1.5),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(
                        CupertinoIcons.checkmark_seal_fill,
                        color: Color(0xFF10B981),
                        size: 16,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          isFront
                              ? 'INSTITUTO NACIONAL ELECTORAL · ANVERSO'
                              : 'INSTITUTO NACIONAL ELECTORAL · REVERSO (MRZ)',
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                            color: ZentryxColors.white,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    isFront
                        ? 'TITULAR: ${operatorName.toUpperCase()}\nCLAVE ELECTOR: MNRJCR88041215H200 · FOLIO $folio'
                        : 'IDMEX2491083746<<088041215H3012319\nMENDOZA<ROJAS<<CARLOS<EDUARDO<<',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFFE5E7EB),
                      height: 1.35,
                    ),
                  ),
                ],
              ),
            )
          else
            Container(
              padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 12),
              decoration: BoxDecoration(
                color: CupertinoDynamicColor.resolve(
                  ZentryxColors.paper,
                  context,
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: line),
              ),
              child: Column(
                children: [
                  Icon(
                    isFront
                        ? CupertinoIcons.creditcard
                        : CupertinoIcons.qrcode,
                    color: muted,
                    size: 28,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    subtitle,
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: muted),
                  ),
                ],
              ),
            ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: CupertinoButton(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  color: ZentryxColors.brandStrong,
                  borderRadius: BorderRadius.circular(10),
                  onPressed: onCamera,
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        CupertinoIcons.camera_fill,
                        size: 16,
                        color: ZentryxColors.white,
                      ),
                      SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          'Abrir Cámara',
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: ZentryxColors.white,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: CupertinoButton(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  color: ZentryxColors.brandSoft,
                  borderRadius: BorderRadius.circular(10),
                  onPressed: onGallery,
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        CupertinoIcons.photo_fill,
                        size: 16,
                        color: ZentryxColors.brandDark,
                      ),
                      SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          'Subir desde Galería',
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: ZentryxColors.brandDark,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _IneSkeletonLoader extends StatelessWidget {
  const _IneSkeletonLoader({
    required this.progress,
    required this.statusLabel,
  });

  final double progress;
  final String statusLabel;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: ZentryxColors.brandSoft,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: ZentryxColors.brandStrong),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const CupertinoActivityIndicator(radius: 9),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  statusLabel,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: ZentryxColors.brandDark,
                  ),
                ),
              ),
              Text(
                '${(progress * 100).round()}%',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w800,
                  color: ZentryxColors.brandStrong,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(999),
            child: SizedBox(
              height: 7,
              child: Stack(
                children: [
                  Container(color: ZentryxColors.white),
                  FractionallySizedBox(
                    widthFactor: progress.clamp(0.0, 1.0),
                    child: Container(color: ZentryxColors.brandStrong),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _QrScannerSheet extends StatelessWidget {
  const _QrScannerSheet({required this.onScanned});
  final void Function(String folio, String plate) onScanned;

  @override
  Widget build(BuildContext context) {
    final surface = CupertinoDynamicColor.resolve(ZentryxColors.surface, context);
    final ink = CupertinoDynamicColor.resolve(ZentryxColors.ink, context);
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
      decoration: BoxDecoration(
        color: surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Escáner QR Oficial SITRAMYTEM',
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w800,
                color: ink,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              height: 170,
              width: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFF111217),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: ZentryxColors.brand, width: 2),
              ),
              child: const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    CupertinoIcons.qrcode_viewfinder,
                    color: ZentryxColors.white,
                    size: 64,
                  ),
                  SizedBox(height: 8),
                  Text(
                    'CÁMARA ACTIVA · APUNTA AL GAFETE DE OPERADOR',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF10B981),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
            CupertinoButton(
              color: ZentryxColors.brandStrong,
              borderRadius: BorderRadius.circular(12),
              onPressed: () => onScanned('84021', 'MEX-1234'),
              child: const Text(
                'Simular Escaneo QR: Folio #84021 · MEX-1234',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: ZentryxColors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CameraCaptureSheet extends StatelessWidget {
  const _CameraCaptureSheet({
    required this.sideTitle,
    required this.isFront,
    required this.onCaptured,
  });

  final String sideTitle;
  final bool isFront;
  final VoidCallback onCaptured;

  @override
  Widget build(BuildContext context) {
    final surface = CupertinoDynamicColor.resolve(ZentryxColors.surface, context);
    final ink = CupertinoDynamicColor.resolve(ZentryxColors.ink, context);
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
      decoration: BoxDecoration(
        color: surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Cámara · $sideTitle',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: ink,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              height: 165,
              width: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFF0E0F12),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF10B981), width: 2),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    isFront
                        ? CupertinoIcons.person_crop_rectangle
                        : CupertinoIcons.barcode_viewfinder,
                    color: ZentryxColors.white,
                    size: 56,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Encuadre de credencial INE detectado',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF10B981),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
            CupertinoButton(
              color: ZentryxColors.brandStrong,
              borderRadius: BorderRadius.circular(12),
              onPressed: onCaptured,
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    CupertinoIcons.camera_fill,
                    size: 18,
                    color: ZentryxColors.white,
                  ),
                  SizedBox(width: 8),
                  Text(
                    'Capturar y Previsualizar INE',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w800,
                      color: ZentryxColors.white,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
