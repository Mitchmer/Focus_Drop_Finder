# This is a sample Python script.
from dotenv import load_dotenv
import time
import os
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException

# all Solo ops have the DestinyActivityDefinition { "activityhash" : { "activityTypeHash" : 3851289711 } }
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
#   3816084061 display name : Quickplay: Normal; name: Quickplay: Normal
# Pinnacle ops 1227821118
# FIreteam ops: 556925641
# matchmade fireteam ops: 1996806804

# seems to be both 'daily_grind_chance' and 'daily_grind_guaranteed'

# 3956025454 is the "bonus engrams"

load_dotenv()
API_KEY = os.getenv("BUNGIE_API_KEY")

# Replace with your membership values
# membership_type = 1  # Steam/Epic = 3, Xbox=1, PlayStation=2
# membership_id = "4611686018429826535"  # your Destiny membershipId

membership_type = 1  # Steam/Epic
membership_id = "4611686018429826535"

REQUEST_HEADERS = {"X-API-Key": API_KEY}
BASE = "https://www.bungie.net"
MANIFEST_URL = "/Platform/Destiny2/Manifest/"

SOLO_OPS_ACTIVITY_TYPE_HASH = 3851289711
FIRETEAM_OPS_ACTIVITY_TYPE_HASH = 556925641
FIRETEAM_OPS_MATCHMADE_ACTIVITY_TYPE_HASH = 1996806804

#params = {"components": "204"}


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


def get_solo_ops_activities(activity_hashes):
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
                print(solo_ops_activities)
        elif activity_type_hash == FIRETEAM_OPS_ACTIVITY_TYPE_HASH or activity_type_hash == FIRETEAM_OPS_MATCHMADE_ACTIVITY_TYPE_HASH:
            exists = any(name in activity.values() for activity in fireteam_ops_activities)

    return solo_ops_activities, fireteam_ops_activities, pinnacle_ops_activities


def get_fireteam_ops_activities(activity_hashes):


def main():
    manifest = request_manifest([BASE, MANIFEST_URL])
    activity_hashes = request_activity_hashes(manifest, BASE)

    solo_ops_activities, fireteam_ops_activities, pinnacle_ops_activities = get_solo_ops_activities(activity_hashes)






if __name__ == '__main__':
    main()






