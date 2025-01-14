from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Property(Base):
    __tablename__ = 'properties'
    
    # Basic Required fields
    id = Column(Integer, primary_key=True)
    property_id = Column(String, unique=True, nullable=False)
    title = Column(Text)
    price = Column(String, nullable=True)
    location = Column(String)
    region = Column(String)
    property_type = Column(String)
    purpose = Column(String)
    country = Column(String)
    beds = Column(String, nullable=True)
    baths = Column(String, nullable=True)
    area = Column(String, nullable=True)
    image_url = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    crawl_timestamp = Column(String)
    
    # Additional fields
    features = Column(JSON)
    last_checked = Column(DateTime, default=datetime.now)
    reference = Column(String)
    completion_status = Column(String)
    furnishing = Column(String)

    # Additional nullable fields from Bayut spider
    currency = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    trucheck_date = Column(String, nullable=True)
    reactivated_date = Column(String, nullable=True)
    handover_date = Column(String, nullable=True)

    # Validated Information
    developer = Column(String, nullable=True)
    ownership = Column(String, nullable=True)
    built_up_area = Column(String, nullable=True)
    usage = Column(String, nullable=True)
    parking_availability = Column(Boolean, nullable=True)

    # Building Information
    building_name = Column(String, nullable=True)
    year_of_completion = Column(Integer, nullable=True)
    total_floors = Column(Integer, nullable=True)
    total_building_area = Column(String, nullable=True)

    # Agency Information
    agent_name = Column(String, nullable=True)
    agent_rating = Column(String, nullable=True)
    agency_name = Column(String, nullable=True)
    agency_url = Column(String, nullable=True)

    # Contact Information
    contact_number = Column(String, nullable=True)

    # Additional fields from Bayut
    link_name = Column(String, nullable=True)
    type = Column(String, nullable=True)
    permit_number = Column(String, nullable=True)
    brn_number = Column(String, nullable=True)
    guide_link_title = Column(String, nullable=True)
    average_rent = Column(String, nullable=True)
    floorplan_type = Column(String, nullable=True)
    floorplan_rooms = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<Property(id={self.property_id}, title={self.title})>"
