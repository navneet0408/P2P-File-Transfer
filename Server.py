import socket
from _socket import gethostname
from threading import Thread
from threading import Timer
import time
import sys


#constants
SERVER_IP = "10.0.0.1"
SERVER_PORT = 7777
#SERVER_IP = "127.0.0.1"
#SERVER_PORT = int (sys.argv[1])
HOST_NAME = gethostname()
TIMER_IDLE_PEER = 1
MAX_IDLE_TIME = 10

#variables
peer_list = [[]]
found_peers = [[]]

# Timer Function for removing idle peers
def timer_function():

		for i in range(len(peer_list)-1):
				len_lst = len(peer_list[i+1])
				cur_time = time.time()
				previous_time = float(peer_list[i+1][len_lst-1])
				if (cur_time - previous_time) > MAX_IDLE_TIME:
						peer_list.pop(i+1)
						print peer_list
						break


		t = Timer (TIMER_IDLE_PEER, timer_function)
		t.start()

#Processing the packet
def process_packet(data, s, address):
	lst = data.split()
	if lst[0] == '1':               #Request for UPDATE/CONNECT
		lst.pop(0)
		lst.append(time.time())
		for i in range(len(peer_list)-1):
			if lst[0] == peer_list[i+1][0] and lst[1] == peer_list[i+1][1]:
				peer_list.pop(i+1)
				break
		peer_list.append(lst)
# 		print "Peers Alive List...\n" + peer_list

	#Request for file lookup
	elif lst[0] == '2':
		peer_found=0
		buf = ""
		for i in range(len(peer_list)):
			for j in range(len(peer_list[i]) - 2):
				if lst[1] == peer_list[i][j+2]:
					print peer_list[i]
					buf = "%s %s,%s"%(peer_list[i][0],peer_list[i][1],buf)
					peer_found=1
		print peer_found
		if peer_found==1:
			print "Found Peer..."
			s.sendto(buf,address)
		else:
			print "sending NF"
# 			s.sendto(('NF'),address)
			s.sendto(('\'400\',\'Error\''),address)

	#Delete an entry from the Peer List
	elif lst[0] == '3':
		lst.pop(0)
		for i in range(len(peer_list)-1):
			if lst[0] == peer_list[i+1][0] and lst[1] == peer_list[i+1][1]:
				peer_list.pop(i+1)
				print peer_list
				break
			
	elif lst[0] == '4':
		lst.pop(0)
		snd_str = "4 " + SERVER_IP + str(SERVER_PORT)+' '
		for i in range(len(peer_list)):
			for j in range(len(peer_list[i]) - 2):
				snd_str = peer_list[i][j+2]
				s.sendto(snd_str,address)


def initial():

		#UDP socket works
	print 'Waiting For Peers.... :)'
	sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock_udp.bind((SERVER_IP,SERVER_PORT))
	peer_data = ''
	t = Timer (TIMER_IDLE_PEER, timer_function)
	t.start()
	exp_seq=1
	old_buffer=''
		#Request from Peer
	while True:
		recv_buffer,addr = sock_udp.recvfrom(4096)
		if recv_buffer == 'list':
			sock_udp.sendto(str(peer_list), addr)
		else:
			sock_udp.sendto(recv_buffer,addr)
			if old_buffer != recv_buffer:
				old_buffer = recv_buffer
				recv_buffer_split = recv_buffer.split()
				recv_buffer_len = len(recv_buffer_split)
				num_pkts = recv_buffer_split.pop(recv_buffer_len-1)
				seq_pkt = recv_buffer_split.pop(recv_buffer_len-2)
				exp_seq=exp_seq+1
				peer_data = peer_data + ''.join((str(x)+' ') for x in recv_buffer_split)
				if num_pkts == seq_pkt:
					thread = Thread(target = process_packet, args = (peer_data,sock_udp,addr))
					thread.start() #TEST THREADING!!!!!!!!!!!!!!!!!!!!
					#thread.join()
					peer_data = ''
					exp_seq=1
initial()
