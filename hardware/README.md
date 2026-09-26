# Hardware de Zentryx

Este directorio contiene diseño electrónico y archivos de fabricación/prototipado físico. No forma parte del runtime Python ni de las imágenes Docker.

## Silice

`silice/` es el proyecto KiCad activo del dispositivo de telemetría. Incluye esquemático, PCB, símbolos, footprints y modelos 3D necesarios para el diseño.

Los archivos generados por el editor (locks, cachés y backups) no deben versionarse; `.gitignore` contiene reglas específicas para KiCad.

La validación eléctrica, ERC/DRC y fabricación se gestionan desde KiCad y quedan fuera de la suite CI de software.
