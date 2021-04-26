import numpy as np
import requests
import pandas as pd
from lxml import html
import re
import time

full_profile = 'https://www.peopleperhour.com/freelancer/design/maria-experienced-team-of-graphic-wjawjq'
incomplete_profile = 'https://www.peopleperhour.com/freelancer/writing-translation/lupin-vivian-proofreader-editor-and-artist-qvxnxmm'

def guess_gender(rev: list) -> str:
    """
    Determine gender of a person with a list of reviews
    """
    genders = ['male', 'female']
    gender = None
    nb_male, nb_female = 0, 0
    male = ["he", "his", "him", "himself"]
    female = ["she", "her", "hers", "herself"]

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

def profile_info(url: str) -> dict:
	"""
	Collect all information available on the webpage of the freelancer
	"""
	reviews = []
	resp = requests.get(url)
	if resp.status_code!=200:
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
		gender = guess_gender(reviews)
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
	
profile_info('https://www.peopleperhour.com/freelancer/writing-translation/translate_guru-expert-translation-spanish-french-wymjjm')

# Is it necessary to have all the reviews of the freelancer, or just the one that appears on the first page are enough?
def profile_reviews(url: str) -> list:
	resp = requests.get(url)
	profile = html.fromstring(resp.text)
	reviews = profile.xpath('//div[@class="reviews col-xs-12 col-sm-10 col-sm-push-1 col-md-12 col-md-push-0 listing clearfix"]')
	if len(reviews.xpath('.//span[@class="empty"')) > 0:
		return None
	else:
		
		gender = guess_gender(review_list)
		return gender