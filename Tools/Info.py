import json
from instagrapi import Client

insta_client = Client()
insta_client.login("josednavedaraaz", "NICK@123")

user_info_json = insta_client.user_info_by_username("siddtrades").model_dump_json(indent=4)
user_info = json.loads(user_info_json)

with open("Data/TargetInfo.json", "w") as target_file:
    json.dump(user_info, target_file, indent=4)

print("Updated TargetInfo File")
