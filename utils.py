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
	resp = requests.get(url)
	while resp.status_code!=200:
		time.sleep(60)
		resp = requests.get(url)
	profile = html.fromstring(resp.text)
	info = profile.xpath('.//div[@class="container member-info-container full-width"]')[0]
	projects = info.xpath('.//div[@class="memStats-container "]')[0]
	main_info = info.xpath('.//div[@class="sidebar-box clearfix"]')[0]
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
	if len(projects.xpath('.//a[contains(@title, "go to page ")]')) > 0:
		nb_projects_pages = projects.xpath('.//a[contains(@title, "go to page ")]')[-1].text_content()
	else:
		nb_projects_pages = 1
	return int(nb_projects_pages)

def get_gender(profile_url: str) -> str:
	reviews = []
	nb_pages = get_nb_projects_pages(profile_url)
	nb_pages = min(nb_pages, 10) # it is too long to scrape all pages, so we limit to 10 pages max
	for page in range(1,nb_pages+1):
		resp = requests.get(profile_url+'?Projects_page={}'.format(page))
		while resp.status_code != 200:
			time.sleep(60)
			resp = requests.get(profile_url)
		profile = html.fromstring(resp.text)
		info = profile.xpath('.//div[@class="container member-info-container full-width"]')[0]
		reviews_container = info.xpath('.//div[@class="project-list-feedback"]')
		if len(reviews_container) > 0:
			for full_review in reviews_container:
				if len(full_review.xpath('.//div[@class="col-xs-10 right-col"]')) > 0:
					review = full_review.xpath('.//div[@class="col-xs-10 right-col"]')[0].xpath('.//p')[0].text_content()
					reviews.append(review) 
	if len(reviews) > 0:
		gender = guess_gender_from_reviews(reviews)
	else:
		gender = None
	return gender
		
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
	