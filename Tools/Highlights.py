import re
import ast
import json
import time
import requests
from PIL import Image
from instagrapi import Client

insta_client = Client()
insta_client.login("josednavedaraaz", "NICK@123")

with open("Data/Highlights.txt", "r") as f:
    highlights_data = f.read()

highlight_pks = re.findall(r"Highlight\(pk='(\d+)'", highlights_data)
highlight_pks = [int(pk) for pk in highlight_pks]

print(highlight_pks)

# details = []
# for pk in highlight_pks:
#     print(f"Fetching Highlight {pk}")
#     info = insta_client.highlight_info(pk).model_dump()
#     details.append(info)
#     time.sleep(2)

# with open("Data/AllHighlightDetails.json", "w") as f:
#     json.dump(details, f, indent=4, default=str)

# print("All Highlight Data Saved")

with open("Data/AllHighlightDetails.json", "r") as f:
    highlight_data = json.load(f)

for i in range(1):
    highlight = highlight_data[i] 

    print("Working On First Highlight")

    highlight_pk = highlight["pk"]
    highlight_story_ids = [str(mid) for mid in highlight["media_ids"]]

    new_highlight = insta_client.highlight_create(
        highlight["title"], highlight_story_ids
    )
    new_highlight_pk = new_highlight.pk

    time.sleep(2)

    # cover_url = highlight["cover_media"]["cropped_image_version"]["url"]
    # cover_path = "/tmp/test.jpg"

    # response = requests.get(cover_url)
    # with open(cover_path, "wb") as f:
    #     f.write(response.content)

    # img = Image.open(cover_path)
    # img = img.resize((720, 720))
    # img.save(cover_path)

    # insta_client.highlight_change_cover(highlight_pk, cover_path)

    print("Highlight Created!")
    time.sleep(5)
