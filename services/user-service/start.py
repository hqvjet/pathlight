#!/usr/bin/env python3
"""
Standalone startup script for Pathlight User Service
Run this to start the service independently
"""
import sys
import os
import logging
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """Main function to start the service"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Import after path setup
        import uvicorn
        from src.config import config
        
        logger.info("🚀 Starting Pathlight User Service...")
        logger.info(f"📊 Service Port: {config.SERVICE_PORT}")
        logger.info(f"🗃️ Database: {config.DATABASE_URL}")
        logger.info(f"🐛 Debug Mode: {config.DEBUG}")
        
        # Start the service
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=config.SERVICE_PORT,
            reload=config.DEBUG,
            log_level="info" if not config.DEBUG else "debug"
        )
        
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("Please install required packages: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
