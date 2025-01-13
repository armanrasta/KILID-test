from celery import Celery
from sqlalchemy import create_engine
from src.models.property import Property, Base

celery_app = Celery('tasks',
                    broker='amqp://arman:arman@rabbitmq_broker:5672/',
                    backend='db+postgresql://username:password@postgres_db:5432/real_estate')

@celery_app.task
def process_property_details(property_data: dict):
    # Save to database
    engine = create_engine('postgresql://username:password@postgres_db:5432/real_estate')
    Base.metadata.create_all(engine)
    
    property_obj = Property(**property_data)
    with engine.begin() as conn:
        conn.add(property_obj)
