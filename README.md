# Instagram Tools Collection

This repository contains tools for interacting with Instagram, helping you find available usernames and discover Instagram accounts.

## Tools Included

### 1. Instagram Username Finder

A tool that searches for available 4-character Instagram usernames by automatically checking their availability through Instagram's API.

**Features:**
- Automated checking of random 4-character usernames
- Real-time progress tracking (checks performed, available usernames found)
- Saves results to `AvailableUsernames.txt`
- Discord webhook integration for notifications when available usernames are found

### 2. Instagram Account Finder

A tool that discovers Instagram accounts with a minimum follower threshold by checking randomly generated user IDs.

**Features:**
- Multi-threaded search for faster discovery
- Minimum follower count filtering (default: 30)
- Gmail existence verification
- Recovery email detection
- Detailed account information display:
  - Full name
  - Email
  - Recovery email
  - Follower/following counts
  - User ID
  - Biography
  - Number of posts
- Discord webhook integration for notifications
- Saves results to `FinderResults.txt`

## Setup & Usage

### Prerequisites
- Python 3.6 or higher
- Required packages: `requests`, `user_agent` (automatic installation on first run)

### Configuration

Both tools support Discord webhook notifications. Configuration is saved to:
- `UsernameFinderConfig.json` for the Username Finder
- `AccountFinderConfig.json` for the Account Finder

### Running the Tools

1. **Username Finder:**
   ```
   python InstagramUsernameFinder.py
   ```
   Follow the prompts to configure Discord notifications and begin searching.

2. **Account Finder:**
   ```
   python InstagramAccountFinder.py
   ```
   Follow the prompts to configure Discord notifications and begin the search process.

### Output Files

- `AvailableUsernames.txt` - List of available Instagram usernames found
- `FinderResults.txt` - Detailed information about Instagram accounts discovered
- `GoogleToken.txt` - Used internally for Gmail verification

## Notes

- These tools are intended for educational purposes only
- Usage should comply with Instagram's Terms of Service
- Use responsibly and avoid excessive requests that could trigger rate limiting

## Customization

You can modify the following parameters in the code:
- **Account Finder:**
  - `MIN_FOLLOWERS` - Minimum follower threshold (default: 30)
  - `THREAD_COUNT` - Number of parallel search threads (default: 80)
  
- **Username Finder:**
  - `USERNAME_CHARS` - Character set used for username generation
  - Custom notification settings

## License

This project is for personal use only.
