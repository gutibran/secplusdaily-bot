import sys
import time
from datetime import datetime, timezone
import os
import uuid
import base64
import random
import json
import requests
from dotenv import load_dotenv
import tweepy

def get_environment_variables():
    # load environement variables
    load_dotenv()
    bearer_token = os.environ.get("BEARER_TOKEN")
    consumer_key = os.environ.get("API_KEY")
    consumer_secret = os.environ.get("API_KEY_SECRET")
    access_token = os.environ.get("ACCESS_TOKEN")
    access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")

    # return an object holding the environment variables
    return {
        bearer_token,
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret
    }

def download_data():
    """Download the data that represents the questions and answers from GitHub."""
    return requests.get("https://raw.githubusercontent.com/gutibran/data/main/text/books/comptia_security_practice_tests/json/data.json").json()

def choose_random_domain_objective(data): 
    """Choose a random domain objective."""
    domain_objectives = list(data.keys())
    return domain_objectives[random.randint(0, len(domain_objectives) - 1)]
    
def choose_random_domain_objective_question(data, domain_objective):
    """Choose a random domain objective question."""
    return data[domain_objective][random.randint(0, len(data[domain_objective]) - 1)]

def initialize_analytics_data():
    """Create a the analytics file if it does not exist and return its data. Otherwise create the analytics file and return the initialized data."""
    try:
        with open("./analytics_file.json", "r") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        with open("./analytics_file.json", "w") as json_file:
            json_file.write({}, json_file)
            return {
                "interval": 0,
                "active_questions": [],
            }

def send_poll_tweet(question):
    """Send poll tweet on @secplusdaily account."""
    # grab environment variables
    environement_variables = get_environment_variables()

    # set up twitter v1 api with tweepy
    authorization = tweepy.OAuthHandler(environement_variables["consumer_key"], environement_variables["consumer_secret"])
    authorization.set_access_token(environement_variables["access_token"], environement_variables["access_token_secret"])
    api = tweepy.API(authorization, wait_on_rate_limit=True)

    # set up twitter v2 api with tweepy
    client = tweepy.Client(
        environement_variables["bearer_token"],
        environement_variables["consumer_key"],
        environement_variables["consumer_secret"],
        environement_variables["access_token"],
        environement_variables["access_token_secret"],
        wait_on_rate_limit=True
    )

    # unpack the data within the randomly selected question
    domain_objective = question["domain_objective"].title()
    question_id = question["question_id"]
    question_text = question["question_text"]
    question.insert(0, f"{domain_objective} Question:\n")
    question_image = None
    question_image_media_id = None
    a = question["choice_a"]
    b = question["choice_b"]
    c = question["choice_c"]
    d = question["choice_d"]
    tweet_id = None
    # check if the question contains an image
    if question.get("question_image"):
        # decode the base64 string into an image
        question_image_data = base64.b64decode(question["question_image"])
        question_image_media_id = api.media_upload(filename=f"{domain_objective}_question_{question_id}.png", file=question_image_data)
        tweet_id = client.create_tweet(text=question_text, media_ids=[question_image_media_id], poll_options=[a, b, c, d], poll_duration_minutes=120)
    else:
        tweet_id = client.create_tweet(text=question_text, poll_options=[a, b, c, d], poll_duration_minutes=120)
    return tweet_id 

def main():
    # download most recent data from the github repo
    data = download_data()

    # read in analytics data
    analytics_data = initialize_analytics_data()
    
    # choose a random domain objective
    domain_objective = choose_random_domain_objective(data)
    
    # choose random domain objective question
    question = None

    # check if the current tweet interval is over
    if len(analytics_data["active_questions"]) == 1005:
        analytics_data["interval"] += 1
        analytics_data["active_questions"] = []

    # ensure that the question has not already been posted
    # keep picking questions till one that has not been posted is found
    while True:
        question = choose_random_domain_objective_question(data, domain_objective)
        if question["question_id"] in analytics_data["active_questions"]:
            continue
        else:
            break

    # send the tweet
    tweet_id = send_poll_tweet(question)
    dt = datetime.now()
    ts = datetime.timestamp(dt)
    time_ = datetime.fromtimestamp(ts, tz=timezone.utc)

    # store tweet id
    for item in data[domain_objective]:
        if item["question_id"] == question["question_id"]:
            item["tweet_ids"].append({
                "tweet_id": tweet_id,
                "time": time_,
                "reply_tweet_id": ""
            })
    
    # sleep for 2 hours
    time.sleep(120 * 60) 

    # load environement variables
    load_dotenv()
    bearer_token = os.environ.get("BEARER_TOKEN")
    consumer_key = os.environ.get("API_KEY")
    consumer_secret = os.environ.get("API_KEY_SECRET")
    access_token = os.environ.get("ACCESS_TOKEN")
    access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")

    # v2
    client = tweepy.Client(
        bearer_token,
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret,
        wait_on_rate_limit=True
    )

    # reply to the tweet
    reply_id = client.create_tweet(text=f"{question["answer_letter"]}: {question["answer_text"]}", in_reply_to_tweet_id=tweet_id)

    # save the reply_id of the reply tweet
    # i know this can be made more efficient just getting ideas out
    for item in data[domain_objective]:
        if item["question_id"] == question["question_id"]:
            for tweet in item["tweet_ids"]:
                if tweet["tweet_id"] == tweet_id:
                    tweet_id["tweet_id"]["reply_tweet_id"] = reply_id