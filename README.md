# mindcrawler

It's a simple crawler that crawls the web and stores the results in a Redis datastore.

Flow:

1. Post the seed url with `/create` endpoint
2. Write the seed url to a hash in Redis
3. Publish message the seed url to a channel named `crawling-channel`
4. The workers subscribe to the channel and start crawling the urls
5. Crawling the urls and storing title and description metadata in Redis
6. Get the result with `/review` endpoint

Assumptions:

- The seed url is a valid url
- Only domain of the seed url is crawled, incl. subdomains (e.g. `https://amazon.com` and `https://aws.amazon.com`)
- No crawling for the seed url's path
- The seed url is crawled only once
- If the seed url is crawled again, the result is updated (overwrited)