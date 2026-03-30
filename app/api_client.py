import aiohttp
import asyncio
import logging
import time
from app.models import DeviceResponse
from typing import List

pipeline_start = time.perf_counter()
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 1  
REQUEST_TIMEOUT = 5

# protects API from overload when implemented
semaphore = asyncio.Semaphore(10)

async def fetch_device_info(
    session: aiohttp.ClientSession, 
    device_id: str
    ) -> DeviceResponse :
    request_created = time.perf_counter()
    request_started = None
    request_finished = None
    

    url = f"https://postman-echo.com/get?device_id={device_id}"

    async with semaphore:
        request_started = time.perf_counter()
        logger.debug(f"[API CALL] device_id={device_id} url={url}")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()

                
                request_finished = time.perf_counter()

                api_latency = request_finished - request_started
                queue_time = request_started - request_created
                end_to_end_latency = request_finished - pipeline_start

                logger.debug(f"Device {device_id} completed in g {api_latency:.3f}s")

                return DeviceResponse(
                    device_id=device_id,
                    data=data,
                    error=None,
                    api_latency=api_latency,
                    queue_time=queue_time,
                    end_to_end_latency=end_to_end_latency,
                )

            except asyncio.TimeoutError:
                logger.warning(f"Timeout on attempt {attempt}/{MAX_RETRIES} for {device_id}")
                await asyncio.sleep(RETRY_DELAY)
                continue
            except aiohttp.ClientConnectionError as e:
                #logger.warning(f"HTTP error {e.status} on attempt {attempt} for {device_id}")
                await asyncio.sleep(RETRY_DELAY)
                continue
            except aiohttp.ClientResponseError as e:
                logger.warning(f"HTTP error {e.status} on attempt {attempt}/{MAX_RETRIES} for {device_id}")
                if e.status < 500:
                    break  # don't retry client errors (400, 404, etc.)
            except Exception as e:
                logger.exception(f"Unexpected error for {device_id}: {e}")
                break # no retry if exception is unknown

            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY * attempt)
        
        request_finished = time.perf_counter()

        api_latency = request_finished - request_started
        queue_time = request_started - request_created
        end_to_end_latency = request_finished - pipeline_start

        logger.error(
            f"Device Fetching failed {device_id} (url={url}) after {end_to_end_latency:.3f}s "
            f"(api={api_latency:.3f}s, queue={queue_time:.3f}s)"
        )
            
        return DeviceResponse(
            device_id=device_id,
            data=None,
            error="API failed after retries",
            api_latency=api_latency,
            queue_time=queue_time,
            end_to_end_latency=end_to_end_latency,
            )

async def fetch_all_devices(device_ids: list[str]) -> List[DeviceResponse]:

    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        tasks = [fetch_device_info(session, device_id) for device_id in device_ids]

        logger.info(f"Starting API enrichment for {len(device_ids)} devices...")

        results : list[DeviceResponse] = await asyncio.gather(*tasks)

        # log summary for Api calling
        success = 0
        failed = 0

        for result in results:
            if result.error is not None:
                logger.warning(f"Device {result.device_id} failed: {result.error}")
                failed += 1
            else:
                success += 1

        logger.info(f"API enrichment complete: {success} success, {failed} failed")
        return results
