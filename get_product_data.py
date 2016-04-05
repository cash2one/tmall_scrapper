# -*- coding: utf-8 -*-
"""
Scrapes necessary product and product variation text and image urls for
target products. Listing ids for target products must be present in `products`
list below.
"""
import re
import os
import datetime
from time import sleep
from selenium import webdriver
import pinyin
from models import db_connect, Vendor, Product, Variation, InitialImage
from sqlalchemy.orm import sessionmaker
from settings import BASE_DIR, SHOP as shop

PRODUCT_DIR = os.path.join(BASE_DIR, shop['name'], 'product_data')

products = [] # listing ids for products scrapped from target store

driver = webdriver.Firefox()

def get_variant_depenedent_data(self):
	"""Gets variatnt dependent data from top of listing page: price, monthly sales count,
	local postage cost, inventory count"""
	try:
		product_sale_price_div = self.find_element_by_id('J_PromoPrice') # on sale
		product_full_price_div = self.find_element_by_id('J_StrPriceModBox') # not on sale
		
		try: # try if on sale
			product_price = float(product_sale_price_div.find_element_by_class_name('tm-price').text)
		except: # except if not on sale
			product_price = float(product_full_price_div.find_element_by_class_name('tm-price').text)

	except Exception as e:
		product_price = None
		print 'product id: ', product_id
		print 'product_price error-', e

	try:
		monthly_sell_count_ul = self.find_element_by_class_name('tm-ind-panel')
		monthly_sell_count = float(monthly_sell_count_ul.find_element_by_class_name('tm-count').text)
	except Exception as e:
		monthly_sell_count = None
		print 'monthly_sell_count error-', product_id + ': ' + e

	try:
		postage_div = self.find_element_by_id('J_PostageToggleCont')
		postage_price = postage_div.find_element_by_tag_name('span').text
		postage_price = float(re.findall("[-+]?\d+[\.]?\d*", postage_price)[0])
	except Exception as e:
		postage_price = None
		print 'postage_price error-', product_id + ': ' + e

	try: # element is hidden, removes class to show
		self.execute_script("document.getElementById('J_EmStock').className.replace('tb-hidden', '');")
		available_product_count = self.find_element_by_xpath('//*[@id="J_EmStock"]').text
		available_product_count = int(re.findall("[-+]?\d+[\.]?\d*", available_product_count)[0])
	except Exception as e:
		available_product_count = None
		print 'available_product_count error-', product_id + ': ' + e

	return product_price, monthly_sell_count, postage_price, available_product_count

def get_img_tags_src_attr(content_div):
	"""Gets source tags from image elements of product in main listings body"""
	img_urls_list = []
	imgs = content_div.find_elements_by_tag_name('img')
	for img in imgs:
		img_urls_list.append(img.get_attribute('src'))
	return img_urls_list

def check_for_sku_origin(text):
	"""Parses SKU and place of origin from general product details"""
	unicode_content = text.replace(' ', '').split(':')[1]
	return unicode_content

def get_top_div_general_product_details(self):
	"""Parses information from general product details and filters for
	SKU and product origin to then parse in above function"""
	sku_u = u'\u8d27\u53f7' # 货号
	origin_u = u'\u4ea7\u5730' # 产地
	details_dict = {}
	target_lis = driver.find_elements_by_xpath('//ul[@id="J_AttrUL"]/li')
	for li in target_lis:
		text = li.text
		if sku_u in text:
			details_dict['sku'] = check_for_sku_origin(text)
		if origin_u in text:
			origin_unicode = check_for_sku_origin(text)
			origin_pinyin = pinyin.get(origin_unicode, format='strip').title()
			details_dict['origin_unicode'] = origin_unicode
			details_dict['origin_pinyin'] = origin_pinyin
	return details_dict

def check_for_name_size_artist(text):
	"""Parses product details from product body main description"""
	colon_u = u'\uff1a' # ：
	colon = ':'
	paranthesis_u = u'\uff08' # （
	handmade_u = u'\u5168\u624b\u5de5' # 全手工
	# colon_u and colon used inconsistently
	if colon_u in text:
		text = text.split(colon_u)[1]
	elif colon in text:
		text = text.split(colon)[1]
	text = text.replace(handmade_u, '') # removes handmade from name if exists
	try: # material may contain paranthesis
		text = text.split(paranthesis_u)[0]
	except: # pass if paranthesis not found
		pass
	try: # filters out 'mine' and 'old' from material
		text = text.split(mine_u)[1]
		text = text.replace(old_u, '')
	except:
		pass
	return text

def parse_material(text):
	"""Parses material and returns list. Text may contain variations"""
	original_u = u'\u539f' # 原
	mine_u = u'\u77ff' # 矿
	old_u = u'\u8001' # 老
	colon_u = u'\uff1a' # ：
	colon = ':'
	chinese_comma_u = u'\uff0c' # ，
	materials_list = [] # initiates list

	if colon_u in text:
		text = text.split(colon_u)[1]
	elif colon in text:
		text = text.split(colon)[1]

	if chinese_comma_u in text:
		materials = text.split(chinese_comma_u)
	else:
		materials = [text]

	for item in materials:
		try:
			item = item.split(mine_u)[1]
		except:
			pass
		item = item.replace(old_u, '')
		materials_list.append(item)

	return materials_list

def parse_artist(text):
	# print 'parse_artist text: ', text
	colon_u = u'\uff1a' # ：
	paranthesis_u = u'\uff08' # （
	paranthesis_end_u = u'\uff09' # ）
	# text = check_for_name_size_artist(text)
	print 'parse_artist text: ', text
	try:
		artist = text.split(paranthesis_u)[1]
		artist = artist.replace(paranthesis_end_u, '')
	except:
		artist = None
	print 'parse_artist artist: ', artist
	return artist

def parse_dimension(text, keyword):
	chinese_period_u = u'\u3002' # 。
	chinese_comma_u = u'\uff0c' # ，
	try:
		text = text.replace(chinese_period_u, '.')
		text = text.split(keyword)[1]
		text = text.split(chinese_comma_u)[0]
		dimension = re.findall("[-+]?\d+[\.]?\d*", text)
		return dimension[0]
	except Exception as e:
		print 'parse_dimension, ', e
		return None

def get_size_dimensions(text):
	"""Parses details and filters for dimensions and capacity from 
	product description in main body"""
	dimension_dict = {'product_type': 'teapot'}
	spout_to_handle_u = u'\u5634\u5230\u628a' # 嘴到把
	height_u = u'\u9ad8' # 高
	capacity_u = u'\u5bb9' # 容
	cup_diameter_u = u'\u53e3\u5f84' # 口径
	if spout_to_handle_u in text:
		dimension_dict['spout_to_handle'] = parse_dimension(text, spout_to_handle_u)
		# print 'spout_to_handle: ', dimension
	if height_u in text:
		dimension_dict['height'] = parse_dimension(text, height_u)
		# print 'height: ', dimension
	if capacity_u in text:
		dimension_dict['capacity'] = parse_dimension(text, capacity_u)		
		# print 'capacity: ', dimension
	if cup_diameter_u in text:
		dimension_dict['mouth_diameter'] = parse_dimension(text, cup_diameter_u)
		dimension_dict['product_type'] = 'teacup'
	# print 'dimension_dict', dimension_dict
	return dimension_dict

def get_content_div_product_description_details(content_div):
	"""Get product details from desciption in main body and parse"""
	name_u = u'\u54c1\u540d' # 品名
	size_u = u'\u5c3a\u5bf8' # 尺寸
	height_u = u'\u9ad8\u7ea6' # 高约
	capacity_u = u'\u5bb9\u91cf\u7ea6' # 容量约
	material_u = u'\u6ce5\u6599' # 泥料
	artist_u = u'\u4f5c\u8005' # 作者
	colon_u = u'\uff1a' # ：
	colon = ':'
	details_dict = {
			'dimension_variations': {}, # initiate dimension variations
			'material_variations': {} # initiate material variations
		}
	target_ps = content_div.find_elements_by_tag_name('p')
	for span in target_ps:
		dimension_variations = len(details_dict['dimension_variations']) # used for dict key below
		material_variations = 0
		if span.text and len(span.text) > 1:
			text = span.text.replace(' ', '')
			try:			
				title = text.split(colon_u)[0]
			except IndexError:
				title = text.split(colon)[0]
			except:
				title = 'no title'
			if name_u in title: # check only in title
				print 'name_u in title text: ', text
				name_unicode = check_for_name_size_artist(text)
				name_pinyin = pinyin.get(name_unicode, format='strip').title()
				details_dict['name_unicode'] = name_unicode
				details_dict['name_pinyin'] = name_pinyin
			elif size_u in text or height_u in text or capacity_u in text: # check in text (includes title)
				size = check_for_name_size_artist(text)
				dimension_dict = get_size_dimensions(size)
				if len(dimension_dict) > 0:
					details_dict['dimension_variations'].update({dimension_variations: dimension_dict})
			elif material_u in title: # check only in title
				material_list = parse_material(text)
				for item in material_list:
					material_unicode = item
					material_pinyin = pinyin.get(material_unicode, format='strip').title()
					details_dict['material_variations'].update({
							material_variations: {
								'material_unicode': material_unicode,
								'material_pinyin': material_pinyin
							}
						})
					material_variations += 1
			elif artist_u in title: # check only in title
				artist_unicode = parse_artist(text)
				details_dict['artist_unicode'] = artist_unicode
				if artist_unicode is not None:
					artist_pinyin = pinyin.get(artist_unicode, format='strip').title()
					details_dict['artist_pinyin'] = artist_pinyin
				else:
					details_dict['artist_pinyin'] = None
			else:
				pass
				# print "ELSE: ", span.text
				# colon_u = u'\uff1a' # ：
				# text = text.split(colon_u)
				# details_dict[text[0]] = text[1]					

	return details_dict

for product_id in products:
	"""Loops through product IDs in product ID array"""
	driver.get("http://world.tmall.com/item/%s.htm" % product_id)

	current_url = driver.current_url # if redirected to login page then break loop
	if 'login' in current_url:
		print('REDIRECTED TO LOGIN. LOOP BROKE AT: ', product_id)
		break

	# scroll some more
	print 'start counting up...'
	for isec in (.01, .1,.2,.3,.35,.4,.45,.5,.55, .6, .65, .7,.8,.9, 1):
		# print('isec: ', isec)
		driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight * %s);" % isec)
		sleep(0.4)
	print 'finished counting up'

	# Item still listed?
	try:
		is_sold_out = driver.find_element_by_id('J_Sold-out-recommend')
	except:
		is_sold_out = None

	if is_sold_out is not None:
		with open('sold_out.txt', 'a') as f:
			f.write(product_id + ', ')
		print 'SOLD OUT - product_id: ', product_id
		continue

	# get target content div
	content_div = driver.find_element_by_class_name('ke-post')
	# get list of product img urls
	img_urls_list = get_img_tags_src_attr(content_div)
	print('img_urls_list: ', img_urls_list)

	# gets product details (outputs unicode)
	product_general_details_dict = get_top_div_general_product_details(driver)
	if 'sku' not in product_general_details_dict: # sku sometimes not included in text
		product_general_details_dict['sku'] = None
	print('product_general_details_dict: ', product_general_details_dict)
	# gets more product details from description
	product_extra_details_dict = get_content_div_product_description_details(content_div)
	print('product_extra_details_dict: ', product_extra_details_dict)
		# scroll some more
	print 'start counting down...'
	for isec in (1.0, 0.9, 0.8, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3, 0.2, 0.1, 0.05, 0.03):
		# print('isec: ', isec)
		driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight * %s);" % isec)
		sleep(0.4)
	print 'finished counting down'

	# detect if product as variants
	variations = {}
	try:
		variations_ul = driver.find_element_by_class_name('J_TSaleProp')
		variation_lis = variations_ul.find_elements_by_tag_name('li')
		if variation_lis:
			print 'VARIANTS FOUND'
			variation_counter = 0
			for variation_li in variation_lis:
				variation_li.click() # click the variation to change variation dependent data
				# print 'contains special sku? ', driver.current_url
				variation_title_unicode = variation_li.get_attribute('title')
				variation_title_pinyin = pinyin.get(variation_title_unicode, format='strip').title()
				# print 'VARIANTS FOUND: clicked on ', variation_title_unicode
				variation_price, monthly_sell_count, postage_price, available_product_count = get_variant_depenedent_data(driver)
				# print product_price, monthly_sell_count, postage_price, available_product_count
				variations.update({
						variation_counter: {
							'variation_url': driver.current_url,
							'variation_title_unicode': variation_title_unicode,
							'variation_title_pinyin': variation_title_pinyin,
							'variation_price': variation_price,
							'monthly_sell_count': monthly_sell_count,
							'postage_price': postage_price,
							'available_product_count': available_product_count
						}
					})
				variation_counter += 1
				sleep(1)
			# for each variant get variant
	except:
		variation_price, monthly_sell_count, postage_price, available_product_count = get_variant_depenedent_data(driver)
		print 'NO VARIANTS FOUND'
		# print product_price, monthly_sell_count, postage_price, available_product_count
		variations.update({
				0: {
					'variation_url': driver.current_url,
					'variation_title_unicode': None,
					'variation_title_pinyin': None,					
					'variation_price': variation_price,
					'monthly_sell_count': monthly_sell_count,
					'postage_price': postage_price,
					'available_product_count': available_product_count
				}
			})	
	print 'VARIATIONS: ', variations
	page_title = driver.title
	print page_title
	print product_id
	print current_url

	engine = db_connect()
	session=sessionmaker(bind=engine)
	db=session()

	try:
		# # 1) create and save product
		product=Product(
			listing_id = int(product_id),
			url = current_url,
			page_title = page_title,
			product_type = product_extra_details_dict['dimension_variations'][0]['product_type'],
			origin_unicode = product_general_details_dict['origin_unicode'],
			origin_pinyin = product_general_details_dict['origin_pinyin'],
			name_unicode = product_extra_details_dict['name_unicode'],
			name_pinyin = product_extra_details_dict['name_pinyin'],
			artist_unicode = product_extra_details_dict['artist_unicode'],
			artist_pinyin = product_extra_details_dict['artist_pinyin'],
			created=datetime.datetime.now(),
			vendor_id=1
		)

		does_product_exist = db.query(Product).filter(Product.listing_id==int(product_id)).first()
		print 'does_product_exist?: ', does_product_exist
		if not does_product_exist:

			try:
			    db.add(product)
			    db.commit()
			except:
			    db.rollback()
			    db.close()
			    raise

		else:
			product = does_product_exist # If exists set to instance returned by query
			print 'product exists, print product: ', product

		if not does_product_exist: # if product doesnt exist save images

			for img_url in img_urls_list:
				product.images.append(InitialImage(url=img_url))

			try:
			    db.commit()
			except:
			    db.rollback()
			    db.close()
			    raise
		
		# 2) create variations and save to child table

		# Used to deal with dynamic material/dimension variations
		variations_amount = len(variations)
		material_variations_amount = len(product_extra_details_dict['material_variations'])
		dimension_variations_amount = len(product_extra_details_dict['dimension_variations'])
		total_variations = int(max(material_variations_amount, dimension_variations_amount, variations_amount))
		print ('total variations: ', total_variations, ' - material_variations_amount: ', material_variations_amount,
			' - dimension_variations_amount: ', dimension_variations_amount)
		if material_variations_amount > dimension_variations_amount:
			is_greater = 'material_variations'
			is_less = 'dimension_variations'
		elif dimension_variations_amount > material_variations_amount:
			is_greater = 'dimension_variations'
			is_less = 'material_variations'
		else:
			is_greater = 'same'
			is_less = 'same'

		print 'is_greater: ', is_greater, ' - is_less: ', is_less
		for idx in range(0, total_variations):
			current_variation = {}
			# if variation in dimension, not in material then use same material for both
			if is_greater == 'material_variations':
				# materials will change beacuse there are multiple variations so use idx
				current_variation['material_unicode'] = product_extra_details_dict['material_variations'][idx]['material_unicode']
				current_variation['material_pinyin'] = product_extra_details_dict['material_variations'][idx]['material_pinyin']
				# dimesnions won't change because there are no variations so use index 0 to keep same
				try:
					current_variation['spout_to_handle'] = product_extra_details_dict['dimension_variations'][0]['spout_to_handle']
				except KeyError:
					current_variation['spout_to_handle'] = None					
				try:
					current_variation['height'] = product_extra_details_dict['dimension_variations'][0]['height']
				except KeyError:
					current_variation['height'] = None
				try:
					current_variation['capacity'] = product_extra_details_dict['dimension_variations'][0]['capacity']
				except KeyError:
					current_variation['capacity'] = None
				try:
					current_variation['mouth_diameter'] = product_extra_details_dict['dimension_variations'][0]['mouth_diameter']
				except KeyError:
					current_variation['mouth_diameter'] = None
				try:
					current_variation['product_type'] = product_extra_details_dict['dimension_variations'][0]['product_type']
				except KeyError:
					current_variation['product_type'] = None

			elif is_greater == 'dimension_variations':
				# materials won't change because there are no variations so use index 0 to keep same
				current_variation['material_unicode'] = product_extra_details_dict['material_variations'][0]['material_unicode']
				current_variation['material_pinyin'] = product_extra_details_dict['material_variations'][0]['material_pinyin']
				# dimensions will change beacuse there are multiple variations so use idx
				try:
					current_variation['spout_to_handle'] = product_extra_details_dict['dimension_variations'][idx]['spout_to_handle']
				except KeyError:
					current_variation['spout_to_handle'] = None
				try:	
					current_variation['height'] = product_extra_details_dict['dimension_variations'][idx]['height']
				except KeyError:
					current_variation['height'] = None
				try:	
					current_variation['capacity'] = product_extra_details_dict['dimension_variations'][idx]['capacity']
				except KeyError:
					current_variation['capacity'] = None
				try:	
					current_variation['mouth_diameter'] = product_extra_details_dict['dimension_variations'][idx]['mouth_diameter']
				except KeyError:
					current_variation['mouth_diameter'] = None
				try:
					current_variation['product_type'] = product_extra_details_dict['dimension_variations'][idx]['product_type']
				except KeyError:
					current_variation['product_type'] = None

			elif is_greater == 'same' and is_less == 'same':
				try:
					current_variation['material_unicode'] = product_extra_details_dict['material_variations'][0]['material_unicode']
				except KeyError:
					current_variation['material_unicode'] = None					
				try:
					current_variation['material_pinyin'] = product_extra_details_dict['material_variations'][0]['material_pinyin']
				except KeyError:
					current_variation['material_pinyin'] = None						
				try:
					current_variation['spout_to_handle'] = product_extra_details_dict['dimension_variations'][0]['spout_to_handle']
				except KeyError:
					current_variation['spout_to_handle'] = None					
				try:
					current_variation['height'] = product_extra_details_dict['dimension_variations'][0]['height']
				except KeyError:
					current_variation['height'] = None
				try:
					current_variation['capacity'] = product_extra_details_dict['dimension_variations'][0]['capacity']
				except KeyError:
					current_variation['capacity'] = None
				try:
					current_variation['mouth_diameter'] = product_extra_details_dict['dimension_variations'][0]['mouth_diameter']
				except KeyError:
					current_variation['mouth_diameter'] = None
				try:
					current_variation['product_type'] = product_extra_details_dict['dimension_variations'][0]['product_type']
				except KeyError:
					current_variation['product_type'] = None

			else:
				print 'somethings broken with is_greater and is_less'
				break

			# if variation in material and not dimension then use same dimension for both
			if variations[idx]['variation_title_pinyin'] is not None:
				sku_internal = str(product_id) + '-' + variations[idx]['variation_title_pinyin']
				print 'sku_internal set w/ title: ', sku_internal
			else:
				sku_internal = str(product_id)
				print 'sku_internal set w/o title: ', sku_internal

			product_id_not_listing_id = product.id
			variation = Variation(
				url = variations[idx]['variation_url'],
				title_unicode = variations[idx]['variation_title_unicode'],
				title_pinyin = variations[idx]['variation_title_pinyin'],
				sku_external = product_general_details_dict['sku'],
				sku_internal = sku_internal,
				price = int(variations[idx]['variation_price']),
				monthly_sell_count = int(variations[idx]['monthly_sell_count']),
				local_postage = int(variations[idx]['postage_price']),
				inventory_count = int(variations[idx]['available_product_count']),
				material_unicode = current_variation['material_unicode'],
				material_pinyin = current_variation['material_pinyin'],
				capacity = current_variation['capacity'],
				height = current_variation['height'],
				# width=6,
				mouth_diameter = current_variation['mouth_diameter'],
				spout_to_handle = current_variation['spout_to_handle'],
				created = datetime.datetime.now(),
				product_id=product_id_not_listing_id
			)		

			try:
			    product.variations.append(variation)
			    db.commit()
			except Exception as e:
				print 'exception adding variation: ', e
				with open('var_db_exception.text', 'a') as f:
					f.write(sku_internal + ', ')
				db.rollback()
				db.close()
				raise


			try:
			    db.close()	# No more commites below, so close connection
			except:
				pass

			sleep(.4)

			to_path = os.path.join(PRODUCT_DIR, sku_internal)

			try:
				os.stat(to_path)	
				print 'exists: ', to_path
			except:
				os.mkdir(to_path)
				print 'created: ', to_path

			# screenshot
			print("Screenshotting...")
			driver.save_screenshot(os.path.join(to_path, "%s.png" % sku_internal))


			print 'finished with product sku: ', sku_internal
	except Exception as e:
		print 'from exception: ', e
		with open('problem_variations.txt', 'a') as f:
			f.write(product_id + ',\n')

	print 'finished with product: ', product_id

# driver.close()