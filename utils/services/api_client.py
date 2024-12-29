import asyncio
import json
import random
import requests

from curl_cffi import requests
from urllib.parse import urlparse
from utils.settings import DOMAIN_API, logger, Fore


# Function to build HTTP headers dynamically with hardcoded User-Agent
async def build_headers(url, account, method="POST", data=None):
    """
    Build headers for API requests dynamically with fixed User-Agent.
    """
    # Start with base headers
    headers = {
        "Authorization": f"Bearer {account.token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    }

    # Add endpoint-specific headers
    endpoint_specific_headers = get_endpoint_headers(url)
    headers.update(endpoint_specific_headers)

    # Validate serializability of data
    if method in ["POST", "PUT"] and data is not None:
        if not isinstance(data, dict):
            raise ValueError("Payload must be a dictionary.")
        try:
            json.dumps(data, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid payload data: {e}")

    return headers

# Function to return endpoint-specific headers based on the API
def get_endpoint_headers(url):
    """
    Return endpoint-specific headers based on the API.
    """
    EARN_MISSION_SET = {DOMAIN_API["EARN_INFO"], DOMAIN_API["MISSION"], DOMAIN_API["COMPLETE_MISSION"]}
    PING_LIST = DOMAIN_API["PING"]
    ACTIVATE_URL = DOMAIN_API["ACTIVATE"]

    # Necessary headers
    necessary_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://app.nodepay.ai/",
        "Origin": "chrome-extension://lgmpfmgeabnnlemejacfljbmonaomfmm",
        "Connection": "keep-alive",
    }

    # Optional headers
    optional_headers = {
        "Sec-CH-UA": '"Not/A)Brand";v="8", "Chromium";v="126", "Herond";v="126"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cors-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    # Check if the URL matches specific sets
    if url in PING_LIST or url in EARN_MISSION_SET or url == ACTIVATE_URL:
        return {**necessary_headers, **optional_headers}

    # Default minimal headers
    return {"Accept": "application/json"}

# Function to send HTTP requests with error handling and custom headers
async def send_request(url, data, account, method="POST", timeout=120):
    """
    Perform HTTP requests with proper headers and error handling.
    """
    # Validate URL and Data
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a valid string.")
    if data and not isinstance(data, dict):
        raise ValueError("Data must be a dictionary.")

    headers = await build_headers(url, account, method, data)
    proxies = {"http": account.proxy, "https": account.proxy} if account.proxy else None

    if not headers:
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}No headers generated for URL:{Fore.RESET} {urlparse(url).path}")
        raise ValueError("Failed to generate headers")

    try:
        # Choose request method
        if method == "GET":
            response = requests.get(url, headers=headers, proxies=proxies, impersonate="safari15_5", timeout=timeout)
        else:
            response = requests.post(url, json=data, headers=headers, impersonate="safari15_5", proxies=proxies, timeout=timeout)

        response.raise_for_status()  # Raise exception for HTTP errors

        try:
            return response.json() # Parse JSON response
        except json.JSONDecodeError:
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Failed to decode JSON response:{Fore.RESET} {getattr(response, 'text', 'No response')}")
            raise ValueError("Invalid JSON in response")

        except requests.exceptions.ProxyError:
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Proxy connection failed. Unable to connect to proxy{Fore.RESET}")
            raise

    except requests.exceptions.RequestException as e:
        if e.response:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 1))
                logger.warning(
                    f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.YELLOW}Rate limited (429). Retrying after {retry_after} seconds...{Fore.RESET}"
                )
                await asyncio.sleep(retry_after)
            elif e.response.status_code == 403:
                logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}403 Forbidden: Check permissions or proxy.{Fore.RESET}")
                return None
        raise  # Rethrow exception for higher-level handling

# Function to send HTTP requests with retry logic using exponential backoff
async def retry_request(url, data, account, method="POST", max_retries=3):
    """
    Retry requests using exponential backoff.
    """
    retry_count = 0
    while retry_count < max_retries:
        try:
            return await send_request(url, data, account, method)  # Return the response if successful

        except requests.exceptions.RequestException as e:
            short_error = str(e).split(" See")[0]
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Request error:{Fore.RESET} {short_error}")

        except Exception as e:
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Unexpected error:{Fore.RESET} {str(e)}")

        retry_count += 1
        delay = await exponential_backoff(retry_count)
        logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Retry attempt {retry_count}: Retrying after {delay:.2f} seconds...")

    logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Max retries reached for URL:{Fore.RESET} {urlparse(url).path}")
    return None

# Function to implement exponential backoff delay during retries
async def exponential_backoff(retry_count, base_delay=1):
    """
    Perform exponential backoff for retries.
    """
    delay = min(base_delay * (2 ** retry_count) + random.uniform(0, 1), 30)
    await asyncio.sleep(delay)
    return delay
