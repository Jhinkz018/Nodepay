
# NodepayBot - Ping Utility

**Nodepay Bot** is an automation tool designed to simplify tasks for Nodepay users. It supports multiple accounts, proxy integration, and automates activities such as account activation, reward claiming, and periodic pings to keep sessions active.

## Features

| Feature               | Description                                                             |
|-----------------------|-------------------------------------------------------------------------|
| **Multi-Account Management** | Seamlessly manage multiple accounts for efficient automation.       |
| **Proxy Integration**        | Enhance security and scalability by mapping accounts to proxies.   |
| **Automated Rewards**        | Automatically claim rewards based on activity progress to save time.|
| **Session Maintenance**      | Keep accounts active with periodic server pings.                  |
| **Insightful Logging**       | Gain visibility into account activities with a color-coded logging system.|

---

## Prerequisites

- **Python 3.8+**
- Dependencies listed in `requirements.txt`:
  - `aiohttp`
  - `asyncio`
  - `colorama`
  - `loguru`
  - `python-dotenv`
  - `requests`
  - `tls-client`
  - `typing_extensions`

## Installation
**Clone the repository:**
   ```bash
   git clone https://github.com/Enukio/NodepayBot.git
   ```
   ```bash
   cd NodepayBot
   ```

Then you can do automatic installation by typing:

Windows:
```shell
run.bat
```

Linux:
```shell
run.sh
```

# Windows manual installation
```shell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env-example .env
python main.py
```

# Linux manual installation
```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env-example .env
python3 main.py
```

# Termux manual installation
```
> pkg update && pkg upgrade -y
> pkg install python nodejs rust git -y
> git clone https://github.com/Enukio/NodepayBot.git
> cd NodepayBot
> pip install -r requirements.txt
> cp .env-example .env
> python main.py
```

---

## Prepare your environment
   - Set up `tokens.txt` and `proxies.txt` (instructions below).

## Get NP_TOKEN
Retrieving `np_token`: A quick guide to find your `np_token`:

- Open the webpage in your browser.
- Press `F12` or use `Ctrl + Shift + I` (Windows/Linux) / `Cmd + Option + I` (Mac) to open the developer console.
- Go to the **Console** tab.
- Enter the following command:

     ```javascript
     localStorage.getItem('np_token');
     ```
- The value displayed is your `np_token`.
- Save `np_token` to `tokens.txt`

## Setting up `tokens.txt`

The `tokens.txt` file stores the tokens for your accounts. Each line represents a single token. You can configure it in two ways depending on your requirements:

1. **One Token per Account**  
   If you are managing different accounts, list each token on a separate line:
   ```
   token1
   token2
   token3
   ```

2. **Reusing the Same Token for Multiple Accounts**  
   If you want to use the same token across multiple accounts (e.g., for testing or scaling purposes):
   ```
   token1
   token1
   token1
   ```

> **Note:** Ensure that the tokens correspond to valid and active accounts in the system.

---

## Setting up `proxies.txt`

The `proxies.txt` file is optional and allows you to use proxies for account operations. Each line represents one proxy. Follow these steps:

1. Create a file named `proxies.txt` in the root directory of the project.
2. Add your proxies, one per line, in the format:

   ```
   protocol://username:password@hostname:port
   ```
   Example:
   ```
   http://user1:pass1@proxy1.example.com:8080
   http://user2:pass2@proxy2.example.com:8080
   http://user3:pass2@proxy3.example.com:8080
   ```
4. Ensure the proxies are functional and correspond to your desired network configuration.

---

## Configuration

Set the following environment variables in a `.env` file:

| Variable           | Default Value | Description                                          |
|--------------------|---------------|------------------------------------------------------|
| `ACTIVATE_ACCOUNTS`| `False`       | Enables or disables account activation feature.      |
| `DAILY_CLAIM`      | `True`        | Enables or disables the daily claim feature.         |
| `PING_INTERVAL`    | `120`          | Time (in seconds) between pings to the server.       |
| `PING_DURATION`    | `3600`        | Total duration (in seconds) for periodic pinging.    |
| `REQUEST_TIMEOUT`  | `30`          | The default timeout (in seconds) for HTTP requests.  |
| `DEBUG`            | `False`       | Enables or disables debug mode.                      |

---

## Need Proxy?
1. Sign up at [Proxies.fo](https://app.proxies.fo/ref/d02516e7-56b3-9a1f-b7ca-1fb08669f7a6).
2. Go to [Plans](https://app.proxies.fo/plans) and only purchase the "ISP plan" (Residential plans don’t work).
3. Top up your balance, or you can directly buy a plan and pay with Crypto!
4. Go to the Dashboard, select your ISP plan, and click "Generate Proxy."
5. Set the proxy format to `protocol://username:password@hostname:port` and choose any number for the proxy count.
6. Paste the proxies into `proxies.txt`.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

### Support My Channel

[![Static Badge](https://img.shields.io/badge/Telegram-Channel-Link?style=for-the-badge&logo=Telegram&logoColor=white&logoSize=auto&color=blue)](https://t.me/AirdropHarvest)
