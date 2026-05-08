import sys
import os

# Añadir el directorio backend al path de manera robusta
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.services.auth_service import hash_password
from datetime import datetime

def seed_admin():
    # Asegurar que las tablas existen
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Verificar si ya existe el usuario admin
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("Creando usuario administrador...")
            new_admin = User(
                username="admin",
                email="admin@secureframe.com",
                hashed_password=hash_password("admin123"), 
                role="supervisor",
                status="ACTIVE",
                token_version=1,
                created_at=datetime.utcnow()
            )
            db.add(new_admin)
            print("Usuario administrador creado exitosamente.")
        else:
            print("El usuario administrador ya existe. Actualizando contraseña y rol...")
            admin.hashed_password = hash_password("admin123")
            admin.role = "supervisor"
            admin.status = "ACTIVE"
            admin.failed_login_count = 0
            admin.locked_until = None
            print("Datos de administrador actualizados exitosamente.")
        
        db.commit()
        print("Username: admin")
        print("Password: admin123")
    except Exception as e:
        print(f"Error al crear el usuario: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin()
