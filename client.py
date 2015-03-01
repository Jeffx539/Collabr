import Collab.networking.util as nwUtil
import Collab.networking.packet as Packet
import Collab.collaborator
import socket
import threading
import socketserver
import struct
import time

class Client(object):
	def __init__(self):
		self.connected = False
		self.tcpClient = None
		self.hostip = None
		self.hostport = None
		self.id = 0
		self.peers = []
		self.viewdict = {}
		self.windowHandle = None


	def __tcpconnect(self):
		if self.connected:
			return False

		self.tcpClient.connect((self.hostip,self.hostport))
		self.onConnected()
		while 1:
			# recv Header and calculate length of packet
			hdr = nwUtil.recv_full(self.tcpClient,7)
			if not hdr: break
			print(hdr)
			if hdr[0] == 0xFF and hdr[1] == 0xFF:
				length = struct.unpack('!xxxl', hdr)[0]
				data = nwUtil.recv_full(self.tcpClient,length)
				if data[length-1] == 0x00 and data[length-2] == 0x00:
					self.onPacket(Packet.ReadCollabPacket(data))
				else:
					print("Collab - Malformed Packet" + data)

		self.tcpClient.close()
		self.connected = False

	def connect(self,ip,port,name,windowh):
		self.hostip = ip
		self.hostport = port
		self.name = name
		self.windowHandle =  windowh
		self.tcpClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.cli_thread = threading.Thread(target=self.__tcpconnect)
		self.cli_thread.daemon = True
		self.cli_thread.start()
		return self.tcpClient


	def onConnected(self):
		print("Collab - Connected to Endpoint")
		self.sendHello()


	def onPacket(self,packetData):
		if packetData.type == 0x15:
			if packetData.cmd == 0x10:
				self.id = packetData.readShort()
				print("Collab Server Hello ! - ClientId - ",self.id)
				self.requestFullPeerUpdate()
				self.requestAllFiles()

		if packetData.type == 0x20:
			# Async AddPeer Request
			if packetData.cmd == 0x50:
				newCollaborator = Collab.collaborator.Collaborator(0)
				newCollaborator.id = packetData.readShort()
				newCollaborator.name = packetData.readString()
				print("Collab Client - Async Add Peer ",newCollaborator.name)
				self.peers.append(newCollaborator)
			
			if packetData.cmd == 0x51:
				print("Async Char Inset")
				viewid = packetData.readShort()
				viewcharposa = packetData.readLong()
				viewcharposb = packetData.readLong()
				viewdata = packetData.readString()
				localview = None

				for view in self.windowHandle.views():
					for k,v in self.viewdict.items():
						# print(str(k)+" ----- "+ str(v) + " --- ",str(view.id()))
						if viewid == v and k == view.id():
							print("Remote View Is Localview ",k)
							localview = view



				localview.run_command('replace_data',{'positiona':viewcharposa,'positionb':viewcharposb,'data':viewdata})
			
			if packetData.cmd == 0x52:
				print("Async File Add Response")
				serverSideid = packetData.readShort()
				buffername = packetData.readString()
				buffersyntax = packetData.readString()
				bufferdata = packetData.readString()
				self.windowHandle.run_command('new_file')
				tab = self.windowHandle.active_view()
				self.viewdict[tab.id()] = serverSideid
				tab.set_name(buffername)
				tab.set_syntax_file(buffersyntax)
				tab.run_command('insert_data',{'position':0,'data':bufferdata})

	def sendHello(self):
		print("Collab - Sending Hello")
		helloPacket = Packet.WriteCollabPacket(0x10,0x10)
		helloPacket.writeString(self.name)
		self.tcpClient.send(helloPacket.buildPacket())

	def requestFullPeerUpdate(self):
		self.peers = []
		print("Collab - Request Full Peer Update")
		peerPacket = Packet.WriteCollabPacket(0x11,0x10)
		self.tcpClient.send(peerPacket.buildPacket())

	def requestAllFiles(self):
		peerPacket = Packet.WriteCollabPacket(0x12,0x10)
		self.tcpClient.send(peerPacket.buildPacket())


