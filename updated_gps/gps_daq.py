import json

import pika
import sys
import time
import argparse


sys.stdout.flush()

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

	# Define HTTPS Server
	import http.server, ssl, socketserver

	context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
	context.load_cert_chain("dosenet.cert", "dosenet.key")
	server_address = ("0.0.0.0", 443)
	handler = http.server.SimpleHTTPRequestHandler

	# Define Websocket Server
	import asyncio
	from websockets.server import serve

	async def resp(websocket, path):
		async for message in websocket:
			print(message)
			if(message == "clientping"):
				await websocket.send("serverpong")

				# temporary send this json payload
				await websocket.send("start")
			# await websocket.send(message)
			

	async def main():
		async with serve(resp, "0.0.0.0", 8765, ssl=context):
			print("webscoekt server started")
			await asyncio.Future()  # run forever

	# Run Websocket Server (in background)
	import threading
	thread = threading.Thread(target=asyncio.run, args=(main(),))
	thread.start()
	


	while True: # Starts collecting and plotting data
		
		lat, lon = 0, 0
		
		if not arg_dict['test']:
			command = receive('GPS', 'fromGUI')

			if command == 'EXIT':
				print("GPS daq has received command to exit")
				break
		
		# update gps data
		have_fix = False

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
			lat = 0
			lon = 0
			if not arg_dict['test']:
				print("GPS: ",[lat,lon])
				send_data([lat, lon])

			print("Latitude: {0:.6f} degrees".format(lat))
			print("Longitude: {0:.6f} degrees".format(lon))
			# print("Fix quality: {}".format(gps.fix_quality))
							
		sys.stdout.flush()