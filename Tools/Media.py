import json
from instagrapi import Client

insta_client = Client()
insta_client.login("josednavedaraaz", "NICK@123")

with open("Data/TargetInfo.json", "r") as target_file:
    target_info = json.load(target_file)

target_id = target_info["pk"]

target_media_details_json = insta_client.insights_media_feed_all(user_id=target_id, sleep=5).model_dump_json(indent=4)
target_media_details = json.loads(target_media_details_json)

with open("Data/TargetMedia.json", "w") as target_file:
    json.dump(target_media_details, target_file, indent=4)

print("Updated TargetMeida File")
