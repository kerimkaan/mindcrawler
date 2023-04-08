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

app = Flask(__name__)

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return f'User {escape(username)}'


@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return f'Post {post_id}'


@app.route('/path/<path:subpath>')
def show_subpath(subpath):
    # show the subpath after /path/
    return f'Subpath {escape(subpath)}'


@app.route("/")
def index():
    return "<p>Hello, World!</p>"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return f'You are in POST method'
    else:
        return f'You are in GET method'


@app.route("/me", methods=["GET"])
def me_api():
    print(r.get('foo'))
    user = {
        "username": "John",
        "theme": "dark",
        "image": "https://example.com/john.png"
    }
    return {
        "user": user["username"],
        "theme": user["theme"],
        "image": user["image"]
    }


@app.route('/create', methods=['POST'])
def createLink():
    if (not request.is_json):
        return {
            "message": "Missing JSON in request",
            "success": True
        }, 400
    try:
        data = request.get_json()
        url = urlparse(data['url'])
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
            "success": False,
            "url": data['url']
        }
    except Exception as e:
        return {
            "message": "Something went wrong",
            "success": False,
            "error": str(e)
        }, 500

@app.route('/result', methods=['GET'])
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
    app.run(debug=os.getenv('DEBUG'), host=os.getenv('HOST'), port=os.getenv('PORT'))

