from sqlalchemy.orm import Session
from db.base import SessionLocal
from db.models.test import SyntheticData
from datetime import datetime

def seed_ai(db: Session):
    print("Seeding Synthetic AI Data...")
    
    samples = [
        {"name": "AI Spark", "email": "spark@ai.test", "synthetic_value": "Generated-Alpha-001"},
        {"name": "Neural Mind", "email": "mind@ai.test", "synthetic_value": "Generated-Beta-002"},
        {"name": "Data Ghost", "email": "ghost@ai.test", "synthetic_value": "Generated-Gamma-003"},
        {"name": "Logic Bot", "email": "bot@ai.test", "synthetic_value": "Generated-Delta-004"},
        {"name": "Quantum Flow", "email": "flow@ai.test", "synthetic_value": "Generated-Epsilon-005"}
    ]
    
    for s_data in samples:
        existing = db.query(SyntheticData).filter(SyntheticData.email == s_data["email"]).first()
        if not existing:
            data = SyntheticData(
                name=s_data["name"],
                email=s_data["email"],
                synthetic_value=s_data["synthetic_value"]
            )
            db.add(data)
            print(f"  Created synthetic record: {s_data['name']}")
        else:
            print(f"  Synthetic record exists: {s_data['name']}")
    
    db.commit()
    print("AI Seeding complete.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_ai(db)
    finally:
        db.close()
