# Security Groups Design - Secure Smart Locker

## 1. Overview

La seguridad de red se implementa mediante grupos de seguridad escalonados
en la VPC `smartlocker-vpc`. Cada capa (ALB, aplicación, base de datos, Lambdas)
tiene su propio SG con reglas mínimas necesarias (principio de mínimo privilegio).

## 2. SG-ALB (SgSmartLockerAlb)

- **VPC:** smartlocker-vpc
- **Uso:** Application Load Balancer (entrypoint público)

**Inbound Rules:**

| Tipo   | Protocolo | Puerto | Origen    | Comentario                       |
|--------|-----------|--------|-----------|----------------------------------|
| HTTP   | TCP       | 80     | 0.0.0.0/0 | Acceso público (entorno dev/test)|
| HTTPS* | TCP       | 443    | 0.0.0.0/0 | Producción con SSL (futuro)      |

**Outbound Rules:**

| Tipo   | Protocolo | Puerto | Destino   | Comentario                               |
|--------|-----------|--------|-----------|------------------------------------------|
| All TCP| TCP       | 0-65535| 0.0.0.0/0 | Permitir tráfico hacia capa de aplicación|

## 3. SG-APP (SgSmartLockerApp)

- **VPC:** smartlocker-vpc
- **Uso:** Instancias EC2 con Flask (backend principal)

**Inbound Rules:**

| Tipo       | Protocolo | Puerto | Origen             | Comentario                                     |
|------------|-----------|--------|--------------------|------------------------------------------------|
| HTTP       | TCP       | 80     | sg-smartlocker-alb | Tráfico interno desde el ALB hacia Flask      |
| Custom TCP | TCP       | 5000   | sg-smartlocker-alb | Si Flask escucha en 5000 internamente         |
| SSH*       | TCP       | 22     | MI_IP/32           | Acceso de administración temporal (opcional)  |

**Outbound Rules:**

| Tipo   | Protocolo | Puerto | Destino   | Comentario                                         |
|--------|-----------|--------|-----------|----------------------------------------------------|
| All TCP| TCP       | 0-65535| 0.0.0.0/0 | Actualizaciones, salida a RDS vía NAT, etc.        |

## 4. SG-RDS (SgSmartLockerRDS)

- **VPC:** smartlocker-vpc
- **Uso:** Instancia RDS MySQL principal del sistema

**Inbound Rules:**

| Tipo         | Protocolo | Puerto | Origen                | Comentario                                   |
|--------------|-----------|--------|-----------------------|----------------------------------------------|
| MySQL/Aurora | TCP       | 3306   | sg-smartlocker-app    | Conexiones desde EC2 Flask                   |
| MySQL/Aurora | TCP       | 3306   | sg-smartlocker-lambda | Conexiones desde Lambdas dentro de la VPC    |

**Outbound Rules:**

| Tipo   | Protocolo | Puerto | Destino   | Comentario                            |
|--------|-----------|--------|-----------|---------------------------------------|
| All TCP| TCP       | 0-65535| 0.0.0.0/0 | Comportamiento por defecto de RDS     |

## 5. SG-LAMBDA (SgSmartLockerLambda)

- **VPC:** smartlocker-vpc
- **Uso:** Lambdas que acceden a RDS y recursos internos

**Inbound Rules:**

_No se definen reglas específicas; las Lambdas inician las conexiones._

**Outbound Rules:**

| Tipo   | Protocolo | Puerto | Destino   | Comentario                                    |
|--------|-----------|--------|-----------|-----------------------------------------------|
| All TCP| TCP       | 0-65535| 0.0.0.0/0 | Permitir salida hacia RDS, DynamoDB, etc.     |

## 6. Justificación

- Solo el ALB está expuesto a internet.
- La capa de aplicación (Flask) solo recibe tráfico del ALB.
- La base de datos solo acepta conexiones desde la capa de aplicación y Lambdas internas.
- Se minimizan los puntos de entrada y se aplica el principio de mínimo privilegio.
