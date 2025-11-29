# API Gateway & Lambda Design - Secure Smart Locker

## 1. Objetivo

Diseñar los endpoints REST expuestos vía Amazon API Gateway y los microservicios
Lambda en Python que implementan la lógica del sistema Secure Smart Locker.

Requisitos cubiertos:

- API Gateway con ~15 servicios (endpoints) reales
- Uso de múltiples métodos HTTP (GET, POST, PATCH, PUT, DELETE).
- Mínimo 5 funciones Lambda, cada una agrupando responsabilidades coherentes.
- Integración con RDS MySQL para persistencia.
- Preparado para futuras integraciones con DynamoDB y correos.

---

## 2. Microservicios Lambda (visión general)

Cada Lambda estará escrita en Python y se desplegará con permisos mínimos
para acceder solo a los recursos necesarios (RDS, DynamoDB, Secrets Manager).

### 2.1. LambdaAuthService

Responsable de autenticación y perfil de usuario.

- Maneja rutas `/auth/*`.
- Opera sobre tabla `users`.
- Funciones principales:
  - Registro de usuario.
  - Login.
  - Recuperar información del usuario logueado.

### 2.2. LambdaLockerUserService

Responsable de operaciones de lockers para el usuario final.

- Maneja rutas `/lockers/*` asociadas al usuario.
- Opera sobre tablas `lockers` y `locker_requests`.
- Funciones principales:
  - Listar lockers disponibles.
  - Asignar locker.
  - Consultar locker propio.
  - Refrescar OTP.
  - Crear solicitudes de cambio de tiempo y cancelación.

### 2.3. LambdaLockerAdminService

Responsable del panel administrativo de lockers.

- Maneja rutas `/admin/lockers/*`.
- Opera sobre `lockers`, `locker_requests` y `access_logs`.
- Funciones principales:
  - Ver estado general de lockers.
  - Ver detalle de locker.
  - Aprobar/rechazar solicitudes de cambio de tiempo.
  - Forzar liberación de locker.
  - Consultar logs de acceso.

### 2.4. LambdaOtpValidateAccess

Responsable de validar el acceso al locker mediante OTP.

- Maneja `/security/lockers/{lockerId}/access-attempt`.
- Opera principalmente sobre `lockers` y `access_logs`.
- Funciones principales:
  - Validar OTP usando hash SHA-256 + salt.
  - Registrar intentos de acceso (éxito / fallo / expirado / inválido).
  - Integrarse con límites de throttling (API Gateway) para evitar fuerza bruta.

### 2.5. LambdaSecurityAuditWorker

Responsable de tareas de auditoría y seguridad.

- Puede ser invocada por eventos (CloudWatch Events) o directamente.
- Opera sobre `access_logs` y, en futuro, DynamoDB.
- Funciones principales:
  - Analizar intentos fallidos por locker/usuario.
  - Marcar eventos sospechosos.
  - Disparar correos de alerta (usuario y/o admin) cuando se detecta actividad anómala.

---

## 3. Endpoints de API Gateway

La API se expone bajo un prefijo común (por ejemplo `/api`), pero aquí
se listan los paths lógicos sin el prefijo.

### 3.1. Autenticación (LambdaAuthService)

| Método | Path           | Lambda              | Autenticación | Descripción                                      |
|--------|----------------|---------------------|---------------|--------------------------------------------------|
| POST   | `/auth/register` | LambdaAuthService | No            | Registrar nuevo usuario (name, email, password). |
| POST   | `/auth/login`  | LambdaAuthService   | No            | Autenticar usuario y devolver token (JWT).       |
| GET    | `/auth/me`     | LambdaAuthService   | Sí            | Obtener perfil del usuario autenticado.          |

---

### 3.2. Lockers - Usuario (LambdaLockerUserService)

| Método | Path                              | Lambda                   | Autenticación | Descripción                                                   |
|--------|-----------------------------------|--------------------------|---------------|---------------------------------------------------------------|
| GET    | `/lockers/available`             | LambdaLockerUserService  | Sí (user)     | Listar lockers disponibles (`status = available`).            |
| POST   | `/lockers/assign`                | LambdaLockerUserService  | Sí (user)     | Asignar locker (lockerId, tiempo, color).                     |
| GET    | `/lockers/my-locker`             | LambdaLockerUserService  | Sí (user)     | Obtener locker asignado al usuario y tiempo restante.         |
| POST   | `/lockers/my-locker/otp/refresh` | LambdaLockerUserService  | Sí (user)     | Generar nuevo OTP para el locker del usuario.                 |
| POST   | `/lockers/my-locker/request-time-change` | LambdaLockerUserService | Sí (user) | Crear solicitud para extender tiempo de uso del locker.       |
| POST   | `/lockers/my-locker/request-cancel`      | LambdaLockerUserService | Sí (user) | Crear solicitud para cancelar el locker (tiempo de gracia).   |

---

### 3.3. Lockers - Admin (LambdaLockerAdminService)

| Método | Path                                  | Lambda                   | Autenticación | Descripción                                                  |
|--------|---------------------------------------|--------------------------|---------------|--------------------------------------------------------------|
| GET    | `/admin/lockers`                     | LambdaLockerAdminService | Sí (admin)    | Listar todos los lockers (verde/rojo, usuario, expiración).  |
| GET    | `/admin/lockers/{lockerId}`          | LambdaLockerAdminService | Sí (admin)    | Ver detalle de un locker específico.                         |
| PATCH  | `/admin/lockers/{lockerId}/time`     | LambdaLockerAdminService | Sí (admin)    | Aprobar/cambiar tiempo de expiración del locker.             |
| PUT    | `/admin/lockers/{lockerId}/config`   | LambdaLockerAdminService | Sí (admin)    | Actualizar configuración del locker (color, estado, etc.).   |
| DELETE | `/admin/lockers/{lockerId}/force-release` | LambdaLockerAdminService | Sí (admin) | Forzar liberación del locker (quitar propietario).           |
| GET    | `/admin/lockers/{lockerId}/logs`     | LambdaLockerAdminService | Sí (admin)    | Consultar logs de acceso para ese locker.                    |

> Nota: Aquí se cubren métodos GET, POST, PATCH, PUT y DELETE con casos reales
> para cumplir el requisito de utilizar todos los métodos HTTP.

---

### 3.4. Seguridad / OTP (LambdaOtpValidateAccess + LambdaSecurityAuditWorker)

| Método | Path                                         | Lambda                | Autenticación | Descripción                                                                 |
|--------|----------------------------------------------|-----------------------|---------------|-----------------------------------------------------------------------------|
| POST   | `/security/lockers/{lockerId}/access-attempt` | LambdaOtpValidateAccess | No (OTP)    | Endpoint usado por el "casillero físico/simulado" para validar OTP.        |
| GET    | `/security/audit/suspicious-events`          | LambdaSecurityAuditWorker | Sí (admin) | Consultar eventos marcados como sospechosos (basado en `access_logs`).     |

> El endpoint `/security/lockers/{lockerId}/access-attempt` estará protegido
> mediante throttling en API Gateway (ej. 5 intentos por minuto) para mitigar
> ataques de fuerza bruta.

---

## 4. Consideraciones de Seguridad

- Todas las Lambdas usarán un secret en AWS Secrets Manager para obtener
  las credenciales de RDS MySQL.  
- Principio de mínimo privilegio:
  - Lambdas de auth y lockers: solo acceso SELECT/INSERT/UPDATE a las tablas necesarias.
  - LambdaOtpValidateAccess: acceso de lectura a lockers, escritura en access_logs.
  - LambdaSecurityAuditWorker: lectura de access_logs y, si aplica, acceso a DynamoDB.
- Throttling en API Gateway:
  - En particular para `/security/lockers/{lockerId}/access-attempt`
    (ejemplo: 5 req/min por IP o API key).
- El rol IAM de LambdaOtpValidateAccess tendrá:
  - Permisos `secretsmanager:GetSecretValue` sobre el secreto de RDS.
  - Permisos limitados a la VPC (`SgSmartLockerLambda`).

---

## 5. Resumen

- Se definen 15 endpoints útiles, alineados con el flujo de:
  - Registro y login de usuarios.
  - Asignación y gestión de lockers por parte del usuario.
  - Panel de administración de lockers.
  - Validación de OTP y auditoría de seguridad.
- Se definen 5 funciones Lambda claras, cada una con responsabilidades concretas.
- Se cubren todos los métodos HTTP básicos (GET, POST, PATCH, PUT, DELETE).
- El diseño está listo para implementarse en AWS API Gateway y AWS Lambda.
