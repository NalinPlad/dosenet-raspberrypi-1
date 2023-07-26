from http.server import HTTPServer
import json

import pika
import sys
import time
import argparse
import os


# chdir to www folder
sys.stdout.flush()
web_dir = os.path.join(os.path.dirname(__file__), 'updated_gps/www')
os.chdir(web_dir)

def send_data(data):
	connection = pika.BlockingConnection(
					  pika.ConnectionParameters('localhost'))
	channel = connection.channel()
	channel.queue_declare(queue='toGUI')
	message = {'id': 'GPS', 'data': data}

	channel.basic_publish(exchange='',
						  routing_key='toGUI',
						  body=json.dumps(message))
	connection.close()

def receive(ID, queue):
	'''
	Returns command from queue with given ID
	'''
	connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
	channel = connection.channel()
	channel.queue_declare(queue=queue)
	method_frame, header_frame, body = channel.basic_get(queue=queue)
	if body is not None:
		message = json.loads(body)
		if message['id']==ID:
			channel.basic_ack(delivery_tag=method_frame.delivery_tag)
			connection.close()
			return message['cmd']
		else:
			connection.close()
			return None
	else:
		connection.close()
		return None

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--interval", "-i", type=int, default=1)
	parser.add_argument("--test", "-t", action="store_true", default=False)

	args = parser.parse_args()
	arg_dict = vars(args)

    # Main loop runs forever printing the location, etc. every second.
	last_print = time.monotonic()

	have_fix = False
	interval = arg_dict['interval']
	lat, lon = 0, 0

	# Define ssl context
	import http.server, ssl, socketserver

	context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
	context.load_cert_chain("dosenet.cert", "dosenet.key")


	# Define Websocket Server
	import asyncio, signal
	from websockets.server import serve

	

	import json

	async def resp(websocket, path):
		async for message in websocket:
			print(message)
			if(message == "clientping"):
				await websocket.send(f"serverpong:{interval}")
				global have_fix
				have_fix = True
			elif(message.startswith("loc:")):
				# parse with format loc:lat:lon and parse as number
				global lat, lon
				lat, lon = [float(x) for x in message.split(":")[1:]]

			

	async def main(stop):
		async with serve(resp, "0.0.0.0", 8765, ssl=context):
			print("webscoekt server started")
			await stop

	loop = asyncio.get_event_loop()

	# The stop condition is set when receiving SIGTERM.
	stop = loop.create_future()
	loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

	# Run the server until the stop condition is met.
	# loop.run_until_complete(main(stop))

	# Run Websocket Server (in background)
	import threading
	thread = threading.Thread(target=loop.run_until_complete, args=(main(stop),))
	thread.start()


 	# Define HTTPS Server
	server_address = ("0.0.0.0", 443)
	handler = http.server.SimpleHTTPRequestHandler

	def run_server(server_class=HTTPServer, handler_class=handler):
		httpd = server_class(server_address, handler_class)
		httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
		print("Server running in thread:", threading.current_thread().name)
		httpd.serve_forever()
		print("Server has shutdown.")

	server_thread = threading.Thread(target=run_server)
	server_thread.daemon = True

	server_thread.start()  # Server starts in new thread.

	
	


	while True: # Starts collecting and plotting data
		
		
		if not arg_dict['test']:
			command = receive('GPS', 'fromGUI')

			if command != None:
				print(command)

			if command == 'EXIT':
				print("GPS daq has received command to exit")
				
				# kill the websocket server
				stop.set_result(None)

				# kill the https server
				server_thread._stop()

				print("sys exit")
				
				# close program
				sys.exit(0)

        # Every second print out current location details if there's a fix.
		current = time.monotonic()
		if current - last_print >= arg_dict['interval']:
			last_print = current
			if not have_fix:
				# Try again if we don't have a fix yet.
				print("Waiting for fix...")
				lat, lon = 0, 0

			# We have a fix! (gps.has_fix is true)
			# Print out details about the fix like location, date, etc.
			if not arg_dict['test']:
				print("GPS: ",[lat,lon])
				send_data([lat, lon])

			print("Latitude: {0:.6f} degrees".format(lat))
			print("Longitude: {0:.6f} degrees".format(lon))
			# print("Fix quality: {}".format(gps.fix_quality))
							
		sys.stdout.flush()