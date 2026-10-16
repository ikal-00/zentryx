class DriverSession {
  const DriverSession({
    required this.folio,
    required this.unitPlate,
    required this.operatorName,
    required this.economicNumber,
    required this.authMethod,
    this.ineVerified = true,
  });

  final String folio;
  final String unitPlate;
  final String operatorName;
  final String economicNumber;
  final String authMethod; // 'manual' | 'qr'
  final bool ineVerified;
}
