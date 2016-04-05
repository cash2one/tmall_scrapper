"""
Downloads product images from provided listing ids in `target_listing_ids` list.
This script is run after `get_product_data.py` because only then will target image
urls be present in database 
"""

import os
import time
import urllib
from database import *
from settings import BASE_DIR, SHOP as shop

target_listing_ids = [] # pre populate

TARGET_DIR = os.path.join(BASE_DIR, shop['name'], 'initial_images/{}/')

import urllib

db = get_db()

products = db.query(Product).all()
downloaded_images_for_these_listing_ids = []

for lidx, listing_id in enumerate(target_listing_ids, 1):

	try:
		product = db.query(Product).filter(Product.listing_id==int(listing_id)).first()

		to_path = TARGET_DIR.format(listing_id)

		try:
			os.stat(to_path)
		except:
			os.mkdir(to_path)

		product_images = product.images
		image_urls = [pi.url for pi in product_images]

		for idx, url in enumerate(image_urls):
		
			filename = to_path + listing_id + '-' + str(idx) + '.jpg'
			urllib.urlretrieve(url, filename)
			time.sleep(.1)

		downloaded_images_for_these_listing_ids.append(listing_id)
		print 'finished', listing_id, ' #', lidx, 'out of', len(target_listing_ids)

		time.sleep(.1)

	except Exception as e:
		print 'exception: ', e
		print 'died on: ', listing_id
		break

print 'finished: ', downloaded_images_for_these_listing_ids
print 'total amount: ', len(downloaded_images_for_these_listing_ids)


