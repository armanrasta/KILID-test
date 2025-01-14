from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.property import Property, Base
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Update Celery configuration with retry settings
celery_app = Celery('tasks',
                    broker='amqp://arman:arman@localhost:5672/',
                    backend='db+postgresql://username:password@localhost:5432/real_estate')

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_pool='solo' if os.name == 'nt' else 'prefork',
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_retry_on_failure=True,
    broker_connection_retry_on_startup=True
)

@celery_app.task(bind=True, max_retries=3)
def process_property_details(self, property_data: dict):
    """Process and save property details with retry mechanism."""
    logger.info(f"Starting to process property {property_data.get('property_id')}")
    
    try:
        # Clean up the data to match model fields
        cleaned_data = {}
        for key, value in property_data.items():
            # Convert any legacy field names
            if key == 'area_sqft':
                cleaned_data['area'] = value
            elif key == 'bedrooms':
                cleaned_data['beds'] = value
            elif key == 'bathrooms':
                cleaned_data['baths'] = value
            else:
                cleaned_data[key] = value

        # Initialize database connection
        engine = create_engine('postgresql://username:password@localhost:5432/real_estate')
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            existing_property = session.query(Property).filter_by(
                property_id=cleaned_data['property_id']
            ).first()

            if existing_property:
                for key, value in cleaned_data.items():
                    if hasattr(existing_property, key):  # Only set if field exists
                        setattr(existing_property, key, value)
                logger.info(f"Updating existing property {cleaned_data['property_id']}")
            else:
                property_obj = Property(**cleaned_data)
                session.add(property_obj)
                logger.info(f"Creating new property {cleaned_data['property_id']}")

            session.commit()
            logger.info(f"Successfully saved property {cleaned_data['property_id']}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise self.retry(exc=e, countdown=60)

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Critical error processing property: {str(e)}")
        raise

@celery_app.task
def test_task():
    print("Test task executed")
