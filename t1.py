import asyncio
from aiortc import RTCPeerConnection

async def get_data_channel_stats():
    # Create a new RTCPeerConnection
    pc = RTCPeerConnection()
    
    # Create a data channel
    data_channel = pc.createDataChannel("my-data-channel")
    
    # Wait for the data channel to be open (optional)
    @data_channel.on("open")
    async def on_open():
        print("Data channel is open!")
       
        # Get the stats report from the RTCPeerConnection
        stats = await pc.getStats()
        print(stats)
        # Iterate through the stats to find the data channel stats
        for report in stats.values():
            # if report.type == "data-channel":
                print("Data Channel Stats:")
                print(report)
    
    # Close the connection after some time (optional)
    await asyncio.sleep(10)
    await pc.close()

# Run the async function
asyncio.run(get_data_channel_stats())
