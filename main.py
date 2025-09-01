# This is a sample Python script.
from dotenv import load_dotenv
import os
import requests
import discord
from discord.ext import commands

# seems to be both 'daily_grind_chance' and 'daily_grind_guaranteed'
# 3956025454 is the "bonus engrams" item hash

load_dotenv()

# BUNGIE
API_KEY = os.getenv("BUNGIE_API_KEY")
MEMBERSHIP_ID = os.getenv("MEMBERSHIP_ID")
MEMBERSHIP_TYPE = os.getenv("MEMBERSHIP_TYPE")

# DISCORD
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("DISCORD_CHANNEL_IDS", "").split(",") if cid.strip()]

REQUEST_HEADERS = {"X-API-Key": API_KEY}
BASE = "https://www.bungie.net"
MANIFEST_URL = "/Platform/Destiny2/Manifest/"
PROFILE_URL = f"/Platform/Destiny2/{MEMBERSHIP_TYPE}/Profile/{MEMBERSHIP_ID}/"

CLASS_ITEMS = ["Titan Mark", "Hunter Cloak", "Warlock Bond"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def request_manifest(args):
    request_url = ""
    for arg in args:
        request_url += arg
    try:
        response = requests.get(request_url, headers=REQUEST_HEADERS, timeout=10)
        response.raise_for_status()
        response_data = response.json()
    except requests.exceptions.Timeout:
        return "⏳ Bungie API timed out requesting manifest. Try again later."
    except requests.exceptions.RequestException as e:
        return f"⚠️ API error during manifest request: {e}"

    return response_data


def request_activity_hashes(manifest, args):
    request_url = ""
    for arg in args:
        request_url += arg

    request_url += manifest["Response"]["jsonWorldComponentContentPaths"]["en"]["DestinyActivityDefinition"]
    try:
        response = requests.get(request_url, headers=REQUEST_HEADERS, timeout=10)
        response.raise_for_status()
        activity_hashes = response.json()
    except requests.exceptions.Timeout:
        return "⏳ Bungie API timed out during activity hash request. Try again later."
    except requests.exceptions.RequestException as e:
        return f"⚠️ API error during activity hash request: {e}"
    return activity_hashes


def request_item_hashes(manifest, args):
    request_url = ""
    for arg in args:
        request_url += arg

    request_url += manifest["Response"]["jsonWorldComponentContentPaths"]["en"]["DestinyInventoryItemDefinition"]
    try:
        response = requests.get(request_url, headers=REQUEST_HEADERS)
        response.raise_for_status()
        item_hashes = response.json()
    except requests.exceptions.Timeout:
        return "⏳ Bungie API timed out during item hash request. Try again later."
    except requests.exceptions.RequestException as e:
        return f"⚠️ API error during item hash request: {e}"
    return item_hashes


def get_profile_activities():
    params = {
        "components": 204  # CharacterActivities
    }
    response = requests.get(BASE+PROFILE_URL, headers=REQUEST_HEADERS, params=params)

    activities = []
    if response.status_code == 200:
        data = response.json()["Response"]
        character_data = data["characterActivities"]["data"]
        next_key = next(iter(character_data))
        character_activities = character_data[next_key]["availableActivities"]
        for activity in character_activities:
            for visible_reward in activity["visibleRewards"]:
                for reward_item in visible_reward["rewardItems"]:
                    if reward_item["uiStyle"] == "daily_grind_chance" or reward_item["uiStyle"] == "daily_grind_guaranteed":
                        item_hash = reward_item["itemQuantity"]["itemHash"]
                        activity_hash = activity["activityHash"]
                        activities.append(dict(activity=activity_hash, item=item_hash))
    else:
        print("Error:", response.status_code, response.text)

    return activities

def get_activity_names(activities, activity_item_hashes):
    activity_names = []
    for activity_item_hash in activity_item_hashes:
        name = activities[str(activity_item_hash["activity"])]["originalDisplayProperties"]["name"]
        if "Quickplay" in name or name not in activity_names:
            if "Quickplay" in name:
                if activities[str(activity_item_hash["activity"])]["matchmaking"]["maxParty"] == 1:
                    name += " (Solo Ops)"
                else:
                    name += " (Fireteam Ops)"
            activity_names.append(name)
    return activity_names


def get_item_names(items, activity_item_hashes):
    item_names = []
    for activity_item_hash in activity_item_hashes:
        name = items[str(activity_item_hash["item"])]["displayProperties"]["name"]
        if items[str(activity_item_hash["item"])]["equippingBlock"]["ammoType"] == 0:       # is armor?
            words = name.split()
            if words:
                item_type = items[str(activity_item_hash["item"])]["itemTypeDisplayName"]
                if item_type in CLASS_ITEMS:
                    words[-1] = "Class Item"
                else:
                    words[-1] = item_type
                name = ' '.join(words)
        if name not in item_names:
            item_names.append(name)

    return item_names


def create_item_activity_dictionary():
    manifest = request_manifest([BASE, MANIFEST_URL])
    activities = request_activity_hashes(manifest, BASE)
    items = request_item_hashes(manifest, BASE)

    #solo_ops_activities, fireteam_ops_activities, pinnacle_ops_activities = get_ops_activities(activity_hashes)
    activity_item_hashes = get_profile_activities()

    activity_names = get_activity_names(activities, activity_item_hashes)
    item_names = get_item_names(items, activity_item_hashes)

    print(f"Activity names: {activity_names}")
    print(f"Item names: {item_names}")

    bungie_data = []
    for i, activity in enumerate(activity_names):
        bungie_data.append(dict(activity=activity, item=item_names[i]))

    return bungie_data


def format_bungie_data():
    """Format your list of dictionaries into a message string."""
    bungie_data = create_item_activity_dictionary()
    lines = []
    for entry in bungie_data:
        lines.append(f"**{entry['activity']}** → {entry['item']}")
    return "\n".join(lines)


# --- EVENTS ---
@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")

# --- COMMANDS ---
@bot.command(name="focus")
async def focus(ctx):
    """Run Bungie fetch and reply with data."""
    await ctx.send("Fetching latest Bungie data...")
    message = format_bungie_data()
    await ctx.send(message)

# --- MAIN ENTRYPOINT ---
def main():
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()





