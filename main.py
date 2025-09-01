# This is a sample Python script.
from dotenv import load_dotenv
import os
import requests
import discord
import asyncio

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


"""
SOLO_OPS_ACTIVITY_TYPE_HASH = 3851289711
FIRETEAM_OPS_ACTIVITY_TYPE_HASH = 556925641
FIRETEAM_OPS_MATCHMADE_ACTIVITY_TYPE_HASH = 1996806804
FIRETEAM_OPS_ONSLAUGHT_ACTIVITY_TYPE_HASH = 2897687202
FIRETEAM_OPS_CRAWL_ACTIVITY_TYPE_HASH = 2442898492
PINNACLE_OPS_ACTIVITY_TYPE_HASH = 1227821118
CRUCIBLE_OPS_ACTIVITY_TYPE_HASH = 4107873900
"""

def request_manifest(args):
    request_url = ""
    for arg in args:
        request_url += arg

    response_data = requests.get(request_url, headers=REQUEST_HEADERS).json()
    return response_data


def request_activity_hashes(manifest, args):
    request_url = ""
    for arg in args:
        request_url += arg

    request_url += manifest["Response"]["jsonWorldComponentContentPaths"]["en"]["DestinyActivityDefinition"]
    activity_hashes = requests.get(request_url, headers=REQUEST_HEADERS).json()

    return activity_hashes


def request_item_hashes(manifest, args):
    request_url = ""
    for arg in args:
        request_url += arg

    request_url += manifest["Response"]["jsonWorldComponentContentPaths"]["en"]["DestinyInventoryItemDefinition"]
    item_hashes = requests.get(request_url, headers=REQUEST_HEADERS).json()

    return item_hashes

"""
def get_ops_activities(activity_hashes):
    solo_ops_activities = []
    fireteam_ops_activities = []
    pinnacle_ops_activities = []

    for activity_hash, definition in activity_hashes.items():
        #print(definition["activityTypeHash"])
        activity_type_hash = definition["activityTypeHash"]
        name = definition["originalDisplayProperties"]["name"]

        if activity_type_hash == SOLO_OPS_ACTIVITY_TYPE_HASH:
            exists = any(name in activity.values() for activity in solo_ops_activities)
            if not exists:
                solo_ops_activities.append(dict(activityHash=activity_hash, name=name))
                print(f"Solo Ops: {solo_ops_activities}")
        elif activity_type_hash == FIRETEAM_OPS_ACTIVITY_TYPE_HASH or activity_type_hash == FIRETEAM_OPS_MATCHMADE_ACTIVITY_TYPE_HASH or activity_type_hash == FIRETEAM_OPS_ONSLAUGHT_ACTIVITY_TYPE_HASH or activity_type_hash == FIRETEAM_OPS_CRAWL_ACTIVITY_TYPE_HASH:
            exists = any(name in activity.values() for activity in fireteam_ops_activities)
            if not exists and "Conquest" not in name:
                fireteam_ops_activities.append(dict(activityHash=activity_hash, name=name))
                print(f"Fireteam Ops: {fireteam_ops_activities}")
        elif activity_type_hash == PINNACLE_OPS_ACTIVITY_TYPE_HASH:
            exists = any(name in activity.values() for activity in pinnacle_ops_activities)
            if not exists and "Conquest" not in name:
                pinnacle_ops_activities.append(dict(activityHash=activity_hash, name=name))
                print(f"Pinnacle Ops: {pinnacle_ops_activities}")

    return solo_ops_activities, fireteam_ops_activities, pinnacle_ops_activities
"""

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


def format_bungie_data(bungie_data):
    """Format your list of dictionaries into a message string."""
    lines = []
    for entry in bungie_data:
        lines.append(f"**{entry['activity']}** → {entry['item']}")
    return "\n".join(lines)


# --- POST ONCE ---
async def main():
    # Use discord.Client instead of commands.Bot for simplicity

    bungie_data = create_item_activity_dictionary()
    intents = discord.Intents.default()

    async with discord.Client(intents=intents) as client:   # <---
        @client.event
        async def on_ready():
            print(f"✅ Bot logged in as {client.user}")
            for channel_id in DISCORD_CHANNEL_IDS:
                channel = client.get_channel(channel_id)
                if channel:
                    await channel.send("Here’s today’s Bonus Focus rewards:\n" + format_bungie_data(bungie_data))
                    print(f"✅ Posted in {channel.name} (ID: {channel.id})")
                else:
                    print(f"⚠️ Could not find channel with ID {channel_id}")
            await client.close()

        await client.start(DISCORD_BOT_TOKEN)

if __name__ == '__main__':
    asyncio.run(main())






