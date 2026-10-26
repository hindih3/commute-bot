# commute-bot

Discord front end for [commute-planner](https://github.com/hindih3/commute-planner).
`/commute deadline: 9:00` (or `direction: home`) asks the planner for routes
starting the moment the command is sent and replies with the best three.

## Run

The planner server has to be running (it listens on `localhost:8080`).

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # then fill in DISCORD_BOT_TOKEN
.venv/bin/python bot.py
```

## Discord setup

Scopes `bot` + `applications.commands`, no bot permissions, no privileged
intents. With User Install enabled, `/commute` also works in DMs.
