import matplotlib.pyplot as plt
import matplotlib.animation as animation

def draw_latency_graph():
    snd_data= open("send_stats.txt","r").read()
    recv_data = open("incoming_stats.txt","r").read()     
    snd_data = snd_data.split("\n")
    recv_data = recv_data.split("\n")   
    # print(snd_data)
    # print(recv_data)
    snd_data = snd_data[:-1]
    recv_data = recv_data[:-1]  
    latencies=[]
    for i in range(len(recv_data)):
        snd_data[i] = float(snd_data[i])
        recv_data[i] = float(recv_data[i])
        latency = recv_data[i] - snd_data[i]    
        latencies.append(latency) 

    plt.plot(latencies)
    plt.show()

draw_latency_graph()
