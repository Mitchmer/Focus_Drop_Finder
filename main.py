# This is a sample Python script.
from dotenv import load_dotenv
import os
import requests
import discord
from discord.ext import commands
import json
import gc

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

# JSON Paths
MANIFEST_FILENAME = "Manifest.json"
ACTIVITY_DEFINITION_FILENAME = "DestinyActivityDefinition.json"
INVENTORY_ITEM_LITE_DEFINITION_FILENAME = "DestinyInventoryItemLiteDefinition.json"

CLASS_ITEMS = ["Titan Mark", "Hunter Cloak", "Warlock Bond"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def request_manifest(args):
    """
    Requests the Bungie API manifest
    :param args: can be a list of arguments, all that matters is that
        when concatenated they form a complete API request for the
        manifest.
    :return: returns a JSON object for query.
    """
    #local_manifest = None
    #remote_manifest = None
    up_to_date = True

    request_url = ""
    for arg in args:
        request_url += arg
    try:
        response = requests.get(request_url, headers=REQUEST_HEADERS, timeout=10)
        response.raise_for_status()
        remote_manifest = response.json()

        if os.path.exists(MANIFEST_FILENAME):
            with open(MANIFEST_FILENAME, "r") as f:
                local_manifest = json.load(f)
                print("Manifest loaded from local storage")
        else:
            print("Local manifest not found. Saving API manifest")
            with open(MANIFEST_FILENAME, "w") as f:
                # noinspection PyTypeChecker
                json.dump(remote_manifest, f)
            local_manifest = remote_manifest

        # this checks the need to update the manifest
        if local_manifest.get("Response", {}).get("version") != remote_manifest.get("Response", {}).get("version"):
            print(f"Local manifest version diff from remote. Updating manifest")
            print(f"Local version: {local_manifest.get("Response", {}).get("version")}")
            print(f"Remote version: {remote_manifest.get("Response", {}).get("version")}")
            with open(MANIFEST_FILENAME, "w") as f:
                # noinspection PyTypeChecker
                json.dump(remote_manifest, f)
            local_manifest = remote_manifest
            up_to_date = False

    except requests.exceptions.Timeout:
        raise RuntimeError("⏳ Bungie API timed out while fetching manifest metadata.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"❌ Bungie API returned HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"⚠️ Network error while fetching manifest metadata: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"⚠️ Could not parse manifest metadata: {e}")

    del response
    del remote_manifest
    gc.collect()

    return local_manifest, up_to_date


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
        raise RuntimeError("⏳ Bungie API timed out while fetching activity metadata.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"❌ Bungie API returned HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"⚠️ Network error while fetching activity metadata: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"⚠️ Could not parse activity metadata: {e}")
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
        raise RuntimeError("⏳ Bungie API timed out while fetching item metadata.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"❌ Bungie API returned HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"⚠️ Network error while fetching item metadata: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"⚠️ Could not parse item metadata: {e}")
    return item_hashes


def get_profile_activities():
    params = {
        "components": 204  # CharacterActivities
    }
    try:
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
    except requests.exceptions.Timeout:
        raise RuntimeError("⏳ Bungie API timed out while fetching profile metadata.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"❌ Bungie API returned HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"⚠️ Network error while fetching profile metadata: {e}")
    except (json.JSONDecodeError, KeyError) as e:
        raise RuntimeError(f"⚠️ Could not parse profile metadata: {e}")

    return activities

def get_activity_names(activities, activity_item_hashes):
    activity_names = []
    for activity_item_hash in activity_item_hashes:
        name = activities[str(activity_item_hash["activity"])]["originalDisplayProperties"]["name"]
        if "Quickplay" in name or name not in activity_names:
            if "Quickplay" in name:
                if activities[str(activity_item_hash["activity"])]["matchmaking"]["maxParty"] == 1:
                    name = "Quickplay (Solo Ops)"
                else:
                    name = "Quickplay (Fireteam Ops)"
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


def create_item_activity_dictionary(activities, items):

    profile_activity_item_hashes = get_profile_activities()

    activity_names = get_activity_names(activities, profile_activity_item_hashes)
    item_names = get_item_names(items, profile_activity_item_hashes)

    print(f"Activity names: {activity_names}")
    print(f"Item names: {item_names}")

    bungie_data = []
    for i, activity in enumerate(activity_names):
        bungie_data.append(dict(activity=activity, item=item_names[i]))

    return bungie_data


def format_bungie_data(activity_hashes, item_hashes):
    """Format your list of dictionaries into a message string."""
    bungie_data = create_item_activity_dictionary(activity_hashes, item_hashes)
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

    try:
        #activity_hashes = None
        #item_hashes = None
        manifest, up_to_date = request_manifest([BASE, MANIFEST_URL])

        # if data is up to date
        if up_to_date:

            # check if activity JSON exists
            if os.path.exists(ACTIVITY_DEFINITION_FILENAME):
                with open(ACTIVITY_DEFINITION_FILENAME, "r") as f:
                    activity_hashes = json.load(f)
                    print("Activity hashes loaded from local storage")
            else:
                activity_hashes = request_activity_hashes(manifest, BASE)
                with open(ACTIVITY_DEFINITION_FILENAME, "w") as f:
                    json.dump(activity_hashes, f)
                    print("Activity hash file not found. Activity hashes loaded from API")

            # check if item JSON exists
            if os.path.exists(INVENTORY_ITEM_LITE_DEFINITION_FILENAME):
                with open(INVENTORY_ITEM_LITE_DEFINITION_FILENAME, "r") as f:
                    item_hashes = json.load(f)
                    print("Item hashes loaded from local storage")
            else:
                item_hashes = request_item_hashes(manifest, BASE)
                with open(INVENTORY_ITEM_LITE_DEFINITION_FILENAME, "w") as f:
                    json.dump(item_hashes, f)
                    print("Item hash file not found. Item hashes loaded from API")

            # if everything exists, item and activity hashes were loaded from local memory

        else:
            activity_hashes = request_activity_hashes(manifest, BASE)
            with open(ACTIVITY_DEFINITION_FILENAME, "w") as f:
                json.dump(activity_hashes, f)

            item_hashes = request_item_hashes(manifest, BASE)
            with open(INVENTORY_ITEM_LITE_DEFINITION_FILENAME, "w") as f:
                json.dump(item_hashes, f)

            print("Activity and Item hashes loaded from up-to-date API manifest")

        # activity and item hashes exist in memory now

        message = format_bungie_data(activity_hashes, item_hashes)
        await ctx.send(message)

        del activity_hashes
        del item_hashes
        del manifest
        gc.collect()

    except RuntimeError as e:
        await ctx.send(str(e))

# --- MAIN ENTRYPOINT ---
def main():
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()





