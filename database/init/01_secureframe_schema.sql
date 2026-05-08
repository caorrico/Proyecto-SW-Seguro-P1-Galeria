-- SecureFrame Gallery - esquema inicial para pruebas academicas.
-- Este script se ejecuta solo cuando el volumen de PostgreSQL esta vacio.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    token_version INTEGER NOT NULL DEFAULT 1,
    failed_login_count INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITHOUT TIME ZONE NULL,
    CONSTRAINT ck_users_role CHECK (role IN ('user', 'supervisor', 'admin')),
    CONSTRAINT ck_users_status CHECK (status IN ('ACTIVE', 'BLOCKED'))
);

CREATE INDEX IF NOT EXISTS ix_users_id ON users (id);
CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS albums (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    privacy VARCHAR(20) NOT NULL DEFAULT 'private',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITHOUT TIME ZONE NULL,
    rejection_reason TEXT NULL,
    CONSTRAINT ck_albums_privacy CHECK (privacy IN ('public', 'private')),
    CONSTRAINT ck_albums_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX IF NOT EXISTS ix_albums_id ON albums (id);
CREATE INDEX IF NOT EXISTS ix_albums_status ON albums (status);
CREATE INDEX IF NOT EXISTS ix_albums_user_id ON albums (user_id);

CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    stored_path VARCHAR(500) NOT NULL,
    album_id INTEGER NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    status VARCHAR(30) NOT NULL DEFAULT 'uploaded',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_images_id ON images (id);
CREATE INDEX IF NOT EXISTS ix_images_album_id ON images (album_id);
CREATE INDEX IF NOT EXISTS ix_images_user_id ON images (user_id);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_albums_updated_at ON albums;
CREATE TRIGGER trg_albums_updated_at
BEFORE UPDATE ON albums
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

INSERT INTO users (username, email, hashed_password, role)
VALUES (
    'admin_demo',
    'admin@example.com',
    '$argon2id$v=19$m=65536,t=3,p=4$PgdgDEEIYUwJIeS8d+691w$cgfQnGVA0CGAL2VtKN2xIuKyLb1KWeEECNwhPHnQP4Y',
    'admin'
)
ON CONFLICT (username) DO NOTHING;
