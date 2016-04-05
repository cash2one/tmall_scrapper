"""
Initiates database connection
"""

from sqlalchemy.orm import sessionmaker
from models import (Vendor, Product, Variation, InitialImage, 
    db_connect)

def get_db():
    engine=db_connect()
    session=sessionmaker(bind=engine)
    db=session()
    return db