'''
An HTTP socket server that only handles GET requests.
Benjamin Kriebel, 2021
'''

import mimetypes
import os
import socket
import sys

PACKET_SIZE = 1024
ROOT_DIR = 'public'


def generate_not_found_response():
	'''
	Generate an HTTP response with a 404 status.
	'''

	not_found_page = b'<html><h1>Not found!</h1></html>'

	response = 'HTTP/1.1 404 Not Found\r\n'.encode()
	response += 'Connection: close\r\n'.encode()
	response += 'Content-Type: text/html\r\n'.encode()
	response += 'Content-Length: {len(not_found_page)}\r\n\r\n'.encode()
	response += not_found_page

	return response


def generate_ok_response(request_data, request_mime_type):
	'''
	Generate an HTTP response with a 200 response status.
	'''

	response = 'HTTP/1.1 OK 200\r\n'.encode()
	response += 'Connection: close\r\n'.encode()
	response += f'Content-Type: {request_mime_type}\r\n'.encode()
	response += f'Content-Length: {len(request_data)}\r\n\r\n'.encode()
	response += request_data

	return response


def get_request_data(request_uri):
	'''
	Get the requested object's data, if it exists.
	'''

	path = ROOT_DIR + request_uri
	request_data = b''
	request_mime_type = ''

	try:
		if os.path.isdir(path):
			# The requested object is a directory. Create a listing of files.
			request_data += f'Contents of {path}\n\n'.encode()
			files = os.listdir(path)
			for file in files:
				request_data += f'{file}\n'.encode()
				request_mime_type = 'text/plain'
		else:
			# The requested object is a file. Extract the data,
			with open(path, 'rb') as f:
				request_data += f.read()
				request_mime_type = mimetypes.guess_type(path)

	except OSError:
		# The object could not be found. The server will send a 404 error.
		print('[!] Error: File does not exist.')
	
	return (request_data, request_mime_type)


def parse_request_line(request):
	'''
	Get the request method and the request URI from the HTTP request.
	'''

	# Verify that the request method is GET.
	request_method = request.split(' ')[0]
	if request_method != 'GET':
		print('[!] Error: This server only handles GET requests.')
		sys.exit(1)
	
	request_uri = request.split(' ')[1]

	return request_uri


def run_server(host, port):
	'''
	Accept incoming connections, handle HTTP requests, and send HTTP responses.
	'''

	# Create a TCP socket and listen for incoming connections.
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((host, port))
	s.settimeout(60)
	s.listen(10)
	print(f'[!] Server is listening on port {port}.')

	while True:
		client = None
		try:
			# Accept a connection and get the HTTP request.
			client, addr = s.accept()
			data = client.recv(PACKET_SIZE)
			request = data.decode()

			# Get the data for the requested object and its MIME type.
			request_uri = parse_request_line(request)		
			(request_data, request_mime_type) = get_request_data(request_uri)
		
			# Build an HTTP response.
			response = b''
			if request_data:
				response = generate_ok_response(request_data, request_mime_type)
			else:
				response = generate_not_found_response()

			# Send the HTTP response.
			client.send(response)
			client.close()

		except KeyboardInterrupt:
			print('[!] Keyboard interrupt!')
			s.close()
			break


if __name__ == '__main__':
	if len(sys.argv) != 3:
		print('USage: http-server.py <HOST> <PORT>')
		sys.exit(1)
	
	host = sys.argv[1]
	port = int(sys.argv[2])

	run_server(host, port)
