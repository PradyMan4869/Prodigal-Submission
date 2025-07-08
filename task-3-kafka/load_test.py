import requests
import json
import time
import uuid
import asyncio
import aiohttp

API_URL = "http://localhost:8080/register_event"
NUM_REQUESTS = 1000  # Number of requests to send
CONCURRENT_REQUESTS = 100 # How many requests to send in parallel

async def send_request(session, request_num):
    """Sends a single asynchronous request."""
    event_data = {
        "event_type": "page_view",
        "user_id": f"user_{uuid.uuid4()}",
        "payload": {
            "page_url": "/products/abc",
            "request_num": request_num
        }
    }
    try:
        async with session.post(API_URL, json=event_data) as response:
            if response.status == 200:
                # print(f"Request {request_num}: Success")
                return True
            else:
                print(f"Request {request_num}: Failed with status {await response.text()}")
                return False
    except aiohttp.ClientConnectorError as e:
        print(f"Request {request_num}: Connection error - {e}")
        return False


async def main():
    """Main function to run the load test."""
    print(f"Starting load test: {NUM_REQUESTS} requests with {CONCURRENT_REQUESTS} concurrency...")
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(NUM_REQUESTS):
            task = asyncio.create_task(send_request(session, i + 1))
            tasks.append(task)
            # To manage concurrency level
            if len(tasks) >= CONCURRENT_REQUESTS:
                await asyncio.gather(*tasks)
                tasks = []
        
        # Gather any remaining tasks
        if tasks:
            await asyncio.gather(*tasks)

    end_time = time.time()
    duration = end_time - start_time
    rps = NUM_REQUESTS / duration if duration > 0 else float('inf')

    print("\n--- Load Test Summary ---")
    print(f"Total requests sent: {NUM_REQUESTS}")
    print(f"Total time taken: {duration:.2f} seconds")
    print(f"Requests per second (RPS): {rps:.2f}")

if __name__ == "__main__":
    # Ensure you have aiohttp installed: pip install aiohttp
    asyncio.run(main())