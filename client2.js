// get DOM elements
// var dataChannelLog1 = document.getElementById('data-channel1'),
    // dataChannelLog2 = document.getElementById('data-channel2'),
var iceConnectionLog = document.getElementById('ice-connection-state'),
    iceGatheringLog = document.getElementById('ice-gathering-state'),
    signalingLog = document.getElementById('signaling-state');
    livestream = document.getElementById('mode');
    ipaddr = null;
    num_connections=null;


livestream.addEventListener('change', function(){
    if (this.value=="livestream") {
        document.getElementById('remoteip').style.display = 'inline-block';
        document.getElementById('remotelabel').style.display='inline-block';
        document.getElementById('numconslabel').style.display='inline-block';
        document.getElementById('numconnections').style.display='inline-block';
    } else {
        document.getElementById('remoteip').style.display = 'none';
        document.getElementById('remotelabel').style.display='none';
        document.getElementById('numconnections').style.display='none';
        document.getElementById('numconslabel').style.display='none';
    }
});
// if(livestream.value=="livestream")
// {
//     document.getElementById('remoteip').style.display = 'inline-block';
// }
// peer connection


// data channel
var dc = null, dcInterval = null;

function createPeerConnection(conn_id) {
    var config = {
        sdpSemantics: 'unified-plan'
    };

    // if (document.getElementById('use-stun').checked) {
    //     config.iceServers = [{ urls: ['stun:stun.l.google.com:19302'] }];
    // }

    pc = new RTCPeerConnection(config);

    // register some listeners to help debugging
    pc.addEventListener('icegatheringstatechange', () => {
        iceGatheringLog.textContent += ' -> ' + pc.iceGatheringState;
    }, false);
    iceGatheringLog.textContent = pc.iceGatheringState;

    pc.addEventListener('iceconnectionstatechange', () => {
        iceConnectionLog.textContent += ' -> ' + pc.iceConnectionState;
    }, false);
    iceConnectionLog.textContent = pc.iceConnectionState;

    pc.addEventListener('signalingstatechange', () => {
        signalingLog.textContent += ' -> ' + pc.signalingState;
    }, false);
    signalingLog.textContent = pc.signalingState;

    // connect audio / video
    pc.addEventListener('track', (evt) => {
        if (evt.track.kind == 'video'){
            document.getElementById(`video${conn_id}`).srcObject = evt.streams[0];
        }
        else
            document.getElementById(`audio${conn_id}`).srcObject = evt.streams[0];
    });
    return pc;
}

function enumerateInputDevices() {
    const populateSelect = (select, devices) => {
        let counter = 1;
        devices.forEach((device) => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.text = device.label || ('Device #' + counter);
            select.appendChild(option);
            counter += 1;
        });
    };

    navigator.mediaDevices.enumerateDevices().then((devices) => {
        populateSelect(
            document.getElementById('audio-input'),
            devices.filter((device) => device.kind == 'audioinput')
        );
        populateSelect(
            document.getElementById('video-input'),
            devices.filter((device) => device.kind == 'videoinput')
        );
    }).catch((e) => {
        alert(e);
    });
}

function negotiate(pc){
    console.log("Negotiate");
    return pc.createOffer().then((offer) => {
        return pc.setLocalDescription(offer);
    }).then(() => {
        // wait for ICE gathering to complete
        return new Promise((resolve) => {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(() => {
        var offer = pc.localDescription;
        var codec;

        codec = document.getElementById('audio-codec').value;
        if (codec !== 'default') {
            offer.sdp = sdpFilterCodec('audio', codec, offer.sdp);
        }

        codec = document.getElementById('video-codec').value;
        if (codec !== 'default') {
            offer.sdp = sdpFilterCodec('video', codec, offer.sdp);
        }

        // document.getElementById('offer-sdp').textContent = offer.sdp;
        console.log(document.getElementById('mode').value)
        if(document.getElementById('mode').value=="livestream")
        {
            console.log(`${ipaddr}`);
            return fetch(`http://${ipaddr}/offer`, {
                body: JSON.stringify({
                    sdp: offer.sdp,
                    type: offer.type,
                    video_transform: document.getElementById('video-transform').value,
                    livestream: true,
                    num_connections:num_connections
                }),
                headers: {
                    'Content-Type': 'application/json'
                },
                method: 'POST'
            }).then((response) => {
                return response.json();
            }).then((answer) => {
                return pc.setRemoteDescription(answer);
            }).catch((e) => {
                alert(e);
            });

        }
        else
        {
            console.log("video-transform : ",document.getElementById('video-transform').value);
            console.log("webcam")
            return fetch(`/offer`, {
                body: JSON.stringify({
                    sdp: offer.sdp,
                    type: offer.type,
                    video_transform: document.getElementById('video-transform').value,
                    livestream:false,
                    num_connections:num_connections
                }),
                headers: {
                    'Content-Type': 'application/json'
                },
                method: 'POST'
            }).then((response) => {
                return response.json();
            }).then((answer) => {
                console.log("Answer : ",answer);
                // document.getElementById('answer-sdp').textContent = answer.sdp;
                return pc.setRemoteDescription(answer);
            }).catch((e) => {
                alert(e);
            });
        }
    });
}
function display_media_boxes()
{
    let num_connections = document.getElementById('numconnections').value;
    for(let i=0;i<num_connections;i++)
    {
        let inner = document.createElement('div');
        inner.id = `inner${i}`;
        inner.style.border='2px solid black';
        inner.style.width='100%';
        inner.style.height='60vh';
        inner.style.display='flex';
        inner.style.flexDirection='row';
        inner.style.justifyContent='space-around';

    
        let media = document.createElement('div');
        media.id = `media${i}`;
        media.style.display = 'none';
        // media.style.border ='2px solid violet';
        media.style.flex=1;
        media.style.height='100%';
        let h2 = document.createElement('h2');
        h2.innerHTML = 'Media';
        h2.style.fontSize = '2em';
        media.appendChild(h2);
        let audio = document.createElement('audio');
        audio.id = `audio${i}`;
        audio.setAttribute('autoplay',true);
        media.appendChild(audio);
        let video = document.createElement('video');
        video.id = `video${i}`;
        video.setAttribute('autoplay',true);
        video.setAttribute('playsinline',true);
        video.style.display = 'block';
        video.style.margin = 'auto';
        video.style.width = '80%';
        video.style.height = '80%';
        video.style.borderRadius = '2em';
        media.appendChild(video);
        inner.appendChild(media);
        let divData = document.createElement('div');
        let h2_1 = document.createElement('h2');
        h2_1.innerHTML = 'Data channel';
        h2_1.style.fontSize = '2em';
        // inner.appendChild(h2_1);
        divData.appendChild(h2_1);
        let pre = document.createElement('pre');
        pre.id = `data-channel${i+1}`;
        pre.style.height='80%';
        pre.style.overflowY = 'scroll';
        pre.style.fontSize= '1.5em';
        pre.style.border = '1px solid black';
        pre.style.width='80%';
        pre.style.margin='auto';
        pre.style.borderRadius = '1.2em';
        pre.style.textAlign = 'left';
        // pre.style.backgroundColor = 'white';
        divData.style.flex=1;
        divData.appendChild(pre);
        divData.maxHeight='100%';
        // divData.style.padding='2em';   
        // divData.style.border='2px solid black'
        // divData.width='80vw';
        inner.appendChild(divData);
        document.getElementById('container').appendChild(inner);
    }
    const event = new Event('elements_created');
    document.dispatchEvent(event);
}
function start() {
    // document.getElementById('start').style.display = 'none';
    // alert("start");
    document.getElementById('start').innerHTML="Stop";
    document.getElementById('start').setAttribute("onClick","stop()");
  

    document.addEventListener('elements_created',function()
    {
        let dataChannelLog=[]
        dataChannelLog.push(document.getElementById('data-channel1'));
        // console.log("Data Channel Log : ",dataChannelLog);
        inner = document.getElementById('inner0');
        console.log("Inner : ",inner);  
        
        if (document.getElementById('mode').value=="livestream") 
        {
            // let dataChannelLog=[]
            ipaddr = document.getElementById('remoteip').value;
            num_connections = document.getElementById('numconnections').value;
            
            // display_media_boxes(num_connections);
            console.log("Num Connections"+num_connections);
            for(let i=2;i<=num_connections;i++)
            {
                console.log("push");
                dataChannelLog.push(document.getElementById(`data-channel${i}`));
            }
            
            
            let pcs=[]
            for(let i=0;i<num_connections;i++)
            {   
                pc=createPeerConnection(i);
                pcs.push(pc);
                var time_start = null;
                const current_stamp = () => {
                    if (time_start === null) {
                        time_start = new Date().getTime();
                        return 0;
                    } else {
                        return new Date().getTime() - time_start;
                    }
                };
                    if (document.getElementById('use-datachannel').checked) {
                    var parameters = JSON.parse(document.getElementById('datachannel-parameters').value);
        
                    dc = pc.createDataChannel('chat', parameters);
                    dc.addEventListener('close', () => {
                        clearInterval(dcInterval);
                        dataChannelLog[i].textContent += '- close\n';
                    });
                    dc.addEventListener('open', () => {
                        dataChannelLog[i].textContent += '- open\n';
                        dcInterval = setInterval(() => {
                            var message = 'ping ' + current_stamp();
                            dataChannelLog[i].textContent += '> ' + message + '\n';
                            dc.send(message);
                        }, 1000);
                    });
                    dc.addEventListener('message', (evt) => {
                        dataChannelLog[i].textContent += '< ' + evt.data + '\n';

                        if (evt.data.substring(0, 4) === 'pong') {
                            var elapsed_ms = current_stamp() - parseInt(evt.data.substring(5), 10);
                            dataChannelLog[i].textContent += ' RTT ' + elapsed_ms + ' ms\n';
                        }
                    });
                }
                
            }

            // Build media constraints.
            const constraints = {
                audio: false,
                video: false
            };

            if (document.getElementById('use-audio').checked) {
                const audioConstraints = {};

                const device = document.getElementById('audio-input').value;
                if (device) {
                    audioConstraints.deviceId = { exact: device };
                }

                constraints.audio = Object.keys(audioConstraints).length ? audioConstraints : true;
            }

            if (document.getElementById('use-video').checked) {
                const videoConstraints = {};

                const device = document.getElementById('video-input').value;
                if (device) {
                    videoConstraints.deviceId = { exact: device };
                }

                const resolution = document.getElementById('video-resolution').value;
                if (resolution) {
                    const dimensions = resolution.split('x');
                    videoConstraints.width = parseInt(dimensions[0], 0);
                    videoConstraints.height = parseInt(dimensions[1], 0);
                }
                constraints.video = Object.keys(videoConstraints).length ? videoConstraints : true;
            }
            // Acquire media and start negociation.
            tasks=[]
            for(let i=0;i<num_connections;i++)
            {
                if (constraints.audio || constraints.video) {
                    if (constraints.video) {
                        // console.log('Media : ',document.getElementById(`inner${i}`));
                        document.getElementById(`media${i}`).style.display = 'block';
                        // document.getElementById('media2').style.display = 'block';
                    }
                    // return negotiate(pcs[i]);
                    navigator.mediaDevices.getUserMedia(constraints).then((stream) => {
                        console.log("Stream : ",stream);
                        stream.getTracks().forEach((track) => {
                            console.log(track)
                            pcs[i].addTrack(track, stream);
                        });
                        return negotiate(pcs[i]);
                    
                    }, (err) => {
                        alert('Could not acquire media: ' + err);
                    });

                } else {
                    negotiate(pcs[i]);
                }
            }
        }
        else
        {
            // display_media_boxes(1);
            console.log("Here");
            let conn_id=0;
            pc = createPeerConnection(conn_id);

            var time_start = null;

            const current_stamp = () => {
                if (time_start === null) {
                    time_start = new Date().getTime();
                    return 0;
                } else {
                    return new Date().getTime() - time_start;
                }
            };

            if (document.getElementById('use-datachannel').checked) {
                var parameters = JSON.parse(document.getElementById('datachannel-parameters').value);

                dc = pc.createDataChannel('chat', parameters);
                dc.addEventListener('close', () => {
                    clearInterval(dcInterval);
                    dataChannelLog[0].textContent += '- close\n';
                });
                dc.addEventListener('open', () => {
                    dataChannelLog[0].textContent += '- open\n';
                    dcInterval = setInterval(() => {
                        var message = 'ping ' + current_stamp();
                        dataChannelLog[0].textContent += '> ' + message + '\n';
                        dc.send(message);
                    }, 1000);
                });
                dc.addEventListener('message', (evt) => {
                    dataChannelLog[0].textContent += '< ' + evt.data + '\n';

                    if (evt.data.substring(0, 4) === 'pong') {
                        var elapsed_ms = current_stamp() - parseInt(evt.data.substring(5), 10);
                        dataChannelLog[0].textContent += ' RTT ' + elapsed_ms + ' ms\n';
                    }
                });
            }

            // Build media constraints.

            const constraints = {
                audio: false,
                video: false
            };

            if (document.getElementById('use-audio').checked) {
                const audioConstraints = {};

                const device = document.getElementById('audio-input').value;
                if (device) {
                    audioConstraints.deviceId = { exact: device };
                }

                constraints.audio = Object.keys(audioConstraints).length ? audioConstraints : true;
            }

            if (document.getElementById('use-video').checked) {
                const videoConstraints = {};

                const device = document.getElementById('video-input').value;
                if (device) {
                    videoConstraints.deviceId = { exact: device };
                }

                const resolution = document.getElementById('video-resolution').value;
                if (resolution) {
                    const dimensions = resolution.split('x');
                    videoConstraints.width = parseInt(dimensions[0], 0);
                    videoConstraints.height = parseInt(dimensions[1], 0);
                }

                constraints.video = Object.keys(videoConstraints).length ? videoConstraints : true;
            }

            // Acquire media and start negociation.
            
            if (constraints.audio || constraints.video) {
                if (constraints.video) {
                    console.log('Media : ',document.getElementById(`media${conn_id}`));
                    document.getElementById(`media${conn_id}`).style.display = 'block';
                }
                navigator.mediaDevices.getUserMedia(constraints).then((stream) => {
                    stream.getTracks().forEach((track) => {
                        pc.addTrack(track, stream);
                    });
                    return negotiate(pc);
                }, (err) => {
                    alert('Could not acquire media: ' + err);
                });
            } else {
                negotiate(pc);
            }
        }
    });
    display_media_boxes();
    // document.getElementById('stop').style.display = 'inline-block';
}

function stop() {
    // document.getElementById('stop').style.display = 'none';
    console.log("stop");
    document.getElementById('start').innerHTML="Start";
    document.getElementById('start').setAttribute("onClick","start()");

    // close data channel
    if (dc) {
        dc.close();
    }

    // close transceivers
    if (pc.getTransceivers) {
        pc.getTransceivers().forEach((transceiver) => {
            if (transceiver.stop) {
                transceiver.stop();
            }
        });
    }
    // close local audio / video
    pc.getSenders().forEach((sender) => {
        sender.track.stop();
    });

    // close peer connection
    setTimeout(() => {
        pc.close();
    }, 500);
    

}

function sdpFilterCodec(kind, codec, realSdp) {
    var allowed = []
    var rtxRegex = new RegExp('a=fmtp:(\\d+) apt=(\\d+)\r$');
    var codecRegex = new RegExp('a=rtpmap:([0-9]+) ' + escapeRegExp(codec))
    var videoRegex = new RegExp('(m=' + kind + ' .*?)( ([0-9]+))*\\s*$')

    var lines = realSdp.split('\n');

    var isKind = false;
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].startsWith('m=' + kind + ' ')) {
            isKind = true;
        } else if (lines[i].startsWith('m=')) {
            isKind = false;
        }

        if (isKind) {
            var match = lines[i].match(codecRegex);
            if (match) {
                allowed.push(parseInt(match[1]));
            }

            match = lines[i].match(rtxRegex);
            if (match && allowed.includes(parseInt(match[2]))) {
                allowed.push(parseInt(match[1]));
            }
        }
    }

    var skipRegex = 'a=(fmtp|rtcp-fb|rtpmap):([0-9]+)';
    var sdp = '';

    isKind = false;
    for (var i = 0; i < lines.length; i++) {
        if (lines[i].startsWith('m=' + kind + ' ')) {
            isKind = true;
        } else if (lines[i].startsWith('m=')) {
            isKind = false;
        }

        if (isKind) {
            var skipMatch = lines[i].match(skipRegex);
            if (skipMatch && !allowed.includes(parseInt(skipMatch[2]))) {
                continue;
            } else if (lines[i].match(videoRegex)) {
                sdp += lines[i].replace(videoRegex, '$1 ' + allowed.join(' ')) + '\n';
            } else {
                sdp += lines[i] + '\n';
            }
        } else {
            sdp += lines[i] + '\n';
        }
    }

    return sdp;
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
}

enumerateInputDevices();