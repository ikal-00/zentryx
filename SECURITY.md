# Seguridad de Zentryx

## Nunca subir al repositorio

- `.env`;
- `POSTGRES_PASSWORD`;
- tokens de dispositivos o conductores;
- claves SSH privadas;
- tokens temporales de GitHub;
- credenciales de Tailscale;
- copias reales de bases de datos con datos sensibles.

Los valores de ejemplo deben ser claramente ficticios.

## Red de desarrollo

La API compartida debe permanecer enlazada a la IP de Tailscale del servidor, no a una interfaz pública de Internet. PostgreSQL no debe publicar `5432` al host salvo una necesidad explícita.

## Tokens

Los tokens persistidos por la API se almacenan como hashes SHA-256. Los secretos originales deben tratarse como credenciales y rotarse si se exponen.

## Dependencias

Las dependencias de producción viven en `backend/requirements.txt` y `app/requirements.txt`. `requirements-dev.txt` combina ambas para desarrollo local.

## Reporte

Si detectas una vulnerabilidad, comunícala directamente a los mantenedores sin publicar credenciales ni datos reales. Incluye componente, impacto, reproducción mínima y commit afectado.
