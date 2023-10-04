# Async-API-privat
Get an actual currency via CLI or web chat-like app.
Made with asyncio.

CLI request example: py -m main 3 AUD (py -m main @for_how_recent_many_days @additional_currencies)
Chat request example: exchange USD,EUR,AUD 2 (exchange @additional_currencies_separated_by_comma @for_how_recent_many_days)

For CLI, basic currencies = USD and EUR. Could be changed in the main.py.
Minimal range - for today (1), maximum range - 10 days.
