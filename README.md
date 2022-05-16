
## MediaStreamTrack = what you use to receive frames when someone clicks start on the website, a RTC peer connection is created. 
On that connection there is smth called getReceivers which gives you a list of receivers


# windowoffer & guestOffer
Whenever start button clicked, a request is sent here -> yo I want to make a connection -> establishes a peer connection
Peer Connection = large wrapper for everything
RTCPeerConnections.getReceivers() -> gets you the list of receivers that the peer connection has.
    - store peerConnection in dictionary(guest, peerConnection)
    - we want the tracks (MediaStreamTrack = str and coroutine that you can call to get the frame) which we can access from the receivers


#on_track
# basically transforms the track into a transformed  track -> modify the track how we want it to toss it back to the client (window or guest)

- [ ] fix port issues on the vm
- [ ] second window (back view)
- [ ] fix lag issues








- [ ] finish dashboard view
- [ ] client-server-client method
- [ ] cloud server
- [ ] handle audio

RTCPeerConnection.getReceivers()
loop through the list received
  RTCRtpReceiver.track to access the track from a peer conection

addTrack()


pi
debian
laptop

