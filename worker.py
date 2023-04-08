# encoding:utf-8
import os
import redis
import requests
import logging
import time
from datetime import datetime
import random
from dotenv import load_dotenv
from urllib.parse import urlparse
from bs4 import BeautifulSoup

load_dotenv()  # Load .env file

r = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    password=os.getenv('REDIS_PASSWORD')
)

def isExistInRedis (key):
    if r.exists(key):
        return True
    else:
        return False

def getUrlFromRedis (url):
    hash = r.hmget(url, {'url', 'scheme'})
    if hash:
        return hash
    return False

def updateHashInRedis (hashName, key, value):
    r.hset(hashName, key, value)

def createMetadataInRedis (hashName, title = '', description = '', httpStatusCode = 0, duration = 0):
    r.hset(
        hashName, 
        key = None, 
        value = None, 
        mapping = 
            {
                'title': title,
                'description': description,
                'httpStatusCode': httpStatusCode,
                'crawlingTime': datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
                'took': duration
            }
    )

def getMetadataFromUrl (url):
    response = requests.get(url)
    httpStatusCode = response.status_code
    soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
    title = soup.title.string
    description = soup.find('meta', {'name': 'description'})
    if description:
        description = description['content']
    return title, description, httpStatusCode

def worker():
    s = r.pubsub()
    s.subscribe('crawling-channel')
    queue = s.listen()
    for msg in queue:
        logging.info('New message from channel: ', msg['data'])
        if msg['data'] == 1:
            print('Channel is empty')
            logging.info('Channel is empty')
            continue
        data = msg['data'].decode('utf-8')
        if data == '1':
            print('Channel is empty')
        else:
            hashName = 'metadata:' + data
            logging.info('Hash name: ', hashName)
            sleepTime = round(random.uniform(0.0, 3.5), 2)
            print('Sleeping for: ', sleepTime)
            time.sleep(sleepTime)
            if isExistInRedis(hashName):
                print('Metadata already exist')
                continue
            t0 = time.time()
            metadata = getMetadataFromUrl(data)
            t1 = time.time()
            print('Time to get metadata: ', t1 - t0)
            duration = round(t1 - t0, 3)
            print(metadata)
            title = metadata[0] if metadata[0] else ''
            description = metadata[1] if metadata[1] else ''
            httpStatusCode = metadata[2] if metadata[2] else 0
            updateHashInRedis("url:" + urlparse(data)[1], 'processed', 1)
            createMetadataInRedis(hashName, title, description, httpStatusCode, duration)


while True:
    worker()
