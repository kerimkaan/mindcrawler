docker rm -f mindcrawler
docker rm -f mindcrawler-worker
docker image rm mindcrawler:latest
docker image rm mindcrawler-worker:latest
docker build -t mindcrawler:latest -f Dockerfile .
docker build -t mindcrawler:worker -f Dockerfile-Worker .
docker run -d --expose 3000 -p 3000:3000 --name mindcrawler mindcrawler:latest
docker run -d --name mindcrawler-worker mindcrawler:worker
