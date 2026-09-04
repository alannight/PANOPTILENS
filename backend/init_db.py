"""
Initialize database tables for PANOPTILENS
Creates all tables based on SQLAlchemy models
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, Base
from app.models.user import User
from app.models.case import Case
from app.models.image import Image, ImageHash, ImageMetadata, ForensicAnalysis
from app.models.evidence import EvidenceItem, Finding
from app.models.analysis import OCRResult, Clue, TimelineEvent

def init_database():
    """
    Create all tables in the database
    """
    print("Initializing PANOPTILENS database...")
    print(f"Database URL: {engine.url}")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully!")
        
        # List created tables
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
