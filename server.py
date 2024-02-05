import asyncio
import logging
import websockets
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from aiohttp import ClientSession
from aiofile import AIOFile
from aiopath import AsyncPath
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class Server:
    clients = set()
    exchange_command = 'exchange'

    @staticmethod
    def get_script_folder():
        return AsyncPath(__file__).parent

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = "User"
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def log_exchange_command(self):
        log_file_path = self.get_script_folder() / 'exchange_log.txt'
        async with AIOFile(log_file_path, 'a') as log_file:
            await log_file.write(f"Exchange command executed at {datetime.now()}\n")

    async def handle_exchange_command(self, ws: WebSocketServerProtocol):
        await self.log_exchange_command()
        async with ClientSession() as session:
            async with session.get('https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5') as response:
                if response.status == 200:
                    data = await response.json()
                    exchange_rates = ', '.join([f"{rate['ccy']}: {rate['buy']} / {rate['sale']}" for rate in data])
                    await ws.send(f"Exchange rates: {exchange_rates}")
                else:
                    await ws.send("Failed to fetch exchange rates")

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            async for message in ws:
                if message == self.exchange_command:
                    await self.handle_exchange_command(ws)
                else:
                    await self.send_to_clients(f"{ws.name}: {message}")
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())

