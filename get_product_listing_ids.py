"""
Go to shop's product listings page and save source html file
which contains listing ids for target products. This script will
extract the listing ids to be used in `get_product_data.py` script 
"""

from bs4 import BeautifulSoup

path_to_html_file = "" # path to html file to parse for listing ids

soup = BeautifulSoup(open(path_to_html_file), 'html.parser')
dls = soup.find_all('dl', {'class': 'item '})

listing_ids = []
for dl in dls:
	listing_ids.append(str(dl['data-id']))

print listing_ids
