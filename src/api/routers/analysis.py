from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, func, cast, Float
from sqlalchemy.orm import sessionmaker
from src.models.property import Property

router = APIRouter(
    prefix="/analysis",
    tags=["analysis"],
    responses={404: {"description": "Not found"}},
)

# Initialize database connection
DATABASE_URL = 'postgresql://username:password@localhost:5432/real_estate'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

@router.get("/region-listings")
async def get_region_listings():
    session = Session()
    try:
        region_counts = session.query(
            Property.region,
            func.count(Property.id).label('count')
        ).group_by(Property.region).all()

        trucheck_counts = session.query(
            Property.region,
            func.count(Property.id).label('count')
        ).filter(Property.trucheck_date.isnot(None)).group_by(Property.region).all()

        region_data = {region: count for region, count in region_counts}
        trucheck_data = {region: count for region, count in trucheck_counts}

        return {
            "region_counts": region_data,
            "trucheck_counts": trucheck_data
        }
    finally:
        session.close()


@router.get("/avg-price")
async def get_avg_price():
    session = Session()
    try:
        avg_prices = session.query(
            Property.region,
            func.avg(cast(func.replace(Property.price, ',', ''), Float)).label(
                'avg_price')
        ).group_by(Property.region).all()

        total_avg_price = session.query(
            func.avg(cast(func.replace(Property.price, ',', ''), Float)).label(
                'avg_price')
        ).scalar()

        avg_price_data = {region: avg_price for region,
                          avg_price in avg_prices}
        avg_price_data['total'] = total_avg_price

        return avg_price_data
    finally:
        session.close()


@router.get("/max_min_price")
async def get_max_min():
    """Calculate the maximum and minimum price of properties."""
    session = Session()
    try:
        max_price_per_region = session.query(
            Property.region,
            func.max(cast(func.replace(Property.price, ',', ''), Float)).label('max_price')
        ).group_by(Property.region).all()

        min_price_per_region = session.query(
            Property.region,
            func.min(cast(func.replace(Property.price, ',', ''), Float)).label('min_price')
        ).group_by(Property.region).all()

        max_price_total = session.query(
            func.max(cast(func.replace(Property.price, ',', ''), Float)).label('max_price')
        ).scalar()

        min_price_total = session.query(
            func.min(cast(func.replace(Property.price, ',', ''), Float)).label('min_price')
        ).scalar()

        data = {
            'max_price_per_region': {region: max_price for region, max_price in max_price_per_region},
            'min_price_per_region': {region: min_price for region, min_price in min_price_per_region},
            'max_price_total': max_price_total,
            'min_price_total': min_price_total
        }

        return data
    finally:
        session.close()
