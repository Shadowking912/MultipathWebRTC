import asyncio

# Define the first async function
async def say_hello():
    await asyncio.sleep(10)
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
    # await task1
    # await task2
    print("gg")

if 
asyncio.run(main())