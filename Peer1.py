import socket
from _socket import gethostname
from threading import Thread
from threading import Timer
import sys
import time
import httplib
import os, signal
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from time import sleep

#Constants
HOST_NAME = gethostname()
PEER_IP = "10.0.0.2"

#UDP_SERVER_IP = sys.argv[1]
#UDP_SERVER_PORT = int (sys.argv[2])
#UDP_PEER_PORT = int (sys.argv[3])
#TCP_PEER_PORT = int (sys.argv[4])

UDP_SERVER_IP = "10.0.0.1"
UDP_SERVER_PORT = 7777
UDP_PEER_PORT = 8888
TCP_PEER_PORT = 80

RESEND_TIME = 2

#variables
sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_udp.bind((PEER_IP, UDP_PEER_PORT))
send_buffer = ''
recv_buffer = list()
update_msg = '1' + ' ' + str(PEER_IP) + ' ' + str(TCP_PEER_PORT)
addr = None
t = None
ti = None

class HTTPRequestHandler(BaseHTTPRequestHandler):
	#handle GET command
# 	BaseHTTPRequestHandler.server_version = 
	def do_GET(self):
		#rootdir = 'C:/Users/Lakshmi/Desktop/Sample_codes' #file location
		try:
			if self.path.endswith('.txt'):
				f = open(self.path) #open requested file

				#send code 200 response
				self.send_response(200)

				#send header first
				self.send_header('Content-type','text-txt')
				self.end_headers()

				#send file content to client
				self.wfile.write(f.read())
				f.close()
				return

 		except IOError:
 			self.send_error(404, 'file not found')
		
# 		except Exception as e:
# 			self.send_error(505,e+'version mismatch')
			
#Supports multi-threading
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
		"""Handle requests in a separate thread."""

def run():
		global httpd
		print('http server is starting...')
		server_address = (PEER_IP, TCP_PEER_PORT)
		httpd = HTTPServer(server_address, HTTPRequestHandler)
		print('http server is running...')
		httpd.serve_forever()

def check_kill_process(pstring):
		for line in os.popen("ps ax | grep " + pstring + " | grep -v grep"):
				fields = line.split()
				pid = fields[0]
				os.kill(int(pid), signal.SIGILL)

def calc_RTT():
		global RESEND_TIME
		global update_msg
		estimatedRtt = RESEND_TIME
		devRtt=0
		sampleRtt = 0
		start_time = time.time()
		sock_udp.sendto(update_msg,(UDP_SERVER_IP,UDP_SERVER_PORT))
		sock_udp.recvfrom(4096)
		end_time = time.time()
		sample_Rtt =  end_time - start_time
		devRtt = 0.75*devRtt + 0.25*abs(sample_Rtt - estimatedRtt)
		estimatedRtt = 0.875*estimatedRtt + 0.125*sampleRtt
		RESEND_TIME = estimatedRtt + 4*devRtt

def update_msg_send_function():
		global ti
		send_udp_data(update_msg)
		#print update_msg
		ti = Timer (RESEND_TIME, update_msg_send_function)
		ti.start()

def timer_resend_function():
				print send_buffer
				global t
				sock_udp.sendto(send_buffer,(UDP_SERVER_IP,UDP_SERVER_PORT))
				t = Timer (RESEND_TIME, timer_resend_function)
				t.start()

def send_udp_data(data):
				lst=data.split()
				msg=list()
				msg.append('')
				num_pkts=0
				global send_buffer
				global recv_buffer
				global addr
				global t
				for i in range(len(lst)):
								msg[num_pkts] = msg[num_pkts] + ''.join(lst[i]+' ')
								if sys.getsizeof(msg[num_pkts]) > 64:
												msg[num_pkts] = msg[num_pkts] + ' ' + str(num_pkts+1)
												num_pkts=num_pkts+1
												msg.append('')

				if len(msg[num_pkts]) > 0:
								msg[num_pkts] = msg[num_pkts] + ' ' + str(num_pkts+1)
								num_pkts=num_pkts+1
								msg.append('')

				msg.pop(len(msg)-1)

				for i in range(num_pkts):
								msg[i] = msg[i] + ' ' + str(num_pkts)
								send_buffer = msg[i]
								sock_udp.sendto(msg[i],(UDP_SERVER_IP,UDP_SERVER_PORT))
								t = Timer (RESEND_TIME, timer_resend_function)
								t.start()
								recv_buffer.append('')
								recv_buffer[i],addr = sock_udp.recvfrom(4096)
								t.cancel()

def send_file(peer,addr):
								l= peer.recv(1024)
								print l
								f = open(l,'rb')
								noteol = f.read(8)
								while (noteol):
												print 'Sending...'
												peer.send(noteol)
												print noteol
												noteol = f.read(8)
								f.close()
								print "Done Sending"
								peer.close()

def request_for_file(filename):
				global sock_udp
				#open UDP packet to get peer from server
				message = '2 '+filename
				print "Processing the Request"
				try:
								#send data
								print message
								send_udp_data(message)
				finally:
								print "Retrieved sources of files"
								peer_info, addr = sock_udp.recvfrom(4096)
								peer_info = peer_info.split(",")
								print "Choose a peer from the list to download "+filename
								for i in range(len(peer_info)-1):
										print "Choice ",i
										print peer_info[i]
								req_peer = raw_input("Enter Choice: ")
								req_peer = req_peer.split()
								print "Request File from peer ", req_peer, addr
								print "MESSAGE "+ message
								HTTPResponse(req_peer[0],"GET "+filename)

def HTTPResponse(http_server,msg):
		#Open HTTP connection
		conn = httplib.HTTPConnection(http_server)
		msg = msg.split()
		f = open(msg[1],'wb')

		#Send request to server
		print msg[0]
		print msg[1]
		conn.request(msg[0], msg[1])
		f_content = conn.getresponse()
		#print server response and data
		print(f_content.status, f_content.reason)
		data_received = f_content.read()
		f.write(data_received)
		f.close()
		print "FILE DOWNLOAD COMPLETE!!!"
		#  print(data_received)
		conn.close()

def delete_sharing_file(file_name):
		global update_msg
		lst= update_msg.split()
		for i in range (2, len(lst)-1):
				if lst[i]==file_name:
						lst.pop(i)
		update_msg = lst[0]
		for i in range(len(lst)):
				update_msg = update_msg+' '+lst[i]
		print 'DELETE COMPLETE!!!'

def  add_sharing_file(file_name):
		global update_msg
		update_msg = update_msg + ' ' + file_name

def initial():
		global ti
		calc_RTT()
		ti = Timer (RESEND_TIME, update_msg_send_function)
		ti.start()

		ti = Timer (RESEND_TIME, calc_RTT)
		ti.start()
#     try:
		thread = Thread(target = run, args = ())
		thread.start()
		sleep(1)
		while 1:
				print "Menu\n1.Receive a file \n2.Add sharing file\n3.Delete sharing file\n4.List all files being shared\n5.Exit\n6.View Directory\n"
				a = raw_input("Enter Choice: ")
				if a=='1':
						file_name = raw_input("Enter the file you require:")
						request_for_file(file_name)
				elif a=='2':
						file_name = raw_input("Enter the file you want to share:")
						add_sharing_file(file_name)
				elif a=='3':
						file_name = raw_input("Enter the file you want to Delete:")
						delete_sharing_file(file_name)
				elif a=='4':
						print "Getting the list of files..."
						print update_msg
				elif a=='5':
						send_udp_data('3 ' + PEER_IP + ' ' + str(TCP_PEER_PORT))
						print "Exiting....."
						sock_udp.close()
						httpd.shutdown()
						print "SHUTDOWN!!"
						ti.cancel()
						quit()
						sys.exit()
				elif a=='6':
						sock_udp.sendto('list', (UDP_SERVER_IP, UDP_SERVER_PORT))
						(direc, addr) = sock_udp.recvfrom(4096)
						print direc
						print addr
				else:
						print "Invalid choice...."

#     finally:
#         print "Exiting"
#         sock_udp.close()
#         ti.cancel()
#         sys.exit()

initial()
