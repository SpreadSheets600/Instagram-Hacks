import json
from instagrapi import Client

insta_client = Client()
insta_client.login("josednavedaraaz", "NICK@123")

media_url = "https://www.instagram.com/siddtrades/p/C0b4uKsvE8f/"
media_pk = insta_client.media_pk_from_url(media_url)
media_info = insta_client.media_info(media_pk)

with open("Data/TargetMediaInfo.json", "w") as target_file:
    json.dump(json.loads(media_info.model_dump_json(indent=4)), target_file, indent=4)

video_url = getattr(media_info, "video_url", None)

if video_url:
    insta_client.video_download_by_url(video_url, folder="/tmp")
    print(f"Downloaded Video : {video_url}")
