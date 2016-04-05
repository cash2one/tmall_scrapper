from sqlalchemy import (create_engine, Column, Integer, Float, String, DateTime, 
	ForeignKey, func)
from sqlalchemy.dialects.mysql import VARCHAR, BIGINT, BOOLEAN, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import relationship, backref

import settings


DeclarativeBase = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """

    return create_engine(URL(**settings.DATABASE), connect_args={'charset':'utf8'})


def create_tables(engine):
    """"""
    DeclarativeBase.metadata.create_all(engine)

class Vendor(DeclarativeBase):
	__tablename__ = 'vendor'
	id = Column(Integer, primary_key=True)
	name_unicode = Column('name_unicode', VARCHAR(50), nullable=False)
	name_pinyin = Column('name_pinyin', VARCHAR(50), nullable=False)
	shop_url = Column('shop_url', VARCHAR(250), nullable=False)
	email = Column('email', VARCHAR(50), nullable=False)
	mobile = Column('mobile', VARCHAR(50), nullable=False)
	contact_name_unicode = Column('contact_name_unicode', VARCHAR(50), nullable=False)
	created = Column('created', DateTime, nullable=False, default=func.now())
	updated = Column('updated', DateTime, nullable=True)
	products = relationship(
		'Product',
		cascade='all, delete-orphan',
		backref=backref('parent_vendor',
						uselist=True,
						cascade='delete, all')
		)

	def __repr__(self):
		return '<Vendor: %d - %s>' % (self.id, self.name_pinyin)

class Product(DeclarativeBase):
	__tablename__ = 'product'
	id = Column(Integer, primary_key=True)
	listing_id = Column('listing_id', BIGINT(20), nullable=False)
	url = Column('url', VARCHAR(250), nullable=False)
	page_title = Column('page_title', VARCHAR(250), nullable=False)
	product_type = Column('product_type', VARCHAR(25), nullable=False)
	origin_unicode = Column('origin_unicode', VARCHAR(250), nullable=False)
	origin_pinyin = Column('origin_pinyin', VARCHAR(250), nullable=False)
	name_unicode = Column('name_unicode', VARCHAR(250), nullable=True)
	name_pinyin = Column('name_pinyin', VARCHAR(250), nullable=True)
	artist_unicode = Column('artist_unicode', VARCHAR(250), nullable=True)
	artist_pinyin = Column('artist_pinyin', VARCHAR(250), nullable=True)
	is_available = Column('is_available', BOOLEAN, nullable=False, default=1)
	created = Column('created', DateTime, nullable=False, default=func.now())
	updated = Column('updated', DateTime, nullable=True)
	have_final_images = Column('have_final_images', BOOLEAN, nullable=True)
	vendor_id = Column(Integer, ForeignKey('vendor.id'))
	vendor = relationship("Vendor", back_populates="products")
	variations = relationship(
		"Variation",
		cascade="all, delete-orphan",
		backref=backref("parent_product",
						uselist=True,
						cascade='delete, all'))
	images = relationship(
		"InitialImage",
		cascade="all, delete-orphan",
		backref=backref("parent_product",
						uselist=True,
						cascade='delete, all'))	

	def __repr__(self):
		return '<Product %d - Listing %d>' % (self.id, self.listing_id)

class Variation(DeclarativeBase):
	__tablename__ = 'variation'
	id = Column('id', Integer, primary_key=True)
	url = Column('url', VARCHAR(250), nullable=False)
	title_unicode = Column('title_unicode', VARCHAR(200), nullable=True)
	title_pinyin = Column('title_pinyin', VARCHAR(200), nullable=True)
	sku_external = Column('sku_external', VARCHAR(50), nullable=True)
	sku_internal = Column('sku_internal', VARCHAR(50), nullable=False)
	price = Column('price', Integer, nullable=False)
	monthly_sell_count = Column('monthly_sell_count', Integer, nullable=True)
	local_postage = Column('local_postage', Integer, nullable=True)
	inventory_count = Column('inventory_count', Integer, nullable=True)
	material_unicode = Column('material_unicode', VARCHAR(200), nullable=False)
	material_pinyin = Column('material_pinyin', VARCHAR(200), nullable=False)
	capacity = Column('capacity', Integer, nullable=True)
	height = Column('height', Float, nullable=True)
	width = Column('width', Float, nullable=True)
	length = Column('length', Float, nullable=True)
	spout_to_handle = Column('spout_to_handle', Float, nullable=True)
	mouth_diameter = Column('mouth_diameter', Float, nullable=True)
	created = Column('created', DateTime, nullable=False, default=func.now())
	updated = Column('updated', DateTime, nullable=True)
	product_id = Column(Integer, ForeignKey('product.id'))
	product = relationship("Product", back_populates="variations")
	is_listed = Column('is_listed', BOOLEAN, nullable=True)
	have_final_images = Column('have_final_images', BOOLEAN, nullable=True)
	html_template = Column('html_template', TEXT, nullable=True)

	def __repr__(self):
		return '<Variation %d - Product %d - Listing %d>' % (self.id, self.product.id, self.product.listing_id)

class InitialImage(DeclarativeBase):
	__tablename__ = 'initialimage'
	id = Column('id', Integer, primary_key=True)
	url = Column('url', VARCHAR(200), nullable=False)
	product_id = Column(Integer, ForeignKey('product.id'))
	product = relationship("Product", back_populates="images")	
	created = Column('created', DateTime, nullable=False, default=func.now())

	def __repr__(self):
		return '<InitialImage %d>' % (self.id)