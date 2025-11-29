# Lambda Functions Design – Secure Smart Locker (Resumen Técnico)

Todas las funciones están escritas en Python, conectadas a RDS MySQL dentro de la VPC privada usando el Security Group `SgSmartLockerLambda`.

---

## 1. LambdaAuthService
**Propósito:** Registro, autenticación y obtención del perfil del usuario.  
**Endpoints:**
- POST /auth/register
- POST /auth/login
- GET /auth/me

**Tablas:**  
- users

**Operaciones:**  
- Hash de contraseña con SHA256 + salt  
- Generación de JWT  
- Validación de usuario

---

## 2. LambdaLockerUserService
**Propósito:** Gestión de lockers del usuario.  
**Endpoints:**
- GET /lockers/available
- POST /lockers/assign
- GET /lockers/my-locker
- POST /lockers/my-locker/otp/refresh
- POST /lockers/my-locker/request-time-change
- POST /lockers/my-locker/request-cancel

**Tablas:**  
- lockers  
- locker_requests

**Operaciones:**  
- Asignación de locker  
- Expiración y extensión  
- Rotación de OTP (hash + salt)  
- Solicitudes de usuario

---

## 3. LambdaLockerAdminService
**Propósito:** Control administrativo de lockers.  
**Endpoints:**
- GET /admin/lockers
- GET /admin/lockers/{lockerId}
- PATCH /admin/lockers/{lockerId}/time
- PUT /admin/lockers/{lockerId}/config
- DELETE /admin/lockers/{lockerId}/force-release
- GET /admin/lockers/{lockerId}/logs

**Tablas:**  
- lockers  
- locker_requests  
- access_logs

**Operaciones:**  
- Liberación forzada  
- Cambios en expiración  
- Configuración del locker  
- Consulta de auditorías

---

## 4. LambdaOtpValidateAccess
**Propósito:** Validación del OTP para acceso al casillero.  
**Endpoint:**
- POST /security/lockers/{lockerId}/access-attempt

**Tablas:**  
- lockers  
- access_logs

**Operaciones:**  
- Validación de OTP (SHA256 + salt)  
- Verificación de expiración  
- Registro de intentos (success/failed/expired)  
- Integración con throttling de API Gateway

---

## 5. LambdaSecurityAuditWorker
**Propósito:** Auditoría y detección de actividad sospechosa.  
**Endpoints:**
- GET /security/audit/suspicious-events  
- Invocación programada por CloudWatch  
- Invocación directa por LambdaOtpValidateAccess

**Tablas:**  
- access_logs  
- (Opcional) security_alerts

**Operaciones:**  
- Revisión de eventos recientes  
- Detección de patrones sospechosos  
- Notificación a usuario / admin  
- Registro de alertas

---

## Acceso a RDS y Secrets Manager
Todas las Lambdas utilizan:
- secretsmanager:GetSecretValue para credenciales  
- Conexión PyMySQL  
- Subnets privadas de la VPC  
- Security Group SgSmartLockerLambda

---

## Estructura general de los handlers
Cada Lambda usa:

```python
path = event.get("rawPath", "")
method = event.get("requestContext", {}).get("http", {}).get("method")
