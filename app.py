from flask import Flask
from markupsafe import escape
from flask import request
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
import redis

load_dotenv()  # Load .env file

r = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    password=os.getenv('REDIS_PASSWORD')
)

def appFactory():
    app = Flask(__name__)
    return app

factory = appFactory()

@factory.route("/")
def index():
    return "<p>Hello, World!</p>"


@factory.route('/create', methods=['POST'])
def createLink():
    if (not request.is_json or request.get_json() == {} or type(request.get_json()) == None):
        return {
            "message": "Missing JSON in request",
            "success": False
        }, 400
    try:
        data = request.get_json()
        url = urlparse(data['url'])
        if (url[0] == "" or url[1] == ""): # If scheme or url is empty, return error
            return {
                "message": "Scheme or url is missing, you can add it to your link like https://google.com",
                "success": False,
                "url": data['url']
            }, 400
        print(url)
        # We need full URL like https://google.com
        message = url[0] + '://' + url[1]
        existInRedis = r.exists("url:"+url[1])
        if (existInRedis):
            isProcessed = r.hget("url:"+url[1], "processed")
            if (isProcessed == b'0'):
                r.publish('crawling-channel', message) # re-publish message to crawling-channel for crawling
                return {
                    "message": "Link is processing",
                    "success": False,
                    "url": data['url']
                }, 202
            return {
                "message": "Link already exist",
                "success": False,
                "url": data['url']
            }, 409
        r.hset("url:"+url[1], key=None, value=None, mapping={"scheme": url[0], "url": url[1], "path": url[2], "processed": 0})  # Create a new hash in redis
        # Publish message to crawling-channel for crawling
        r.publish('crawling-channel', message)
        return {
            "message": "Link created successfully",
            "success": True,
            "url": data['url']
        }
    except Exception as e:
        return {
            "message": "Something went wrong",
            "success": False,
            "error": str(e)
        }, 500

@factory.route('/result', methods=['GET'])
def getResult():
    url = request.args.get('url')
    if (url == "" or url == None):
        return {
            "message": "Missing URL in request",
            "success": False
        }, 400
    url = urlparse(url)
    existInRedis = r.exists("url:"+url[1])
    print(existInRedis)
    if (not existInRedis):
        return {
            "message": "Link not found",
            "success": False
        }, 404
    fullUrl = url[0] + "://" + url[1]
    hashName = "metadata:" + fullUrl
    try:
        hash = r.hgetall(hashName)
        if (hash == {}):
            return {
                "message": "Metadata not found",
                "success": False
            }, 404
    except:
        return {
            "message": "Metadata can not get",
            "success": False
        }, 500
    return {
        "message": "Link found",
        "success": True,
        "result": {
            "url": fullUrl,
            "title": hash[b'title'].decode('utf-8'),
            "description": hash[b'description'].decode('utf-8'),
            "status": int(hash[b'httpStatusCode'].decode('utf-8')),
            "createdAt": hash[b'crawlingTime'].decode('utf-8'),
            "took": float(hash[b'took'].decode('utf-8')),
        }
    }, 200

if __name__ == "__main__":
    factory.run(debug=os.getenv('DEBUG'), host=os.getenv('HOST'), port=os.getenv('PORT'))

