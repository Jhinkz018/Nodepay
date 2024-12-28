import aiohttp
import ssl

from urllib.parse import urlparse
from utils.settings import logger, Fore


# Load proxies from a file
def load_proxies():
    try:
        with open('proxies.txt', 'r') as file:
            proxies = file.read().splitlines()

        if not proxies:
            logger.warning(f"{Fore.CYAN}00{Fore.RESET} - {Fore.YELLOW}No proxies found in proxies.txt. Running without proxies.{Fore.RESET}")

        return proxies
    
    except FileNotFoundError:
        logger.warning(f"{Fore.CYAN}00{Fore.RESET} - {Fore.YELLOW}File proxies.txt not found. Running without proxies.{Fore.RESET}")
        return []

    except Exception as e:
        logger.error(f"{Fore.CYAN}00{Fore.RESET} - {Fore.RED}Error loading proxies:{Fore.RESET} {e}")
        return []

# Prompt the user to decide whether to use proxies
def get_proxy_choice():
    while (user_input := input("Do you want to use proxy? (yes/no)? ").strip().lower()) not in ['yes', 'no']:
        print("Invalid input. Please enter 'yes' or 'no'.")

    print(f"You selected: {'Yes' if user_input == 'yes' else 'No'}, ENJOY!\n")

    if user_input == 'yes':
        proxies = load_proxies()

        if not proxies:
            logger.error(f"{Fore.CYAN}00{Fore.RESET} - {Fore.RED}No proxies found in proxies.txt. Please add valid proxies.{Fore.RESET}")
            return []
        return proxies
    return []

# Map tokens to proxies, assigning None if proxies are insufficient
def assign_proxies(tokens, proxies):
    if proxies is None:
        proxies = []

    paired = list(zip(tokens[:len(proxies)], proxies))
    remaining = [(token, None) for token in tokens[len(proxies):]]

    return paired + remaining

# Extract the hostname (IP address) from a given proxy URL
def get_proxy_ip(proxy_url):
    try:
        return urlparse(proxy_url).hostname
    except Exception:
        return "Unknown"

# Create SSL context to allow self-signed certificates
def create_ssl_context():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context

# Get the public IP address, optionally through a proxy
async def get_ip_address(proxy=None):
    try:
        proxy_ip = get_proxy_ip(proxy) if proxy else "Unknown"
        url = "https://api.ipify.org?format=json"

        ssl_context = create_ssl_context()

        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy, ssl=ssl_context) as response:

                if response.status == 200:
                    result = await response.json()
                    return result.get("ip", "Unknown")

                return "Unknown"
    
    except Exception as e:
        error_message = str(e).split(", url")[0]
        logger.error(f"{Fore.CYAN}00{Fore.RESET} - {Fore.RED}Request failed {error_message}{Fore.RESET}")
    
    return proxy_ip

# Resolves IP or proxy for the account
async def resolve_ip(account):
    try:
        if account.proxy and account.proxy.startswith("http"):
            return await get_ip_address(account.proxy)
        else:
            return await get_ip_address()
    except Exception as e:
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Failed to resolve proxy or IP address:{Fore.RESET} {e}")
        return "Unknown"
