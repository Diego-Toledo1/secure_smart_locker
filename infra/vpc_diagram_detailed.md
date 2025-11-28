# Diagrama Detallado de VPC - Secure Smart Locker

## 1. Resumen

- VPC: `smartlocker-vpc` (`10.0.0.0/16`)
- Región: `us-east-2`
- 3 capas:
  - Capa pública (ALB, NAT)
  - Capa privada de aplicación (EC2 Flask, Lambdas en VPC)
  - Capa privada de datos (RDS MySQL)

## 2. Componentes

### 2.1. VPC y Gateway

- VPC: `smartlocker-vpc` (`10.0.0.0/16`)
- Internet Gateway: `smartlocker-igw`
- NAT Gateway: `smartlocker-nat-a` en `smartlocker-public-a`

### 2.2. Subnets y Tablas de Ruta

#### Capa Pública

- Route Table: `rtb-smartlocker-public`
  - Rutas:
    - `10.0.0.0/16` → `local`
    - `0.0.0.0/0` → `smartlocker-igw`
  - Subnets:
    - `smartlocker-public-a` (`10.0.0.0/24`, `us-east-2a`)
    - `smartlocker-public-b` (`10.0.1.0/24`, `us-east-2b`)

Uso:
- ALB (Application Load Balancer)
- NAT Gateway (`smartlocker-nat-a`)

#### Capa Privada de Aplicación

- Route Table: `rtb-smartlocker-private-app`
  - Rutas:
    - `10.0.0.0/16` → `local`
    - `0.0.0.0/0` → `smartlocker-nat-a`
  - Subnets:
    - `smartlocker-private-app-a` (`10.0.10.0/24`, `us-east-2a`)
    - `smartlocker-private-app-b` (`10.0.11.0/24`, `us-east-2b`)

Uso:
- EC2 con Flask (backend principal)
- Lambdas en VPC que consumen RDS

#### Capa Privada de Base de Datos

- Route Table: `rtb-smartlocker-private-db`
  - Rutas:
    - `10.0.0.0/16` → `local`
  - Subnets:
    - `smartlocker-private-db-a` (`10.0.12.0/24`, `us-east-2a`)
    - `smartlocker-private-db-b` (`10.0.13.0/24`, `us-east-2b`)

Uso:
- RDS MySQL (Multi-AZ ready)
- Sin salida directa a internet

## Tabla Subnets

## Subnets

| Name                     | CIDR        | AZ         | Type           | Purpose                      |
|--------------------------|------------|-----------|----------------|------------------------------|
| smartlocker-public-a     | 10.0.0.0/24 | us-east-2a| Public         | ALB, NAT                     |
| smartlocker-public-b     | 10.0.1.0/24 | us-east-2b| Public         | ALB                          |
| smartlocker-private-app-a| 10.0.10.0/24| us-east-2a| Private (App)  | EC2 Flask, Lambdas in VPC    |
| smartlocker-private-app-b| 10.0.11.0/24| us-east-2b| Private (App)  | EC2 Flask, Lambdas in VPC    |
| smartlocker-private-db-a | 10.0.12.0/24| us-east-2a| Private (DB)   | RDS MySQL                    |
| smartlocker-private-db-b | 10.0.13.0/24| us-east-2b| Private (DB)   | RDS MySQL (Multi-AZ ready)   |