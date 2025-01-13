from fastapi import FastAPI
from sqlalchemy import create_engine, func
from ..models.property import Property

app = FastAPI()
engine = create_engine('postgresql://username:password@postgres_db:5432/real_estate')

@app.get("/analytics/regions")
async def get_region_analytics():
    with engine.connect() as conn:
        # Count listings by region
        region_counts = conn.execute(
            func.count(Property.id).label('count'),
            func.groupby(Property.region)
        ).all()
        
        # Count TruCheck listings by region
        trucheck_counts = conn.execute(
            func.count(Property.id).label('count'),
            func.groupby(Property.region),
            Property.tru_check == True
        ).all()
        
        return {
            "region_counts": region_counts,
            "trucheck_counts": trucheck_counts
        }
