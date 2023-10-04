import asyncio, aiohttp
import logging, platform, sys, json
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

### py -m main 3 AUD

# LOGGER CONFG
### put level=logging.INFO to disable debug
logging.basicConfig(
    format="%(asctime)s | [%(levelname)s] | %(message)s",
    level=logging.DEBUG,
    handlers=[logging.StreamHandler()],
)

# CONSTANT
GET_URL_TEMPLATE = "https://api.privatbank.ua/p24api/exchange_rates?json&date="
BASIC_CURRENCY_LIST = ["USD", "EUR"]


### INTERFACES
class IO(ABC):
    @abstractmethod
    def do_output(self):
        ...

    @abstractmethod
    def parse_input(self):
        ...


class ConsoleIO(IO):
    def __init__(self) -> None:
        super().__init__()
        self.DAYS = int(sys.argv[1])
        logging.debug(f"SELF DAYS: {self.DAYS}")
        self.currency_list = BASIC_CURRENCY_LIST

    async def do_output(self, parsed_dict: dict) -> None:
        logging.debug(f"do_output revieved 'parsed_dict': {parsed_dict}")
        for (
            date,
            currency_data,
        ) in parsed_dict.items():  # cycling through each currency in the responce
            logging.debug(f"date, currency_data: {date}, {currency_data}")
            logging.info("+" * 10)
            logging.info(f"Date: {date}")
            logging.info("+" * 10)
            for (
                currency_data_dict
            ) in currency_data:  # extracting dicts with currency_data from the list
                if (
                    currency_data_dict["currency"] in self.currency_list
                ):  # checking if current currency is on our desired list
                    logging.debug(f"'currency_data_dict': {currency_data_dict}")
                    logging.debug(
                        f"'currency_data_dict['currency']': {currency_data_dict['currency']}"
                    )
                    logging.info(
                        f"{currency_data_dict['currency']} sale: {currency_data_dict['saleRateNB']}"
                    )
                    logging.info(
                        f"{currency_data_dict['currency']} purchase: {currency_data_dict['purchaseRateNB']}"
                    )
                    logging.info("-" * 10)

    def save_to_file(self, data: dict) -> None:
        with open("currencies.json", "w") as afp:
            json.dump(data, afp, indent=2)

    async def parse_input(self, command_args: list = sys.argv) -> None:
        try:
            command_args[2]
        except IndexError:
            ...
        else:
            logging.debug("HAVE ADDITIONAL CURRENCIES!")
            [self.currency_list.append(currency) for currency in command_args[2:]]
        finally:
            logging.debug(f"Currency list: {self.currency_list}")
            await self._check_days()

    async def _check_days(self) -> None:
        if self.DAYS > 10:
            logging.info(
                "Maximum range is 10 days. Will return results for 10 days now!"
            )
            self.DAYS = 10
        elif self.DAYS <= 0:
            logging.info(
                "Minumum range is 1 days (for today). Will return results for today now!"
            )
            self.DAYS = 1


class Handler(ABC):
    ...


class PrivatAPIHandler(Handler):
    async def exchange(self, dates: list[datetime]) -> list[dict]:
        responces_list = []
        logging.debug(f"DATES: {dates}")
        async with aiohttp.ClientSession() as session:
            # for date in dates:
            coroutines = [self.send_request(session, date) for date in dates]
            responses = await asyncio.gather(*coroutines)
            for response in responses:
                if response:
                    responces_list.append(response)

        return responces_list

    async def send_request(
        self, session: aiohttp.ClientSession, date: datetime
    ) -> None | dict:
        get_date = date.strftime("%d.%m.%Y")  # 01.12.2014
        get_url = GET_URL_TEMPLATE + get_date
        logging.debug(
            f"CRAFTED URL: {get_url}"
        )  # https://api.privatbank.ua/p24api/pubinfo?exchange&coursid=11
        try:
            async with session.get(get_url) as response:
                logging.debug(f"Status: {response.status}")
                logging.debug(f"Type: {response.headers['content-type']}")
                if response.status == 200:
                    result = await response.json()
                    logging.debug(f"GOT RESULT: {result}")
                    return result
                else:
                    logging.error(f"Error status: {response.status} for {get_url}")

        except aiohttp.ClientConnectionError as error:
            logging.error(f"Error Connection: {str(error)} for {get_url}")
            return None

    async def time_machine_date_checker(
        self, days: int, todays_date: datetime
    ) -> list[datetime]:
        dates_list = []
        for i in range(days):
            delta = timedelta(days=i)
            back_date = todays_date - delta
            dates_list.append(back_date)
            logging.debug(f"DATES FROM TM: {dates_list}")
        return dates_list

    async def parse_result(
        self, result: list[dict], currency_list: list[str]
    ) -> dict[str:list]:
        only_desired_currencies_dict = {}
        for item in result:  # cycling through each day in the range
            currency_dict_list = item[
                "exchangeRate"
            ]  # taking list of dictionaries from the JSON of that date (API specific)
            only_desired_currencies_dict[item["date"]] = []
            for (
                currency
            ) in currency_dict_list:  # cycling through each currency in the responce
                if (
                    currency["currency"] in currency_list
                ):  # checking if current currency is on our desired list
                    only_desired_currencies_dict[item["date"]].append(currency)
        logging.debug(f"Desired currencies list: {only_desired_currencies_dict}")
        return only_desired_currencies_dict


class UI(ABC):
    def __init__(self, io: IO, handler: Handler) -> None:
        super().__init__()
        self.io = io
        self.handler = handler

    @abstractmethod
    async def get_course(self, dates):
        await self.handler.exchange(dates)
        ...

    @abstractmethod
    async def display_info(self, data):
        await self.io.do_output(data)
        ...


class ExchangeUI(UI):
    async def get_dates(self, days: int) -> list[datetime]:
        todays_date = datetime.now()
        logging.debug(f"TODAY: {todays_date}")
        return await self.handler.time_machine_date_checker(days, todays_date)

    async def parse_exchanges(self, exchanges: list[dict]) -> dict[str:list]:
        return await self.handler.parse_result(exchanges, self.io.currency_list)

    async def get_course(self, dates: list[datetime]) -> list[dict]:
        return await self.handler.exchange(dates)

    async def display_info(self, parsed_list: dict[str:list]) -> None:
        await self.io.do_output(parsed_list)


class ConsoleUI(ExchangeUI):
    async def start(self) -> None:
        await self.io.parse_input()
        dates = await self.get_dates(
            self.io.DAYS
        )  # getting specific dates for set range in TM
        exchanges_list = await self.get_course(
            dates
        )  # getting list of JSONs  as response from API for each of the date from TM
        parsed_exchange = await self.parse_exchanges(
            exchanges_list
        )  # taking only currencies that we are interested in
        await self.display_info(parsed_exchange)  # show output
        await self.save_to_file(parsed_exchange)  # save output to JSON file
        logging.info(f"DONE!")

    async def save_to_file(self, parsed_list: dict[str:list]) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.io.save_to_file, parsed_list)


### EXECUTE
if __name__ == "__main__":
    io = ConsoleIO()
    handler = PrivatAPIHandler()
    ui = ConsoleUI(io, handler)

    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(ui.start())
