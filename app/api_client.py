import aiohttp
import asyncio
import logging
import time

start = time.perf_counter()
logger = logging.getLogger(__name__)

# protects API from overload when implemented in line 14
semaphore = asyncio.Semaphore(10)


async def fetch_device_info(session, device_id):

    url = f"https://postman-echo.com/get?device_id={device_id}"

    async with semaphore:
        logger.debug(f"[API CALL] device_id={device_id} url={url}")

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                
            duration = time.perf_counter() - start

            logger.debug(f"Device {device_id} completed in {duration:.3f}s")

            # returns a coroutine
            return {
                "device_id": device_id, 
                "data": data, 
                "error": None,
                "duration": duration
                }

        except Exception as e:
            duration = time.perf_counter() - start

            logger.error(
                f"failed to fetch device {device_id} (url={url}) after {duration:.3f}s: {e}", 
                exc_info=True
            )
            # returns coroutine
            return {
                "device_id": device_id, 
                "data": None, 
                "error": str(e),
                "duration": duration
                }


async def fetch_all_devices(device_ids):

    timeout = aiohttp.ClientTimeout(total=5)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        #each task is a coroutine object, not yet executed/run
        tasks = [fetch_device_info(session, device_id) for device_id in device_ids]

        logger.info(f"Starting API enrichment for {len(device_ids)} devices...")
        #execute all coroutines concurrently and collect results (list of dicts)
        results = await asyncio.gather(*tasks)

        # log summary for Api calling
        success = 0
        failed = 0

        for result in results:
            if result["error"] is not None:
                logger.warning(
                    f"Device {result['device_id']} failed: {result['error']}"
                )
                failed += 1
            else:
                success += 1

        logger.info(f"API enrichment complete: {success} success, {failed} failed")
        return results
