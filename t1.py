import asyncio

async def task_one():
    print("Task One: Starting")
    await asyncio.sleep(2)  # Non-blocking sleep for 2 seconds
    print("Task One: Done")
    return 1

async def task_two():
    print("Task Two: Starting")
    await asyncio.sleep(1)  # Non-blocking sleep for 1 second
    print("Task Two: Done")
    return 2
tasks = []
async def main():
    # for i in range(2):
    tasks.append(asyncio.create_task(task_one()))
    tasks.append(asyncio.create_task(task_two()))

    results=await asyncio.gather(*tasks)
    print(results)
    # await asyncio.gather(task_one(), task_two())  # Run both tasks concurrently

# Run the async function
asyncio.run(main())
