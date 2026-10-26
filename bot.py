"""Discord front end for commute-planner.

/commute takes a deadline (and optionally "home"), asks the planner server for
plans starting at the moment the command was sent, and replies with the best few.
"""
import asyncio
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import aiohttp
import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ["DISCORD_BOT_TOKEN"]
PLANNER_URL = os.environ.get("PLANNER_URL", "http://localhost:8080")
CHICAGO = ZoneInfo("America/Chicago")
MAX_PLANS = 3

client = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(client)


def parse_time(text: str) -> str | None:
    """'9:00', '09:00', '17:25', '5:25pm', '9am' -> 'HH:MM' (what the planner expects)."""
    cleaned = text.strip().lower().replace(" ", "")
    for fmt in ("%H:%M", "%I:%M%p", "%I%p"):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%H:%M")
        except ValueError:
            pass
    return None


def minutes(t: str) -> int:
    hours, mins = map(int, t[:5].split(":"))
    return hours * 60 + mins


def label(plan: dict) -> str:
    """'walk', '157 bus', 'Blue Line + 8 bus'."""
    rides = [f"{s['line']} Line" if s["mode"] == "TRAIN" else f"{s['line']} bus"
             for s in (leg["segment"] for leg in plan["legs"]) if s["transit"]]
    return " + ".join(rides) or "walk"


def format_plans(plans: list[dict], start: str, deadline: str, commute: str) -> str:
    where = "Union Station" if commute == "TO_UNION" else "campus"
    if not plans:
        return f"No route gets you to {where} by {deadline} leaving at {start}."

    lines = [f"Leaving {start}, to {where} by {deadline}:"]
    for i, plan in enumerate(plans[:MAX_PLANS], 1):
        lines.append(f"\n**{i}. Arrive {plan['arrival'][:5]}** ({label(plan)})")
        previous_arrival = None
        for leg in plan["legs"]:
            if leg["segment"]["minutes"] == 0:
                continue  # "Leave class" is just the starting point
            wait = minutes(leg["departs"]) - minutes(previous_arrival) if previous_arrival else 0
            note = f"  _(wait {wait} min)_" if wait > 0 else ""
            lines.append(f"`{leg['departs'][:5]}` {leg['segment']['description']}{note}")
            previous_arrival = leg["arrives"]
    return "\n".join(lines)


@tree.command(description="Commute options leaving now")
@app_commands.describe(deadline="When you need to be there, e.g. 9:00 or 5:25pm",
                       direction="away = to campus (default), home = to Union Station")
@app_commands.choices(direction=[app_commands.Choice(name="away", value="TO_CAMPUS"),
                                 app_commands.Choice(name="home", value="TO_UNION")])
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def commute(interaction: discord.Interaction, deadline: str,
                  direction: app_commands.Choice[str] | None = None):
    end = parse_time(deadline)
    if end is None:
        await interaction.response.send_message(
            f"Couldn't read `{deadline}` as a time. Try `9:00`, `17:25` or `5:25pm`.", ephemeral=True)
        return

    # The moment the command was sent is the trip's start (Discord gives it in UTC)
    start = interaction.created_at.astimezone(CHICAGO).strftime("%H:%M")
    commute_value = direction.value if direction else "TO_CAMPUS"

    # Discord wants an answer within 3 seconds; live CTA lookups can take longer
    await interaction.response.defer(thinking=True)
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as http:
            async with http.get(f"{PLANNER_URL}/plans",
                                params={"start": start, "deadline": end, "commute": commute_value}) as response:
                response.raise_for_status()
                plans = await response.json()
    except (aiohttp.ClientError, asyncio.TimeoutError):
        await interaction.followup.send("The planner server isn't answering. Is it running?")
        return

    await interaction.followup.send(format_plans(plans, start, end, commute_value))


@client.event
async def on_ready():
    synced = await tree.sync()  # register /commute with Discord
    print(f"Logged in as {client.user}; commands: {[c.name for c in synced]}")


if __name__ == "__main__":
    client.run(TOKEN)
