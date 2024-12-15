import asyncio
from threading import Thread
# Define the first async function
def write():
    while True:
        pass

async def say_hello():
    while True:
        await asyncio.sleep(3)
        print("Hello")

# Define the second async function
async def say_goodbye():
    print("Good Bye")

# Main function to launch the async functions
async def main():
    # Run the functions concurrently
    task1 = asyncio.create_task(say_hello())
    task2 = asyncio.create_task(say_goodbye())

    # Wait for both tasks to complete
    await task1
    # await task2
    print("gg")

thread=Thread(target=write)
thread.daemon=True
thread.start()
asyncio.run(main())