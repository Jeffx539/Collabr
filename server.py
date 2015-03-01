import Collab.collaborator
import Collab.networking.util as nwUtil
import Collab.networking.packet as Packet
import socket
import threading
import socketserver
import struct
import time
import sublime
import base64
import re

class Server():
	def __init__(self):
		super().__init__()
		self.listening = False
		self.tcpServer = None
		self.peers = []
		self.tcpThread = None
		self.connection = 0
		self.windowHandle = None

	def listen(self,port,whndl):
		if not self.listening:
			self.listenPort = port
			self.tcpServer = ThreadedTCPServer(('0.0.0.0', self.listenPort), ThreadedTCPRequestHandler)
			self.tcpServer.serverInstance = self
			self.tcpThread = threading.Thread(target=self.tcpServer.serve_forever)
			self.tcpThread.daemon = True
			self.tcpThread.start()
			self.listening = True
			self.windowHandle = whndl
			return True
		else:
			return False


	def kill(self):
		if self.listening:
			self.tcpServer.shutdown()
			self.tcpServer.socket.close()
			self.listening = False
			self.tcpThread.join()
			return True
		else:
			return False
	
	# Returns peer from client request handler
	def findPeer(self,clientRequestHandler):
		for peer in self.peers:
			if peer.networkHandle == clientRequestHandler:
				return peer
		
	# Called on each new packet
	def onPacket(self,clientRequestHandler,packetData):
		print(self.peers)
		if packetData.type == 0x10:
			if packetData.cmd == 0x10:
				clientPeer = self.findPeer(clientRequestHandler)
				clientPeer.name = packetData.readString()
				clientPeer.id = self.connection
				print("Collab - Server Hello From " ,clientPeer.name)
				self.sendHello(clientPeer)
			if packetData.cmd == 0x11:
				clientPeer = self.findPeer(clientRequestHandler)
				print("Collab - Client "+ clientPeer.name +" requested a Full Peer Update")
				self.sendAsyncFullPeerUpdate(clientPeer)
				print("Collab - Client "+ clientPeer.name +" requested a Full File Update")
			if packetData.cmd == 0x12:
				clientPeer = self.findPeer(clientRequestHandler)
				print("Collab - Client "+clientPeer.name+" request Full File Update")
				for view in self.windowHandle.views():
					self.sendAsyncFile(view,clientPeer)

	
					


	def sendHello(self,peer):
		pack = Packet.WriteCollabPacket(0x10,0x15)
		pack.writeShort(peer.id)
		pack.writeLong(int(time.time()))
		peer.networkHandle.sendall(pack.buildPacket())


	def sendAsyncFullPeerUpdate(self,reqpeer):
		for peer in self.peers:
			if peer != reqpeer:
				pack = Packet.WriteCollabPacket(0x50,0x20)	
				pack.writeShort(peer.id)
				pack.writeString(peer.name)
				reqpeer.networkHandle.sendall(pack.buildPacket())
				print("Sending -- "+ reqpeer.name + " -- "+peer.name)

	
	def sendAsyncCharUpdate(self,reqpeer,viewId,pos,line):
		pack = Packet.WriteCollabPacket(0x51,0x20)
		pack.writeShort(viewId)
		pack.writeLong(pos.a)
		pack.writeLong(pos.b)
		pack.writeString(line)
		reqpeer.networkHandle.sendall(pack.buildPacket())


	def sendAsyncFile(self,view,reqpeer):
		viewId = view.id()
		bufferfilename = "placeHolder"
		bufferstr = view.substr(sublime.Region(0,view.size()))
		# print(view.file_name())
		# if type(view.file_name()) != None:
		# 	filename = re.search("[\/]([^\/]+)$",view.file_name()).group(0)[1: ]
		# 	print(filename)
		pack = Packet.WriteCollabPacket(0x52,0x20)	
		pack.writeShort(viewId)
		pack.writeString(bufferfilename)
		pack.writeString(view.settings().get('syntax'))
		pack.writeString(bufferstr)
		reqpeer.networkHandle.sendall(pack.buildPacket())
		print("Sending File -- "+ str(viewId) + " -- "+reqpeer.name)


	def testbroadcast(self,viewId,pos,character):
		for peer in self.peers:
			self.sendAsyncCharUpdate(peer,viewId,pos,character)
			
		

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	pass

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
	def handle(self):
		# adds peer and increases connection count
		newCollaborator = Collab.collaborator.Collaborator(self.request)
		self.server.serverInstance.connection += 1
		self.server.serverInstance.peers.append(newCollaborator)
		while 1:
			# recv Header and calculate length of packet
			hdr = nwUtil.recv_full(self.request,7)
			if not hdr: break
			if hdr[0] == 0xFF and hdr[1] == 0xFF:
				length = struct.unpack('!xxxl', hdr)[0]
				data = nwUtil.recv_full(self.request,length)
				if data[length-1] == 0x00 and data[length-2] == 0x00:
					print("valid Packet")
					self.server.serverInstance.onPacket(self.request,Packet.ReadCollabPacket(data))
				else:
					print("Collab - Malformed Packet" + data)
		for peer in self.server.serverInstance.peers:
			if self.request == peer.networkHandle:
				self.server.serverInstance.peers.remove(peer)
				print("Peer Disconnected")