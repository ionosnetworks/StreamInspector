FROM python:3.11

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/`curl -sS https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE`/linux64/chromedriver-linux64.zip
RUN unzip -j /tmp/chromedriver.zip -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

COPY ./app /app
# upgrade pip
RUN pip install --upgrade pip

# install selenium
RUN pip3 install selenium polling2 webdriver-manager slack_sdk PyMySQL

CMD ["python", "/app/app.py"]

