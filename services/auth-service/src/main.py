from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
import os
import atexit

from .config import config
from .database import create_tables, SessionLocal, ensure_tables
from .models import Admin
from .services.auth_service import hash_password
from .routes.auth_routes import router as auth_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Auth Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=config.ALLOWED_METHODS,
    allow_headers=config.ALLOWED_HEADERS,
)

scheduler = BackgroundScheduler()

def run_study_reminders():
    try:
        db = SessionLocal()
        
        from .services.email_reminders import send_reminders_to_users

        result = send_reminders_to_users(db)
        logger.info(f"[REMINDER DEBUG] Kết quả gửi nhắc nhở: {result}")
        db.close()
    except Exception as e:
        logger.error(f"[REMINDER DEBUG] Lỗi khi gửi nhắc nhở: {str(e)}")

scheduler.add_job(
    func=run_study_reminders,
    trigger=CronTrigger(minute="*"),
    id='study_reminders',
    name='Send study reminder emails',
    replace_existing=True
)

scheduler.start()
logger.info("Background scheduler started for study reminders")
atexit.register(lambda: scheduler.shutdown())

app.include_router(auth_router)

@app.on_event("startup")
async def startup_event():
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        logger.info("Running on AWS Lambda - skipping database setup")
        return
    
    try:
        ensure_tables()
        logger.info("Database setup completed successfully")
        db = SessionLocal()
        try:
            admin = db.query(Admin).filter(Admin.username == config.ADMIN_USERNAME).first()
            if not admin:
                admin = Admin(
                    username=config.ADMIN_USERNAME,
                    password=hash_password(config.ADMIN_PASSWORD)
                )
                db.add(admin)
                db.commit()
                logger.info("Default admin user created")
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.get("/")
async def root():
    return {"message": "Auth Service is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth-service"}

@app.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration"""
    return {
        "FRONTEND_URL": config.FRONTEND_URL,
        "DATABASE_URL": config.DATABASE_URL[:50] + "..." if config.DATABASE_URL else None,
        "JWT_SECRET_KEY": config.JWT_SECRET_KEY[:10] + "..." if config.JWT_SECRET_KEY else None,
        "SMTP_USERNAME": config.SMTP_USERNAME,
        "EMAIL_VERIFICATION_EXPIRE_MINUTES": config.EMAIL_VERIFICATION_EXPIRE_MINUTES,
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
