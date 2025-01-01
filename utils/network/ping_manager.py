import asyncio
import time

from colorama import Style
from urllib.parse import urlparse

from utils.services import retry_request, mask_token, resolve_ip
from utils.settings import DOMAIN_API, PING_DURATION, PING_INTERVAL, logger, Fore


# Send periodic pings to the server for the given account
async def process_ping_response(response, url, account, data):
    if not response or not isinstance(response, dict):
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Invalid or empty response. {response}{Fore.RESET}")
        return "failed", None

    response_data = response.get("data", {})
    if not isinstance(response_data, dict):
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Invalid 'data' field in response: {response_data}{Fore.RESET}")
        return "failed", None

    logger.debug(
        f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Response {{"
        f"Success: {response.get('success')}, Code: {response.get('code')}, "
        f"IP Score: {response.get('data', {}).get('ip_score', 'N/A')}, "
        f"Message: {response.get('msg', 'No message')}}}"
    )

    try:
        version = response_data.get("version", "2.2.7")
        data["version"] = version

        ping_result = "success" if response.get("code", -1) == 0 else "failed"
        network_quality = response_data.get("ip_score", "N/A")

        account_stats = account.browser_ids[0]
        account_stats.setdefault("ping_count", 0)
        account_stats.setdefault("score", 0)
        account_stats.setdefault("successful_pings", 0)

        account_stats['ping_count'] += 1
        if ping_result == "success":
            account_stats['score'] += 10
            account_stats["successful_pings"] += 1
        else:
            account_stats['score'] -= 5

        logger.debug(
            f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - "
            f"Browser Stats {{Ping Count: {account.browser_ids[0]['ping_count']}, "
            f"Success: {account.browser_ids[0]['successful_pings']}, "
            f"Score: {account.browser_ids[0]['score']}, "
            f"Last Ping: {account.browser_ids[0]['last_ping_time']:.2f}}}"
        )

        return ping_result, network_quality

    except (AttributeError, KeyError, TypeError) as e:
        short_error = str(e).split(". See")[0]
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Error processing response: {short_error}{Fore.RESET}")
        return "failed", None

# Function to start the ping process for each account
async def start_ping(account):
    current_time = time.time()

    separator_line = f"{Fore.CYAN + Style.BRIGHT}-" * 75 + f"{Style.RESET_ALL}"

    if account.index == 1:
        logger.debug(separator_line)

    # Validate browser_ids
    if not account.browser_ids or not isinstance(account.browser_ids[0], dict):
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Invalid or missing browser_ids structure{Fore.RESET}")
        return

    account.browser_ids[0].setdefault('ping_count', 0)
    account.browser_ids[0].setdefault('score', 0)

    last_ping_time = account.browser_ids[0].get('last_ping_time', 0)
    logger.debug(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Current time: {current_time}, Last ping time: {last_ping_time}")

    if last_ping_time and (current_time - last_ping_time) < PING_INTERVAL:
        logger.warning(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.YELLOW}Hold on! Please wait a bit longer before trying again{Fore.RESET}")
        return

    account.browser_ids[0]['last_ping_time'] = current_time

    # Start ping loop
    for url in DOMAIN_API.get("PING", []):
        try:
            logger.debug(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Sending ping to {urlparse(url).path}")
            data = {
                "id": account.account_info.get("uid"),
                "browser_id": account.browser_ids[0],
                "timestamp": int(time.time()),
            }

            # Send request with retry handling
            response = await retry_request(url, data, account)
            if response is None:
                continue
        
            ping_result, network_quality = await process_ping_response(response, url, account, data)

            logger.debug(separator_line)

            identifier = await resolve_ip(account)
            logger.info(
                f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - "
                f"{Fore.GREEN if ping_result == 'success' else Fore.RED}Ping {ping_result}{Fore.RESET}, "
                f"Token: {Fore.CYAN}{mask_token(account.token)}{Fore.RESET}, "
                f"IP Score: {Fore.CYAN}{network_quality}{Fore.RESET}, "
                f"{'Proxy' if account.proxy else 'IP Address'}: {Fore.CYAN}{identifier}{Fore.RESET}"
            )

            if ping_result == "success":
                break

        except KeyError as ke:
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}KeyError during ping: {ke}{Fore.RESET}")

# Ping all accounts periodically
async def ping_all_accounts(accounts):
    start_time = time.time()

    while time.time() - start_time < PING_DURATION:
        try:
            # Ping all accounts concurrently
            tasks = [start_ping(account) for account in accounts]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log errors for failed accounts
            for account, result in zip(accounts, results):
                if isinstance(result, Exception):
                    logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Error pinging account: {result}{Fore.RESET}")

        except Exception as e:
            short_error = str(e).split(". See")[0]
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Unexpected error in ping_all_accounts: {short_error}{Fore.RESET}")

        logger.info(f"{Fore.CYAN}00{Fore.RESET} - Sleeping for {PING_INTERVAL} seconds before the next round")
        await asyncio.sleep(PING_INTERVAL)
