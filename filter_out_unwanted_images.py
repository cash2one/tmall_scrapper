"""
After target images have been downloaded using `get_images.py` this script
may be used to filter out unwanted images according to their dimensions.
Unwanted images may include decoration banners and other non-product images.
Typically the dimensions of these unwanted images will be the same for different
listings as they are just reused for each.
"""

import os
from PIL import Image
from database import *
from settings import BASE_DIR, SHOP as shop

db=get_db()
products=db.query(Product).all()
listing_ids=[str(p.listing_id) for p in products]

TARGET_DIR = os.path.join(BASE_DIR, shop['name'], 'images/{}/')

def delete_img(path):
    os.remove(path)

for idx, item in enumerate(listing_ids, 0):

    item_dir = TARGET_DIR.format(item)

    try:
        os.stat(item_dir)
    except:
        pass

    for (path, dirs, files) in os.walk(item_dir):

        for file in files:
            image_path = os.path.join(item_dir, file)

            img = Image.open(image_path)
            width = img.size[0]
            height = img.size[1]

            if width == 750 and height == 43:
                delete_img(image_path)

            elif width == 750 and height == 160:
                delete_img(image_path)

            elif width == 750 and height == 841:
                delete_img(image_path)

            elif width == 680 and height == 841:
                delete_img(image_path)
            
            else:
                pass