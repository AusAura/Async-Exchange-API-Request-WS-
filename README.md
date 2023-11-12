# Async-Exchange-API-Request(WS)
Get an actual currency exchange rate via CLI or web chat-like app (bot-like) by requesting it from the PrivatBank API. 

The chat is a simple... chat (supports sharing messages between some number of different clients) with additional bot-like functionality that checks sent messages for commands. If the WS server is hosted on the prod server in the internet, of course. If the command is found, runs some related code.

In our case, the only available command is 'exchange' that sends request to PrivatBank API.

- Made with SOLID principles, abstraction.
- Uses asyncio. Every request to the API is done asynchronously.
- Chat was made with WebSockets. 
- Displaying messages in the chat is done with JavaScript.
- Results are saved in currencies.json

### Usage:

**1) CLI interface:**
- Run the script in CLI with the parameters.
- Additional currencies should be separated with space.
- Basic currencies = USD and EUR. Could be changed in the main.py code.

CLI request example: py -m main 3 AUD 

(py -m main @for_how_many_days @additional_currencies)

**2) Chat interface:**
- Run the chat_server.py
- Run the chat_client.html
- Use it like a chat.
- Sent the request to get currency exchange rates.
- Minimal range - for today (1), maximum range - 10 days.

Chat request example: exchange USD,EUR,AUD 2 

(exchange @additional_currencies_separated_by_comma @for_how_recent_many_days)
