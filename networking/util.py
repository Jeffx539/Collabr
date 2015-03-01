



def recv_full(sock, cnt):
	buf = []
	while cnt>0:
		data = sock.recv(min(10240, cnt))
		if not data: break
		buf.append(data)
		cnt -= len(data)
	return b''.join(buf)
