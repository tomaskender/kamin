# pull official base image
FROM python:3.10.7-slim-buster

WORKDIR /kamin-web

# install dependencies
ADD ./requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ADD . .

# launch
ENTRYPOINT ["streamlit", "run", "app.py"]
