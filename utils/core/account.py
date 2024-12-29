import asyncio
import time

from utils.network import get_profile_info, ping_all_accounts
from utils.services import get_proxy_choice, assign_proxies
from utils.services import processed_tokens, load_tokens, send_request
from utils.settings import ACTIVATE_ACCOUNTS, DAILY_CLAIM, logger, Fore
from utils.settings import DOMAIN_API, CONNECTION_STATES, setup_logging, startup_art


# Account class to hold token, proxy, and other details for each account
class AccountData:
    def __init__(self, token, index, proxy=None):
        self.token = token
        self.index = index
        self.proxy = proxy

        # Set the initial connection status to 'None' (no connection)
        self.status_connect = CONNECTION_STATES["NONE_CONNECTION"]
        self.points_per_proxy = {}
        self.account_info = {}
        self.claimed_rewards = set()
        self.retries = 0
        self.last_ping_status = 'Waiting...'

        # Initialize a list to hold browser session details (such as ping counts and scores)
        self.browser_ids = [
            {
                'ping_count': 0,
                'successful_pings': 0,
                'score': 0,
                'start_time': time.time(),
                'last_ping_time': None
            }
        ]

    # Reset account state for retries or disconnection
    def reset(self):
        self.status_connect = CONNECTION_STATES["NONE_CONNECTION"]
        self.account_info = {}
        self.retries = 3
        logger.info(f"{Fore.CYAN}00{Fore.RESET} - {Fore.GREEN}Resetting account {self.index}{Fore.RESET}")

# Activate accounts and update their status
async def activate_accounts(accounts) -> None:
    if isinstance(accounts, AccountData):
        accounts = [accounts]

    tasks = [send_request(DOMAIN_API["ACTIVATE"], {}, account, method="POST") for account in accounts]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    for account, response in zip(accounts, responses):
        if isinstance(response, Exception):
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Error activating account {account.index}: {response}{Fore.RESET}")
            account.status_connect = CONNECTION_STATES["NONE_CONNECTION"]
            continue

        if response and response.get("code") == 5 and "already activated" in response.get("msg", "").lower():
            account.status_connect = CONNECTION_STATES["CONNECTED"]
            logger.debug(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.GREEN}Account {account.index} is already activated.{Fore.RESET}")

        elif response and response.get("success") and response.get("data") is True:
            account.status_connect = CONNECTION_STATES["CONNECTED"]
            logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.GREEN}Account {account.index} activated successfully.{Fore.RESET}")

# Synchronize account data by fetching profile and earning information
async def process_account(account):
    try:
        await get_profile_info(account)
    except Exception as e:
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Error processing account {account.index}: {e}{Fore.RESET}")

# Main function to manage the application flow
async def process():
    startup_art()
    setup_logging()

    proxies = get_proxy_choice()
    tokens = await load_tokens()

    logger.info(f"{Fore.CYAN}00{Fore.RESET} - {Fore.GREEN}Proceeding with{'out proxies...' if not proxies else ' proxies...'}{Fore.RESET}")

    token_proxy_pairs = assign_proxies(tokens, proxies)
    accounts = [AccountData(token, index, proxy) for index, (token, proxy) in enumerate(token_proxy_pairs, start=1)]

    if ACTIVATE_ACCOUNTS:
        await activate_accounts(accounts)

    while True:
        try:
            if DAILY_CLAIM:
                processed_tokens.clear()
                logger.info(f"{Fore.CYAN}00{Fore.RESET} - Loading account details, checking rewards, and claiming. Please wait...")
                await asyncio.sleep(3)

                # Collect tasks related to accounts: syncing profiles and fetching total points
                tasks = [asyncio.create_task(process_account(account)) for account in accounts]
                await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(f"{Fore.CYAN}00{Fore.RESET} - Preparing to send ping, please wait...")
            await asyncio.sleep(3)

            # Ping all accounts to keep their sessions active
            await ping_all_accounts(accounts)

        except asyncio.CancelledError:
            print("Main loop interrupted. Cleaning up...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in the main loop: {e}")
