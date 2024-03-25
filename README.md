This Automation uses Selenium framework to test the functioning of the Live Streams in LiveReach App.


### Instructions to run
* Set up `.env` file

```
DEFAULT_ACCOUNT_PASSWORD="ACCOUNT_PASSWORD_HERE"
SLACK_OAUTH_TOKEN="SLACK_TOKEN_HERE"
MYSQL_HOST="mysql.infra.livereachmedia.com"
MYSQL_USER=livereachmedia
MYSQL_PASSWORD=
MYSQL_DB=adxprismDb
ORGS=523, 514
SLACK_CHANNEL="live-streams-check"
```

* To Add orgs to this Automation - Append the organization ids to `ORGS` in `.env` file

* To update reporting slack channel, modify `SLACK_CHANNEL` in `.env`

* Running with Docker compose
```
# Build image and start container
docker compose up --build -d

# view live logs
docker compose logs --follow 

# stop the container
docker compose stop

# start container
docker compose start
```