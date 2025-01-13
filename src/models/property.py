from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True)
    property_id = Column(String, unique=True, nullable=False)
    title = Column(String)
    price = Column(String)
    location = Column(String)
    region = Column(String)
    tru_check = Column(Boolean, default=False)
    property_type = Column(String)
    purpose = Column(String)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    area_sqft = Column(Float)
    image_url = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Additional fields
    amenities = Column(JSON)
    features = Column(JSON)
    agent_details = Column(JSON)
    last_checked = Column(DateTime, default=datetime.now)
    property_reference = Column(String)
    completion_status = Column(String)
    furnishing_status = Column(String)

    def __repr__(self):
        return f"<Property(id={self.property_id}, title={self.title})>"
