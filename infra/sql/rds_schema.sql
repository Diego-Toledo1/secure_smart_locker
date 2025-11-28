-- Crear base de datos (si no existe) y seleccionarla
CREATE DATABASE IF NOT EXISTS smartlocker_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE smartlocker_db;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  email         VARCHAR(255) NOT NULL UNIQUE,
  name          VARCHAR(150) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role          ENUM('user','admin') NOT NULL DEFAULT 'user',
  created_at    DATETIME NOT NULL,
  updated_at    DATETIME NULL
) ENGINE=InnoDB;

-- Tabla de casilleros (lockers)
CREATE TABLE IF NOT EXISTS lockers (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  code             VARCHAR(50) NOT NULL UNIQUE, -- A1, A2, B3...
  status           ENUM('available','occupied','disabled') NOT NULL DEFAULT 'available',
  current_user_id  INT NULL,
  assigned_at      DATETIME NULL,
  expires_at       DATETIME NULL,
  current_otp_hash CHAR(64) NULL,   -- SHA-256(OTP + salt)
  otp_salt         CHAR(32) NULL,   -- salt en hex
  otp_valid_until  DATETIME NULL,
  color_hex        CHAR(7) NULL,    -- #RRGGBB (locker personalizado)
  created_at       DATETIME NOT NULL,
  updated_at       DATETIME NULL,
  CONSTRAINT fk_lockers_user
    FOREIGN KEY (current_user_id) REFERENCES users(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB;

-- Tabla de logs de acceso y eventos
CREATE TABLE IF NOT EXISTS access_logs (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  locker_id   INT NOT NULL,
  user_id     INT NULL,
  event_type  ENUM('access_attempt','otp_rotation','owner_removed','time_changed') NOT NULL,
  status      ENUM('success','failed','expired','invalid_otp') NOT NULL,
  reason      VARCHAR(255) NULL,
  source_ip   VARCHAR(45) NULL,
  user_agent  VARCHAR(255) NULL,
  created_at  DATETIME NOT NULL,
  CONSTRAINT fk_access_logs_locker
    FOREIGN KEY (locker_id) REFERENCES lockers(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_access_logs_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON UPDATE CASCADE
    ON DELETE SET NULL
) ENGINE=InnoDB;

-- Tabla de solicitudes de cambios (extensión de tiempo, cancelación, etc.)
CREATE TABLE IF NOT EXISTS locker_requests (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  locker_id     INT NOT NULL,
  user_id       INT NOT NULL,
  request_type  ENUM('change_time','cancel') NOT NULL,
  status        ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  requested_until DATETIME NULL,        -- nueva fecha propuesta de expiración
  notes         VARCHAR(255) NULL,      -- motivo o comentario
  created_at    DATETIME NOT NULL,
  resolved_at   DATETIME NULL,
  CONSTRAINT fk_requests_locker
    FOREIGN KEY (locker_id) REFERENCES lockers(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE,
  CONSTRAINT fk_requests_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
) ENGINE=InnoDB;
