import tornado.web
import tornado.websocket
import tornado.ioloop
from tornado import gen
from tornado.escape import json_decode
import json

import psycopg2 as pq
import psycopg2.extras
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

def websocketManager(event, data):
    print('sending message to clients')
    for c in hub:
        c.write_message(message)

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print('new connection:', self)
        hub.add(self)
        #cur = cnx.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cur = cnx.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        query = "select id,callerid,state,exten,to_char(starttime,'DD/MM/YYYY - HH:MI:SS') as starttime,to_char(endtime,'DD/MM/YYYY - HH:MI:SS') as endtime,to_char(totaltime,'HH:MI:SS') as totaltime,to_char(ringtime,'HH:MI:SS') as ringtime,to_char(answertime,'HH:MI:SS') as answertime,to_char(holdtime,'HH:MI:SS') as holdtime,to_char(day,'DD/MM/YYYY') as day from agent_state where day = now()::date"
        cur.execute(query)
        #rows = cur.fetchall()
        print(json.dumps(cur.fetchall(), indent=2))
        """
        for r in rows:
            print(r['callerid'])
        """
        self.write_message(json.dumps({'event':'updateState','data':'a message from server'}))

    def on_message(self, message):
        raw = json_decode(message)
        event = raw['event']
        data = raw['data']

        print('message received from client', message)
        websocketManager(event, data)

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
        listen('agent_state_changes')
        print('server is running in port 8000')
        ioloop.start()
    except KeyboardInterrupt as e:
        print('stopping server')
        ioloop.stop()

if __name__ == '__main__':
	main()
