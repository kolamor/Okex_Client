import aiohttp
import asyncio
import json
import zlib
import copy

class BaseClient():
	"""docstring for BaseClient _init фабрика, замена __init__"""
	@classmethod
	async def _init(cls, **kwargs):
		self = cls()


		return self

	async def fetch_trades_history(self, send_json=None):
		self.send_json = self.trade_history if send_json is None else copy.deepcopy(send_json)
		print('=======', self.send_json)
		self.name = 'fetch_trades_history'
		return self

	async def fetch_candles(self, send_json=None):
		self.send_json = self.candles if send_json is None else copy.deepcopy(send_json)
		print("+++++++", self.send_json)
		self.name = 'fetch_candles'
		return self

	async def _fetch():
		pass

class OkexWSClient(BaseClient):
	"""docstring for OkexWSClient"""
	url = 'wss://real.okex.com:10440/ws/v1'
	trade_history = {'event':'addChannel','channel':'ok_sub_spot_btc_usdt_depth'}
	candles = {"event" : "addChannel", "channel" : "ok_sub_spot_bch_btc_ticker"}

	@classmethod
	async def _init(cls, **kwargs):
		self = cls()
		return self

	async def fetch_trades_history(self, send_json=None):
		self = await super().fetch_trades_history()
		async with aiohttp.ClientSession() as session:
			await self._fetch(session)

	async def fetch_candles(self, send_json=None):
		self = await super().fetch_candles()
		async with aiohttp.ClientSession() as session:
			await self._fetch(session)
	
	async def _fetch(self, session):
		async with session.ws_connect(self.url) as ws:
			await ws.send_json(self.send_json,  compress=None, dumps=json.dumps)
			print('Запрос ', self.name, ': ', self.send_json)
			async for msg in ws:
				if msg.type == aiohttp.WSMsgType.TEXT:
					print('Text: ', msg.data)
					if msg.data == 'close cmd':
						await ws.close()
						break
					else:
						pass
				elif msg.type == aiohttp.WSMsgType.ERROR:
					break
				elif msg.type == aiohttp.WSMsgType.PING:
					await ws.pong()
				elif msg.type == aiohttp.WSMsgType.BINARY:
					data = await self._inflate_decoding(msg.data)
					await OkexWSConverter.converter(data, self.name)
					await asyncio.sleep(1)
					
	
	async def _inflate_decoding(self, data):
		"""decoding inflate from WS Okex"""
		decompress = zlib.decompressobj(-zlib.MAX_WBITS)
		inflated = decompress.decompress(data)
		inflated += decompress.flush()
		return inflated



class OkexWSConverter():
	
	@staticmethod
	async def converter(data, name):
		print('-----WS--------------', name , '---------------------')
		print(data)


class OkexRESTClient(BaseClient):

	url = 'https://www.okex.com/api/v1/trades.do'
	trade_history = {'symbol' : 'ltc_btc'}
	candles = {'symbol': 'eth_btc'}

	async def fetch_candles(self):
		self = await super().fetch_candles()
		
		async with aiohttp.ClientSession() as session:
			while True:
				await self._fetch(session)


	async def fetch_trades_history(self):
		self = await super().fetch_trades_history()
		
		async with aiohttp.ClientSession() as session:
			while True:
				await self._fetch(session)
				

	async def _fetch(self, session):
		await asyncio.sleep(3)
		async with session.get(self.url, params=self.send_json) as response:
			data =  await response.json()
			await OkexRESTConverter.converter(data, self.name)
			return

class OkexRESTConverter():

	@staticmethod
	async def converter(data, name):
		print('-----REST--------------', name , '---------------------')
		print(data)



async def main():
    client_ws_2 = await OkexWSClient._init()
    await client_ws_2.fetch_candles()

async def main1():
    client_ws = await OkexWSClient._init()
    await client_ws.fetch_trades_history()

async def main2():
	client_rest = await OkexRESTClient._init()
	await client_rest.fetch_candles()

async def main3():
	client_rest = await OkexRESTClient._init()
	await client_rest.fetch_trades_history()

if __name__ == '__main__':
	loop = asyncio.get_event_loop()
	task = [
			loop.create_task(main()),
			loop.create_task(main1()),
			loop.create_task(main2()),
			loop.create_task(main3()),
		]
	wait_tasks = asyncio.wait(task)
	loop.run_until_complete(wait_tasks)
	# loop.run_until_complete(main())
