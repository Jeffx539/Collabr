import struct 


class WriteCollabPacket:
	def __init__(self,cmd,typ):
		self.buffer = b''
		self.command = (cmd)
		self.type = (typ)
		self.writeShort(cmd)
		self.writeShort(typ)
		
	def writeShort(self,data):
		self.buffer += (struct.pack('!h', data))

	def writeLong(self,data):
		self.buffer += (struct.pack('!l', data))	

	def writeString(self,data):
		buff = b''
		buff += (struct.pack('!l',len(data)))
		buff += (bytes(data,'ASCII'))
		self.buffer += buff

	def buildPacket(self):
		finalbuff = b''
		finalbuff += bytearray([0xFF,0xFF,0x00])
		finalbuff += struct.pack('!l',len(self.buffer)+2)
		finalbuff += self.buffer
		finalbuff += bytearray([0x00,0x00])
		return finalbuff
		


class ReadCollabPacket:
	def __init__(self,packet):
		self.packetbuffer = packet
		self.cmd ,self.type = struct.unpack('!hh',packet[0:4])
		self.packetbuffer = self.packetbuffer[4:]

	def debugPrint(self):
		print(self.cmd)
		print(self.type)

	def readString(self):
		strlen, = struct.unpack('!l',self.packetbuffer[0:4])
		self.packetbuffer = self.packetbuffer[4:]
		string = self.packetbuffer[0:strlen]
		self.packetbuffer = self.packetbuffer[strlen:]
		return string.decode('ASCII')
		
	def readShort(self):
		shrt, = struct.unpack('!h',self.packetbuffer[0:2])
		self.packetbuffer = self.packetbuffer[2:]
		return shrt

	def readLong(self):
		lng, = struct.unpack('!l',self.packetbuffer[0:4])
		self.packetbuffer = self.packetbuffer[4:]
		return lng