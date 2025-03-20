from colorama import Style
from datetime import timedelta

from utils.settings import DOMAIN_API, logger, Fore
from utils.services import retry_request, mark_token, mask_token


# Function to display account information
def display_account_info(account, data):
    logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.LIGHTMAGENTA_EX}Account Info for {data['name']}{Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Email: {Fore.CYAN}{data['email']}{Fore.RESET}")
    logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Referral Link: {Fore.CYAN}{data['referral_link']}{Fore.RESET}")
    logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - State: {Fore.CYAN}{data['state']}{Fore.RESET}")
    logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Network Earning Rate: {Fore.CYAN}{data['network_earning_rate']}{Fore.RESET}")

# Function to display earning information
def display_earning_info(account, data):
    logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.LIGHTMAGENTA_EX}Status of {data['season_name']}{Style.RESET_ALL}")
    logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Total Earning: {Fore.CYAN}{data['total_earning']}{Fore.RESET}")
    logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Today Earning: {Fore.CYAN}{data['today_earning']}{Fore.RESET}")
    logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Current Point: {Fore.CYAN}{data['current_point']}{Fore.RESET}")
    logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Pending Point: {Fore.CYAN}{data['pending_point']}{Fore.RESET}")

# Function to get reward mapping
def get_reward_mapping():
    return {
        "1": {"name": "Daily", "required": None, "is_progress_based": False},
        "19": {"name": "Hourly", "required": None, "is_progress_based": True},
        "15": {"name": "7 Day", "required": None, "is_progress_based": False},
        "16": {"name": "14 Day", "required": "7-Day", "is_progress_based": False},
        "17": {"name": "21 Day", "required": "14-Day", "is_progress_based": False},
        "18": {"name": "28 Day", "required": "21-Day", "is_progress_based": False}
    }

# Fetch and display profile information for the account
async def get_profile_info(account):
    try:
        # Check if the token is already processed
        if not await mark_token(account):
            logger.debug(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.YELLOW}Token already processed. Skipping...{Fore.RESET}")
            return

        # Log separator for better readability
        separator_line = f"{Fore.CYAN + Style.BRIGHT}-" * 75 + f"{Style.RESET_ALL}"

        if account.index == 1:
            logger.info(separator_line)

        # Fetch account profile details
        logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Fetching profile details with token: {Fore.CYAN}{mask_token(account.token)}{Fore.RESET}")
        response = await retry_request(DOMAIN_API["SESSION"], {}, account)

        if response.get("success"):
            logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - Profile details fetched {Fore.GREEN}successfully{Fore.RESET}")
            account.account_info = response["data"]
            data = account.account_info

            # Display account info
            logger.info(separator_line)
            display_account_info(account, data)

            if account.account_info.get("uid"):
                await get_earning_info(account)
                await process_and_claim_rewards(account)

            logger.info(separator_line)

        else:
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Session failed for token{Fore.RESET} "
                         f"{Fore.CYAN}{mask_token(account.token)}{Fore.RESET}: {Fore.RED}Np Token Expired{Fore.RESET}")

    except Exception as e:
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Profile fetch failed with token:{Fore.RESET} "
                     f"{Fore.CYAN}{mask_token(account.token)}{Fore.RESET}")

        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Response content:{Fore.RESET} {e.response.text}")

# Fetch and display the earning information of an account
async def get_earning_info(account):
    try:
        response = await retry_request(DOMAIN_API["EARN_INFO"], {}, account, method="GET")

        if not response or not response.get('success'):
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Unable to fetch earning info. Response:{Fore.RESET} {response}")
            return

        data = response.get('data', {})
        if not isinstance(data, dict):
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Invalid data structure received for earning info{Fore.RESET}")
            return

        # Display earning information using the new function
        display_earning_info(account, data)

    except Exception as e:
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Failed to fetch earning info:{Fore.RESET} {e}")

# Handle checking and claiming rewards for an account
async def process_and_claim_rewards(account):
    try:
        response = await retry_request(DOMAIN_API["MISSION"], {}, account, method="GET")

        # Check if response is None
        if response is None:
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}No response received for mission data{Fore.RESET}")
            return

        # Ensure response contains 'success'
        if not response.get('success'):
            logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Failed to fetch mission data:{Fore.RESET} {response}")
            return

        data = response.get('data', [])

        # Ensure 'data' is a list
        if not isinstance(data, list):
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Unexpected data format:{Fore.RESET} {data}")
            return

        if not data:
            logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.YELLOW}No missions found{Fore.RESET}")
            return

        logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.LIGHTMAGENTA_EX}Checking rewards for account {account.index}{Style.RESET_ALL}")

        reward_mapping = get_reward_mapping()

        for item in data:
            if not isinstance(item, dict):
                logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Invalid mission format:{Fore.RESET} {item}")
                continue

            # Get reward info safely
            reward_info = reward_mapping.get(str(item.get('id')))

            if reward_info:
                if reward_info["required"] and reward_info["required"] not in account.claimed_rewards:
                    continue
                await claim_reward(account, item, reward_info["name"], reward_info["required"], reward_info["is_progress_based"])

    except Exception as e:
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Error checking rewards:{Fore.RESET} {e}")

# Handle the process of claiming daily rewards for an account
async def claim_reward(account, reward_data, reward_name, required_claim=None, is_progress_based=False):
    current_process = reward_data.get('current_process', 0)
    target_process = reward_data.get('target_process', 1)

    # Handle rewards based on progress or availability
    if is_progress_based and current_process < target_process:
        logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.YELLOW}{reward_name} is not ready yet. Progress: {current_process}/{target_process}{Fore.RESET}")
        return

    # Reward available for claiming
    if reward_data.get('status') == "AVAILABLE":
        logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.GREEN}{reward_name} reward is available for claiming{Fore.RESET}")
        await complete_reward_claim(account, reward_data['id'], reward_name)
        account.claimed_rewards.add(reward_name.replace(" ", "-"))

    # Reward locked, handle locked and progress-based cases
    elif reward_data.get('status') == "LOCK":
        if current_process < target_process:
            logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.YELLOW}{reward_name} is locked. Progress: {current_process}/{target_process}{Fore.RESET}")

        elif current_process == target_process:
            logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.GREEN}{reward_name} completed, locked. Transitioning{Fore.RESET}")
            # Optionally try to claim again or mark it as ready

        else:
            remain_time = int(reward_data.get('remain_time', 0)) / 1000
            time_remaining = str(timedelta(seconds=remain_time)).split('.')[0]
            logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.YELLOW}{reward_name} will be available in... {time_remaining}{Fore.RESET}")

    # Reward will be available soon (handle unanticipated or specific statuses)
    elif reward_data.get('status') in ["SOON", "PENDING", "WAITING"]:
        remain_time = int(reward_data.get('remain_time', 0)) / 1000
        time_remaining = str(timedelta(seconds=remain_time)).split('.')[0]
        logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.YELLOW}{reward_name} will be available in... {time_remaining}{Fore.RESET}")

    # Handle rewards that are already completed
    elif reward_data.get('status') == "COMPLETED":
        logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.GREEN}{reward_name} has already been completed and claimed{Fore.RESET}")
        account.claimed_rewards.add(reward_name.replace(" ", "-"))

    else:
        logger.warning(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Unhandled status '{reward_data.get('status')}' for {reward_name}.{Fore.RESET}")

# Finalize the reward claim and print the results
async def complete_reward_claim(account, mission_id, reward_type):
    try:
        data = {"mission_id": str(mission_id)}

        response = await retry_request(DOMAIN_API["COMPLETE_MISSION"], data, account)

        # Check if response is None
        if response is None:
            logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}No response received for claiming {reward_type} reward.{Fore.RESET}")
            return

        # Process response if successful
        if response.get('success'):
            earned_points = response.get('data', {}).get('earned_points', 0) # Avoid KeyError
            logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.GREEN}{reward_type} Reward Claimed:{Fore.RESET} {Fore.CYAN}{earned_points} points{Fore.RESET}")
        else:
            logger.info(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Failed to claim {reward_type} reward:{Fore.RESET} {Fore.RED}{response}{Fore.RESET}")

    except Exception as e:
        logger.error(f"{Fore.CYAN}{account.index:02d}{Fore.RESET} - {Fore.RED}Error claiming {reward_type} reward:{Fore.RESET} {Fore.RED}{e}{Fore.RESET}")
