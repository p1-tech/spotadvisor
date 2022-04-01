FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD [ "python", "./spotadvisor.py", "--maxintcode", "2", "--mincpus", "48", "--region=us-west-2", "--intelonly", "--format", "json" ]
