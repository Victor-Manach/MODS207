import numpy as np
import requests
import pandas as pd
from lxml import html
import re
import time
import json
import urllib

full_profile = 'https://www.peopleperhour.com/freelancer/design/maria-experienced-team-of-graphic-wjawjq'
incomplete_profile = 'https://www.peopleperhour.com/freelancer/writing-translation/lupin-vivian-proofreader-editor-and-artist-qvxnxmm'

def guess_gender_from_reviews(rev: list) -> str:
    """
    Determine the gender of a person with a list of reviews
    """
    genders = ['male', 'female']
    gender = None
    nb_male, nb_female = 0, 0
    male = ["he", "his", "him", "himself"]
    female = ["she", "her", "hers", "herself"]
	# We start by using the reviews to determine the gender of the person
    for r in rev:
        for word in male:
            if re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search(r) is not None:
                nb_male+=1
        for word in female : 
            if re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search(r) is not None:
                nb_female+=1
    if nb_male !=0 or nb_female!=0:
        prob_male, prob_female = nb_male/(nb_male+nb_female), nb_female/(nb_male+nb_female)
        if prob_male!=prob_female:
            gender = genders[np.argmax([prob_male, prob_female])]
    return gender

def guess_gender_from_name(name: str) -> str:
	"""
	Determine the gender of a person with the name (we use a database with a list of names and the corresponding gender)
	"""
	name = name.capitalize()
	nb_male, nb_female = 0, 0
	gender = None
	genders = ['male', 'female']
	# the first query is to get the number of occurrences of the name in the database
	where = urllib.parse.quote_plus("""
	{
		"Name": "%s"
	}
	""" % name)
	url_count = 'https://parseapi.back4app.com/classes/Listofnames_Complete_List_Names?count=1&limit=0&where=%s' % where
	headers = {
		'X-Parse-Application-Id': '9Ly08smbo3R4nkHLl3dJCutvCWd9QA1wJAesk8MR', # This is your app's application id
		'X-Parse-REST-API-Key': 'DwR8KujtRPBvdFIIs6vEFRtSkZYXjDRzXuHAvVdQ' # This is your app's REST API key
	}
	names_count = json.loads(requests.get(url_count, headers=headers).content.decode('utf-8')) # Here you have the data that you need
	nb_names = names_count['count']
	if nb_names != 0:
		# the second query is to get the gender associated to each result, only if there are matching names in the database
		url_names = 'https://parseapi.back4app.com/classes/Listofnames_Complete_List_Names?count=1&limit=%s&where=%s' % (str(nb_names), where)
		data = json.loads(requests.get(url_names, headers=headers).content.decode('utf-8'))
		results = data['results']
		for res in results:
			if res['Gender'] == 'male':
				nb_male += 1
		prob_male = nb_male/nb_names
		gender = genders[np.argmax([prob_male, 1-prob_male])]
	return gender

def profile_info(url: str) -> dict:
	"""
	Collect all information available on the webpage of the freelancer
	"""
	reviews = []
	resp = requests.get(url)
	while resp.status_code!=200:
		time.sleep(60)
		resp = requests.get(url)
	profile = html.fromstring(resp.text)
	info = profile.xpath('.//div[@class="container member-info-container full-width"]')[0]
	projects = info.xpath('.//div[@class="memStats-container "]')[0]
	main_info = info.xpath('.//div[@class="sidebar-box clearfix"]')[0]
	reviews_container = info.xpath('.//div[@class="project-list-feedback"]')
	name = main_info.xpath('.//div[@class="details "]')[0].xpath('.//h1')[0].text_content().strip()
	location = main_info.xpath('.//div[@class="member-location"]')[0].text_content().strip()
	languages = main_info.xpath('.//div[@class="member-languages clearfix"]')[0].text_content().strip()
	if len(main_info.xpath('.//span[@class="js-about-full-text"]')) > 0:
		description = main_info.xpath('.//span[@class="js-about-full-text"]')[0].text_content().strip()
	else:
		description = ''
	if len(main_info.xpath('.//div[@class="total-rating"]')) > 0:
		rating = float(main_info.xpath('.//div[@class="total-rating"]')[0].text_content().strip())
	else:
		rating = 0.
	if len(main_info.xpath('.//div[@class="total-reviews"]')) > 0:
		nb_reviews = main_info.xpath('.//div[@class="total-reviews"]')[0].text_content().strip()
		if len(nb_reviews) > 2:
			nb_reviews = int(nb_reviews[1:-1])
		else:
			nb_reviews = int(nb_reviews)
	else:
		nb_reviews = 0
	price = main_info.xpath('.//span[@class="member-cost"]')[0].xpath('.//div')[0].text_content().strip()
	skills = [skill.text_content() for skill in main_info.xpath('.//a[@class="tag-item small"]')]
	
	if len(main_info.xpath('.//div[@class="clearfix industry-expertise-list skills-item"]')) > 0:
		expertise = main_info.xpath('.//div[@class="clearfix industry-expertise-list skills-item"]')[0].text_content().strip()
	else:
		expertise = ''
	nb_projects = int(projects.xpath('.//div[@class="memberStats-item memberStats-rating"]')[0].xpath('.//div[@class="insights-value"]')[0].text_content().strip())
	nb_buyers = int(projects.xpath('.//div[@class="memberStats-item u-mgb--1"]')[0].xpath('.//div[@class="insights-value"]')[0].text_content().strip())
	last_active = projects.xpath('.//div[@class="memberStats-item item-margin"]')[0].xpath('.//div[@class="insights-value"]')[0].text_content().strip()
	
	if len(reviews_container) > 0:
		for full_review in reviews_container:
			if len(full_review.xpath('.//div[@class="col-xs-10 right-col"]')) > 0:
				review = full_review.xpath('.//div[@class="col-xs-10 right-col"]')[0].xpath('.//p')[0].text_content()
				reviews.append(review)
		gender = guess_gender_from_reviews(reviews)
	else:
		gender = None
	info = {
		'name': name,
		'location': location,
		'languages': languages,
		'description': description,
		'rating': rating,
		'nb_reviews': nb_reviews,
		'price': price,
		'skills': skills,
		'expertise': expertise,
		'nb_projects': nb_projects,
		'nb_buyers': nb_buyers,
		'last_active': last_active,
		'gender': gender
	}
	return info

def get_nb_projects_pages(profile_url: str) -> int:
	resp = requests.get(profile_url)
	while resp.status_code != 200:
		time.sleep(60)
		resp = requests.get(profile_url)
	
	projects = html.fromstring(resp.text)
	nb_projects_pages = projects.xpath('.//a[contains(@title, "go to page ")]')[-1].text_content()
	
	return int(nb_projects_pages)

def get_projects_id(profile_url: str, projects_page: int) -> list:
	id_list = []
	profile_url += '?Projects_page={}'.format(projects_page)
	resp = requests.get(profile_url)
	while resp.status_code != 200:
		time.sleep(60)
		resp = requests.get(profile_url)
	
	projects = html.fromstring(resp.text)
	projects_ids = projects.xpath('.//div[@class="keys"]')[0].xpath('.//span')
	for project_id in projects_ids:
		id_list.append(int(project_id.text_content()))
	
	return id_list


def get_all_reviews(profile_url: str) -> str:
	nb_projects_pages = get_nb_projects_pages(profile_url)
	project_ids = {}
	for i in range(1,nb_projects_pages+1):
		project_ids['{}'.format(i)] = get_projects_id(profile_url, i)
		if i%10==0:
			print(str(i)+' pages checked for the project ids')
	print(project_ids)
	reviews_dict, reviews_list = {}, []
	cookies = {
    	'_ga_7KBXBWQ5QT': 'GS1.1.1620422045.2.1.1620423884.60',
    	'_ga': 'GA1.2.1664462320.1620077339',
    	'_gid': 'GA1.2.1255311243.1620422047',
    	'_uetsid': '28484f00af7911ebbd2dd9d9b74b9c95',
    	'_uetvid': '25d97cc09e2b11ebbce54387f8524914',
    	'PHPSESSID': '121a79acac4a174e42d4a61cf4126be3',
    	'YII_CSRF_TOKEN': 'bXFvY1dKbWtCejFPTkRlN210SmZFN2ZTbEk2R3h4NTfPzFVHVguGmY5RzU-YDV7fa2yXqfaJ4qtkrO4ir9zs4A',
    	'connect.sid': 's%3AugbmU4a_aaetn78tHOhXoDenzLY0Y4aP.a%2F1C6iaa6bFOGzD%2BwdQkUwSJXKua%2BQt%2BnSqh%2FzJ5hjQ',
    	'_gcl_au': '1.1.89486104.1620077339',
    	'api': '6bb881afc885f120138a6f7b73d85d90c80be4b5YTo0OntpOjA7aTo1NzYwODc3O2k6MTtzOjU6IjBiOGZmIjtpOjI7aTo4NjQwMDAwO2k6MzthOjA6e319',
    	'mid': '1618519355022490900792955',
	}
	headers = {
    	'Accept': '*/*',
    	'Connection': 'keep-alive',
    	'Accept-Language': 'en-us',
    	'Host': 'www.peopleperhour.com',
    	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15',
    	'Referer': profile_url,
    	'Accept-Encoding': 'gzip, deflate, br',
    	'X-Requested-With': 'XMLHttpRequest',
    	'sentry-trace': '0a33dbde2a7548258e8a74c8069e280b-99131d7007beb685-0',
	}
	for page_nb,project_id in project_ids.items():
		for ids in project_id:
			params = (
				('Projects_page', page_nb),
				('ajax', 'activity-list'),
				('fPageH{}'.format(ids), str(1000)),
			)
			resp = requests.get(profile_url, headers=headers, params=params, cookies=cookies)
			while resp.status_code != 200:
				time.sleep(60)
				resp = requests.get(profile_url, headers=headers, params=params, cookies=cookies)
			reviews = html.fromstring(resp.text)
			hidden_reviews = reviews.xpath('.//p')
			for review in hidden_reviews:
				reviews_list.append(review.text_content())
			reviews_dict['{}'.format(ids)] = reviews_list
		if int(page_nb)%10==0:
			print(str(page_nb)+' pages scrape for the reviews over '+str(nb_projects_pages))
	print(len(reviews_dict))
	print(reviews_dict)

get_all_reviews('https://www.peopleperhour.com/freelancer/design/maria-experienced-team-of-graphic-wjawjq')


def get_exchange_rates(currencies: list, date: str) -> dict:
	"""
	Determine the exchange rate between the base currency and USD on the specified date
	The date must be of the format YYYY-MM-DD
	"""
	exchange_rates = {}
	for base in currencies:
		url = 'https://api.ratesapi.io/api/' + date + "?base=" + base + "&symbols=USD"
		r=requests.get(url)
		while r.status_code != 200:
			time.sleep(60)
			r=requests.get(url)
		exchange_dict = r.json()
		exchange_rate = exchange_dict['rates']['USD']
		exchange_rates[base] = exchange_rate
	return exchange_rates
	