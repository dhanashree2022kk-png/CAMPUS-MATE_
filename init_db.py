"""Create CampusMate tables without removing existing data."""
from app import app, db
with app.app_context():
    db.create_all()
print('Database initialized; existing records were preserved.')
