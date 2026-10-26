# commute-bot

Discord front end for [commute-planner](https://github.com/hindih3/commute-planner).
`/commute deadline: 9:00` (or `direction: home`) asks the planner for routes
starting the moment the command is sent and replies with the best three.

## Run

The planner server has to be running (it listens on `localhost:8080`).

```bash
.venv/bin/python bot.py
```

First-time setup on a new machine (skip if `.venv` and `.env` already exist,
since copying the example over an existing `.env` erases the token):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp -n .env.example .env   # -n: never overwrite; then fill in DISCORD_BOT_TOKEN
```

## Discord setup

Scopes `bot` + `applications.commands`, no bot permissions, no privileged
intents. With User Install enabled, `/commute` also works in DMs.
