import tornado.web
import tornado.websocket
import tornado.ioloop
from tornado import gen
import json

import psycopg2 as pq
import os

class IndexHandler(tornado.web.RequestHandler):
	def get(self):
		self.render('index.html', state='Ready!!!')

ioloop = tornado.ioloop.IOLoop.instance()
hub = set()
cnx = pq.connect('host=ryr.homeplex.org port=55443 dbname=asterisk user=asterisk password=$asterisk$123$')
#cnx = pq.connect('host=190.117.161.6 dbname=asterisk user=asterisk password=$asterisk$123$')
cnx.set_isolation_level(pq.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

def listen(channel):
	cur = cnx.cursor()
	print('listen changes in channel: ', channel)
	cur.execute('LISTEN %s;' % channel)

@gen.coroutine
def watch_db(fd, events):
	state = cnx.poll()
	if state == pq.extensions.POLL_OK:
		notify = cnx.notifies.pop()
		print('>>>DB feeds!')
		dispatchEvent('updateState',notify.payload)

def dispatchEvent(event, data):
	for c in hub:
		c.write_message(json.dumps({'event':event, 'data': data}))


def websocketManager(message):
	print('sending message to clients')
	for c in hub:
		c.write_message(message)

class WebSocketHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		print('new connection:', self)
		hub.add(self)
		#self.write_message('hello ws.')
		self.write_message(json.dumps({'event':'updateState','data':'a message from server'}))

	def on_message(self, message):
		print('message received from client', message)
		websocketManager(message)

	def on_close(self):
		print('client disconnecyed:', self)
		hub.remove(self)

class AjaxHandler(tornado.web.RequestHandler):
	def get(self):
		print('Ajax GET request')

	def post(self):
		print('Ajax POST request')
handlers = [
	(r'/', IndexHandler),
	(r'/ws', WebSocketHandler),
	(r'/ajax', AjaxHandler),
]

settings = dict(
	static_path = os.path.join(os.getcwd(), 'static'),
	template_path = os.path.join(os.getcwd(), 'templates'),
	debug = True
)

app = tornado.web.Application(handlers, **settings)
ioloop.add_handler(cnx.fileno(), watch_db, ioloop.READ)

def main():
	try:
		app.listen(8000)
		listen('calls_changes')
		print('server is running in port 8000')
		ioloop.start()
	except KeyboardInterrupt as e:
		print('stopping server')
		ioloop.stop()

if __name__ == '__main__':
	main()
