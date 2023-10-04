import asyncio
import logging
import websockets, aiopath
import names
from datetime import datetime
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from main import UI, ExchangeUI, PrivatAPIHandler, IO, Handler
from abc import ABC

### LOGGER CONFGS
apath= 'exchange.log'
stream_logger = logging.getLogger()
stream_log_handler = logging.StreamHandler()
stream_log_handler.setLevel(logging.INFO)
stream_formatter = logging.Formatter('%(asctime)s | %(message)s')
stream_log_handler.setFormatter(stream_formatter)
stream_logger.addHandler(stream_log_handler)

apath = aiopath.AsyncPath(apath)
file_logger = logging.getLogger()
file_log_handler = logging.FileHandler(apath)
file_log_handler.setLevel(logging.WARNING)
file_formatter = logging.Formatter('%(asctime)s | %(message)s')
file_log_handler.setFormatter(file_formatter)
file_logger.addHandler(file_log_handler)

# debug_logger = logging.getLogger()
# debug_log_handler = logging.StreamHandler()
# debug_log_handler.setLevel(logging.DEBUG)
# debug_formatter = logging.Formatter('%(asctime)s | [%(levelname)s] | %(message)s')
# debug_log_handler.setFormatter(debug_formatter)
# debug_logger.addHandler(debug_log_handler)

### LOGGING FUNCTIONS
def log_all(message):
        # self.debug_logger.debug(message)
        stream_logger.info(message)

def log_error(message):
        stream_logger.error(message)

def file_log(message):
        file_logger.warning(message)


###INTERFACES
class ChatUI(ExchangeUI):
    async def display_info(self, parsed_list: dict[str:list]) -> list[str]:
        return await self.io.do_output(parsed_list)
    
    async def log_to_file(self, parsed_list: dict[str:list]) -> None:
        await self.io.log_to_file(parsed_list)


class ChatIO(IO):
    def __init__(self) -> None:
        super().__init__()
        self.DAYS = 1
        self.currency_list = []
        logging.debug(f"ChatIO init: {self.currency_list}")

    async def parse_input(self, message: str) -> list[str] | str:
        try:
            parsed_message = message.split(' ')
            currencies = parsed_message[1]
            days = parsed_message[2]
        except IndexError:
            log_error(f'Parameters are not correct in request for "exchange": {message}!')
            return parsed_message[0]
        else:
            currencies = currencies.split(',')
            [self.currency_list.append(currency) for currency in currencies]
            log_all(f'PARSED CURRENCIES: {currencies}!')
            # file_logger.warning(f'PARSED CURRENCIES: {currencies}!')
            try:
                self.DAYS = int(days)
            except:
                log_error(f'Parameters are not correct in request for "exchange": {message}!')
                return parsed_message[0]
        finally:
            log_all(f"Currency list: {self.currency_list}")
            await self._check_days()
            return parsed_message

    async def _check_days(self) -> None:
        if self.DAYS > 10:
            log_all('Maximum range is 10 days. Will return results for 10 days now!')
            # file_logger.warning('Maximum range is 10 days. Will return results for 10 days now!')
            self.DAYS = 10
        elif self.DAYS <= 0:
            log_all('Minumum range is 1 days (for today). Will return results for today now!')
            # file_logger.warning('Minumum range is 1 days (for today). Will return results for today now!')
            self.DAYS = 1

    async def do_output(self, parsed_dict: dict) -> list[str]:
        answer_list = []
        log_all(f"do_output revieved 'parsed_dict': {parsed_dict}")
        for date, currency_data in parsed_dict.items(): #cycling through each currency in the responce
                log_all(f"date, currency_data: {date}, {currency_data}")
                message_date = f'Date: {date}\n' + f'{"-" * 10}\n'
                # file_logger.warning(f"1st stage message: {message_date}")
                if not currency_data:
                    message = message_date + f"Unfortunately, we do not have any data for this day yet."
                    answer_list.append(message)
                else:
                    message = message_date
                    for currency_data_dict in currency_data: #extracting dicts with currency_data from the list
                        # file_logger.warning(f"LOOPING THROUGH THE CURRENCY_DATA: {currency_data}, \n specifically - {currency_data_dict}")
                        # file_logger.warning(f"Current currency: {currency_data_dict['currency']}")
                        if currency_data_dict['currency'] in self.currency_list: #checking if current currency is on our desired list
                            # log_all(f"")
                            message += (
                                f"{currency_data_dict['currency']} sale: {currency_data_dict['saleRateNB']}\n" +
                                f"{currency_data_dict['currency']} purchase: {currency_data_dict['purchaseRateNB']}\n"
                            )
                    answer_list.append(message)
                    # file_logger.warning(f"2nd stage message: {message}")
        # file_logger.warning(f"Answer list content: {answer_list}")
        return answer_list
    
    async def log_to_file(self, data: dict[str: list]) -> None:
        # apath = aiopath.AsyncPath("exchange.log")
        # file_logger.warning(f"TRYING TO WRITE FILE: {...} WITH DATA {data}")
            # afp.write(data)
        file_log(f'{data}')


class Server(ABC):
    ...


class CurrencyChatServer(Server):
    def __init__(self, ui: UI, handler: Handler) -> None:
        self.clients = set()
        self.ui = ui
        self.handler = handler

    async def register(self, ws: WebSocketServerProtocol) -> None:
        ws.name = names.get_full_name()
        self.clients.add(ws)
        log_all(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol) -> None:
        self.clients.remove(ws)
        log_all(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str) -> None:
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol) -> None:
        await self.register(ws)
        try:
            await self.send_message(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def send_message(self, ws: WebSocketServerProtocol) -> None:
        async for message in ws:
            parsed_message = await self.ui.io.parse_input(message)
            log_all(f'TRYING TO LOOK FOR "exchange" IN REQUEST: {parsed_message}')
            # file_logger.warning(f'TRYING TO LOOK FOR "exchange" IN REQUEST: {parsed_message}')
            await self.send_to_clients(f"{ws.name}: {message}")

            if parsed_message[0] == 'exchange':
                log_all(f'I SEE THE REQUEST: {parsed_message[0]}')
                # file_logger.warning(f'I SEE THE REQUEST: {parsed_message[0]}') 
                info_for_sending = await self.get_exchange()
                log_all(f'THIS IS WHAT I HAVE FOR SENDING: {info_for_sending}')
                # file_logger.warning(f'THIS IS WHAT I HAVE FOR SENDING: {info_for_sending}') 

                await self.send_to_clients(f"This is what you asked for!\n")
                for info in info_for_sending:
                    if info:
                        await self.send_to_clients(info)

                self.ui.io.currency_list = []
                log_all(f'DONE!')
                # file_logger.warning(f'DONE!')    

    async def get_exchange(self) -> list[str]:
        dates = await self.ui.get_dates(self.ui.io.DAYS) #getting specific dates for set range in TM
        exchanges_list = await self.ui.get_course(dates) #getting list of JSONs  as response from API for each of the date from TM
        parsed_dist = await self.ui.parse_exchanges(exchanges_list)
        await self.ui.log_to_file(parsed_dist)
        info_for_sending = await self.ui.display_info(parsed_dist)
        return info_for_sending


async def main() -> None:
    server = CurrencyChatServer(ui, handler)
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    io = ChatIO()
    handler = PrivatAPIHandler()
    ui = ChatUI(io, handler)
    asyncio.run(main())