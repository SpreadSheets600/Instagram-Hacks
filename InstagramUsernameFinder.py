from email import message
import os
import sys
import json
import time
import random
from datetime import datetime

try:
    import requests

except ImportError:
    os.system("pip install requests")
    import requests


class Colors:
    RED = "\033[1;91m"
    GREEN = "\033[1;92m"
    YELLOW = "\033[1;93m"
    BLUE = "\033[1;94m"
    MAGENTA = "\033[1;95m"
    CYAN = "\033[1;96m"
    WHITE = "\033[1;97m"
    RESET = "\033[0m"


USERNAME_CHARS = "1234567890qwertyuiopasdfghjklzxcvbnm"
ALPHA_CHARS = "qwertyuiopasdfghjklzxcvbnm"

total_checks = 0
available_usernames = 0


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def live_typing(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def send_discord_notification(username, webhook_url):
    if not webhook_url:
        return False

    try:
        message = {
            "embeds": [
                {
                    "title": "✅ Available Instagram Username Found",
                    "description": f"Username: **{username}**",
                    "color": 5763719,
                    "fields": [
                        {"name": "Length", "value": str(len(username)), "inline": True},
                        {
                            "name": "Found At",
                            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "inline": True,
                        },
                    ],
                    "footer": {"text": "Instagram Username Finder"},
                }
            ]
        }

        response = requests.post(webhook_url, json=message)

        return response.status_code == 204
    except Exception as e:
        print(
            f"{Colors.RED}[ERROR] Discord Notification Failed : {str(e)}{Colors.RESET}"
        )
        return False


def check_username_availability(username, notifications_config):
    global total_checks, available_usernames
    total_checks += 1

    print(
        f"{Colors.YELLOW}Checks: {Colors.WHITE}{total_checks}  "
        f"{Colors.GREEN}Available: {Colors.WHITE}{available_usernames}  "
        f"{Colors.CYAN}Current: {Colors.WHITE}{username}{' ' * 10}",
        end="\r",
    )

    try:
        response = requests.post(
            "https://www.instagram.com/accounts/web_create_ajax/attempt/",
            headers={
                "Host": "www.instagram.com",
                "x-ig-app-id": "936619743392459",
                "x-instagram-ajax": "81f3a3c9dfe2",
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Safari/537.36",
                "x-csrftoken": "jzhjt4G11O37lW1aDFyFmy1K0yIEN9Qv",
                "origin": "https://www.instagram.com",
                "referer": "https://www.instagram.com/accounts/emailsignup/",
            },
            data=f"email=test{random.randint(100000, 999999)}@gmail.com&username={username}&first_name=&opt_into_one_tap=false",
        )

        if (
            '"feedback_required"' in response.text
            or '"errors": {"username":' in response.text
            or '"code": "username_is_taken"' in response.text
        ):
            return False
        else:
            available_usernames += 1

            print(
                f"\n{Colors.GREEN}[FOUND] {Colors.WHITE}{username} Is Available!{' ' * 20}"
            )

            with open("AvailableUsernames.txt", "a") as f:
                f.write(f"{username},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            if notifications_config["discord"]["enabled"]:
                send_discord_notification(
                    username, notifications_config["discord"]["webhook_url"]
                )

            return True
    except Exception as e:
        print(f"\n{Colors.RED}[ERROR] {str(e)}{Colors.RESET}")
        time.sleep(5)
        return False


def generate_usernames(notifications_config):
    while True:
        chars = [random.choice(USERNAME_CHARS) for _ in range(3)]
        alpha_char = random.choice(ALPHA_CHARS)

        patterns = [
            alpha_char + chars[0] + chars[1] + chars[2],
            chars[0] + alpha_char + chars[1] + chars[2],
            chars[0] + chars[1] + alpha_char + chars[2],
            chars[0] + chars[1] + chars[2] + alpha_char,
        ]

        username = random.choice(patterns)

        check_username_availability(username, notifications_config)

        time.sleep(random.uniform(1.5, 3.0))


def save_config(config):
    with open("UsernameFinderConfig.json", "w") as f:
        json.dump(config, f, indent=4)


def load_config():
    try:
        with open("UsernameFinderConfig.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "discord": {"enabled": False, "webhook_url": ""},
        }


def main():
    clear_screen()
    print(
        f"\n{Colors.RESET}{Colors.YELLOW}[1/2]  Instagram Username Finder\n  ----------------------\n"
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

    print(
        f"{Colors.RESET}{Colors.YELLOW}[3/3] {Colors.WHITE}Username Generation Settings:"
    )
    print(f"  Character set: {Colors.CYAN}{USERNAME_CHARS}")
    print(f"  Username length: {Colors.CYAN}4 Characters")
    print(f"  File logging: {Colors.CYAN}AvailableUsernames.txt")

    print(f"{Colors.RESET}")
    input(
        f"{Colors.GREEN}Press Enter To Start Searching For Available Usernames ...{Colors.RESET}"
    )

    clear_screen()
    print(
        f"{Colors.GREEN}[STARTED] {Colors.WHITE}Searching For Available Instagram Usernames ..."
    )

    try:
        generate_usernames(config)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}[STOPPED] {Colors.WHITE}Username Search Stopped")
        print(
            f"{Colors.GREEN}Found {Colors.WHITE}{available_usernames} {Colors.GREEN}Available Usernames Out Of {Colors.WHITE}{total_checks} {Colors.GREEN}Checks."
        )
        if available_usernames > 0:
            print(f"{Colors.WHITE}Results Saved In AvailableUsernames.txt")
        print(f"{Colors.RESET}")


if __name__ == "__main__":
    main()
