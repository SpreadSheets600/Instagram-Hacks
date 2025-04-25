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


USERNAME_CHARS = "1234567890qwertyuiopasdfghjklzxcvbnm"
ALPHA_CHARS = "qwertyuiopasdfghjklzxcvbnm"

total_checks = 0
available_usernames = 0
last_notification_time = 0
start_time = time.time()


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


def send_stats_notification(webhook_url):
    """Send periodic stats updates to Discord webhook"""
    if not webhook_url:
        return False

    try:

        success_rate = (
            (available_usernames / total_checks * 100) if total_checks > 0 else 0
        )

        def create_progress_bar(percent, length=10):
            filled = int(percent * length / 100)
            return f"{'█' * filled}{'░' * (length - filled)}"

        progress_bar = create_progress_bar(success_rate, 10)

        current_time = time.time()
        runtime = current_time - start_time if "start_time" in globals() else 60
        checks_per_minute = round(total_checks / (runtime / 60))

        message = {
            "embeds": [
                {
                    "title": "📊 Instagram Username Finder - Stats Update",
                    "description": f"**Current Session Stats**\n{progress_bar} `{success_rate:.2f}%`",
                    "color": 3447003,
                    "fields": [
                        {
                            "name": "✅ Available Usernames",
                            "value": f"`{available_usernames}` usernames",
                            "inline": True,
                        },
                        {
                            "name": "🔍 Total Checks",
                            "value": f"`{total_checks}` checks",
                            "inline": True,
                        },
                        {
                            "name": "⚡ Check Rate",
                            "value": f"`{checks_per_minute}` checks/minute",
                            "inline": True,
                        },
                        {
                            "name": "⏱️ Runtime",
                            "value": f"`{int(runtime // 3600)}h {int((runtime % 3600) // 60)}m {int(runtime % 60)}s`",
                            "inline": True,
                        },
                    ],
                    "footer": {
                        "text": "Instagram Username Finder • Auto-generated Status Report"
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            ]
        }

        response = requests.post(webhook_url, json=message)

        if response.status_code == 204:
            print(f"\n{Colors.success('Stats notification sent to Discord')}")
            return True
        else:
            print(
                f"\n{Colors.error(f'Failed to send stats notification! Status: {response.status_code}')}"
            )
            return False
    except Exception as e:
        print(f"\n{Colors.error(f'Error sending stats notification: {e}')}")
        return False


def check_username_availability(username, notifications_config):
    global total_checks, available_usernames, last_notification_time
    total_checks += 1

    spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    spinner = spinner_chars[total_checks % len(spinner_chars)]

    print(
        f"{Colors.BLUE}{spinner} {Colors.YELLOW}Checks: {Colors.WHITE}{total_checks}  "
        f"{Colors.GREEN}Available: {Colors.WHITE}{available_usernames}  "
        f"{Colors.CYAN}Checking: {Colors.WHITE}{username}{' ' * 15}",
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

        current_time = time.time()
        notification_interval = (
            notifications_config.get("notification_settings", {}).get(
                "interval_minutes", 15
            )
            * 60
        )

        if (
            notifications_config["discord"]["enabled"]
            and current_time - last_notification_time > notification_interval
        ):
            send_stats_notification(notifications_config["discord"]["webhook_url"])
            last_notification_time = current_time

        if (
            '"feedback_required"' in response.text
            or '"errors": {"username":' in response.text
            or '"code": "username_is_taken"' in response.text
        ):
            return False
        else:
            available_usernames += 1

            print(" " * 100, end="\r")
            print(
                f"\n{Colors.GREEN}[FOUND] {Colors.WHITE}{username} {Colors.GREEN}is available!{Colors.RESET}{' ' * 20}"
            )

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("AvailableUsernames.txt", "a") as f:
                f.write(f"{username},{timestamp}\n")

            if notifications_config["discord"]["enabled"]:
                send_discord_notification(
                    username, notifications_config["discord"]["webhook_url"]
                )

            if total_checks % 5 == 0:
                print_stats()

            return True
    except Exception as e:
        print(f"\n{Colors.error(f'Error: {str(e)}')}")
        time.sleep(5)
        return False


def generate_usernames(notifications_config):
    global last_notification_time

    last_notification_time = time.time()

    print_stats()

    try:
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

            if total_checks % 50 == 0:
                print_stats()

    except KeyboardInterrupt:
        print_stats()
        raise


def save_config(config):
    with open("UsernameFinderConfig.json", "w") as f:
        json.dump(config, f, indent=4)


def load_config():
    try:
        with open("UsernameFinderConfig.json", "r") as f:
            config = json.load(f)
            if "discord" not in config:
                config["discord"] = {"enabled": False, "webhook_url": ""}
            if "notification_settings" not in config:
                config["notification_settings"] = {
                    "interval_minutes": 15,
                    "enabled": True,
                }
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "discord": {"enabled": False, "webhook_url": ""},
            "notification_settings": {"interval_minutes": 15, "enabled": True},
        }


def print_stats():
    """Print current stats in a visually appealing format"""

    success_rate = (available_usernames / total_checks * 100) if total_checks > 0 else 0
    runtime = time.time() - start_time if "start_time" in globals() else 0

    current_time = datetime.now().strftime("%H:%M:%S")

    clear_screen()
    print(
        f"""
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃  {Colors.BOLD}{Colors.CYAN}Instagram Username Finder{Colors.RESET}                 
    ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
    ┃  {Colors.GREEN}● Available Usernames : {available_usernames:>5}{Colors.RESET}                
    ┃  {Colors.YELLOW}● Total Checks       : {total_checks:>5}{Colors.RESET}                
    ┃  {Colors.MAGENTA}● Success Rate       : {success_rate:.2f}%{Colors.RESET}               
    ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
    ┃  {Colors.BLUE}● Runtime            : {int(runtime // 3600)}h {int((runtime % 3600) // 60)}m {int(runtime % 60)}s{Colors.RESET}        
    ┃  {Colors.CYAN}● Current Time       : {current_time}{Colors.RESET}           
    ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    
    {Colors.GRAY}Press Ctrl+C to stop the process{Colors.RESET}
    """
    )


def main():
    global start_time
    start_time = time.time()

    try:

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
        ║ {Colors.WHITE}Instagram Username Finder {Colors.YELLOW}v1.1{Colors.CYAN}             
        ║ {Colors.GRAY}Finds available Instagram usernames{Colors.CYAN}        
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
                f"\n{Colors.YELLOW}[2/3] {Colors.WHITE}Stats Notification Settings:{Colors.RESET}"
            )
            interval_prompt = f"  {Colors.GRAY}› {Colors.WHITE}Send stats notification every X minutes [{config['notification_settings']['interval_minutes']}]: {Colors.CYAN}"
            interval = input(interval_prompt)

            if interval and interval.isdigit() and int(interval) > 0:
                config["notification_settings"]["interval_minutes"] = int(interval)

            print(
                f"  {Colors.GREEN}● {Colors.WHITE}Stats will be sent every {config['notification_settings']['interval_minutes']} minutes"
            )
        else:
            config["discord"]["enabled"] = False

        print(
            f"\n{Colors.YELLOW}[3/3] {Colors.WHITE}Username Generation Settings:{Colors.RESET}"
        )
        print(
            f"  {Colors.GRAY}› {Colors.WHITE}Character set: {Colors.CYAN}{USERNAME_CHARS}"
        )
        print(
            f"  {Colors.GRAY}› {Colors.WHITE}Username length: {Colors.CYAN}4 characters"
        )
        print(
            f"  {Colors.GRAY}› {Colors.WHITE}File logging: {Colors.CYAN}AvailableUsernames.txt"
        )

        save_config(config)

        if config["discord"]["enabled"]:
            print(f"\n{Colors.success('✓ Discord notifications enabled')}")

            webhook_url = config["discord"]["webhook_url"]

            startup_message = {
                "embeds": [
                    {
                        "title": "🚀 Instagram Username Finder Started",
                        "description": "The Instagram Username Finder has been started and is now searching for available usernames.",
                        "color": 5814783,
                        "fields": [
                            {
                                "name": "📊 Stats Notifications",
                                "value": f"Every `{config['notification_settings']['interval_minutes']}` minutes",
                                "inline": True,
                            },
                            {
                                "name": "🔢 Username Pattern",
                                "value": "4-character usernames",
                                "inline": True,
                            },
                        ],
                        "footer": {
                            "text": "Instagram Username Finder • Session Started"
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
                ]
            }

            requests.post(webhook_url, json=startup_message)

        print(f"\n{Colors.highlight('Starting search...')}")
        input(
            f"{Colors.GREEN}Press Enter To Start Searching For Available Usernames ...{Colors.RESET}"
        )

        generate_usernames(config)
    except KeyboardInterrupt:

        success_rate = (
            (available_usernames / total_checks * 100) if total_checks > 0 else 0
        )
        runtime = time.time() - start_time

        print(f"\n\n{Colors.warning('Username Search Stopped')}")
        print(
            f"{Colors.success(f'Found {available_usernames} available usernames')} out of {total_checks} checks ({success_rate:.2f}%)"
        )
        print(
            f"{Colors.info(f'Total runtime:')} {int(runtime // 3600)}h {int((runtime % 3600) // 60)}m {int(runtime % 60)}s"
        )

        if available_usernames > 0:
            print(f"{Colors.GRAY}Results saved in AvailableUsernames.txt{Colors.RESET}")

        if config["discord"]["enabled"]:
            shutdown_message = {
                "embeds": [
                    {
                        "title": "🛑 Instagram Username Finder Stopped",
                        "description": "The Instagram Username Finder has been stopped by the user.",
                        "color": 15548997,
                        "fields": [
                            {
                                "name": "✅ Available Usernames",
                                "value": f"`{available_usernames}` usernames",
                                "inline": True,
                            },
                            {
                                "name": "🔍 Total Checks",
                                "value": f"`{total_checks}` checks",
                                "inline": True,
                            },
                            {
                                "name": "⏱️ Runtime",
                                "value": f"`{int(runtime // 3600)}h {int((runtime % 3600) // 60)}m {int(runtime % 60)}s`",
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Instagram Username Finder • Session Ended"},
                        "timestamp": datetime.now().isoformat(),
                    }
                ]
            }

            webhook_url = config["discord"]["webhook_url"]
            requests.post(webhook_url, json=shutdown_message)


if __name__ == "__main__":
    main()
