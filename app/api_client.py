import requests
import logging
import aiohttp
import asyncio


semaphore = asyncio.Semaphore(10)

async def fetch_device_info(session, device_id):
    url = f"https://postman-echo.com/get?device_id={device_id}"
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()


async def fetch_all_devices(device_ids):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_device_info(session, device_id) for device_id in device_ids]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

