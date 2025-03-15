import asyncio
import json
import random
import requests
import time
import tls_client

from urllib.parse import urlparse
from utils.settings import DOMAIN_API, REQUEST_TIMEOUT, logger, Fore


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
async def send_request(url, data, account, method="POST", timeout=REQUEST_TIMEOUT):
    """
    Perform HTTP requests with proper headers and error handling.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a valid string.")
    if data and not isinstance(data, dict):
        raise ValueError("Data must be a dictionary.")

    headers = await build_headers(url, account, method, data)
    if not headers:
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}No headers generated for URL: {urlparse(url).path}{Fore.RESET}")
        raise ValueError("Failed to generate headers")

    # Use dictionary-based proxy for tls-client
    proxy_url = {"http": account.proxy, "https": account.proxy} if account.proxy else None
    response = None

    try:
        session = tls_client.Session(
            client_identifier="safari15_5",
            random_tls_extension_order=True # Randomize TLS extension order to avoid detection
        )

        if proxy_url:
            session.proxies = proxy_url

        session.headers = headers
        time.sleep(random.uniform(2, 5))

        # Send request
        if method == "GET":
            response = session.get(url, headers=headers, proxy=proxy_url, timeout_seconds=timeout)
        else:
            response = session.post(url, json=data, headers=headers, proxy=proxy_url, timeout_seconds=timeout)

        # Handle HTTP errors explicitly
        if response.status_code == 403:
            raise Exception("HTTP 403")  # Explicitly raise 403 for retry handling
        elif response.status_code >= 400:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        return response.json()  # Parse JSON response

    except Exception as e:
        error_message = str(e)

        if "timeout" in error_message.lower() or "request canceled" in error_message.lower():
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Connection timed out after {timeout} seconds{Fore.RESET}")
            time.sleep(random.uniform(5, 10))

        return None

# Function to send HTTP requests with retry logic using exponential backoff
async def retry_request(url, data, account, method="POST", max_retries=3):
    """
    Retry requests using exponential backoff.
    """
    for retry_count in range(max_retries):
        try:
            response = await send_request(url, data, account, method)
            if response:
                return response  # Return the response if successful

        except Exception as e:
            error_message = str(e)

            if "HTTP 403" in error_message:
                logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}403 Forbidden: Check permissions or proxy{Fore.RESET}")
                time.sleep(random.uniform(5, 10))

            else:
                logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Error: {e}{Fore.RESET}")

        # Exponential backoff delay before the next retry
        delay = await exponential_backoff(retry_count)
        logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Retry {retry_count + 1}/{max_retries}: Waiting {delay:.2f} seconds...")
        await asyncio.sleep(delay)  # Use asyncio.sleep for async compatibility

    logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Max retries reached for URL: {urlparse(url).path}{Fore.RESET}")
    return None

# Function to implement exponential backoff delay during retries
async def exponential_backoff(retry_count, base_delay=1):
    """
    Perform exponential backoff for retries.
    """
    delay = min(base_delay * (2 ** retry_count) + random.uniform(0, 1), 30)
    return delay  # Return delay value
