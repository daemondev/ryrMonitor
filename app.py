import tornado.web
import tornado.websocket
import tornado.ioloop
from tornado import gen
from tornado.escape import json_decode
import json

import psycopg2 as pq
import psycopg2.extras
import os

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

#class IndexHandler(tornado.web.RequestHandler):
class IndexHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.redirect("/login")
            return
        name = tornado.escape.xhtml_escape(self.current_user)
        self.render('index.html', state='Ready!!!')

class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><div align="center" style="text-align:center;"><form action="/login" method="post">'
                   'User</br><input type="text" name="name"></br>'
                   'Password</br><input type="password" name="password"></br></br>'
                   '<input type="submit" value="Sign in">'
                   '</form></div></body></html>')

    def post(self):
        user = self.get_argument("name")
        password = self.get_argument("password")
        if user == "monitor" and password == "123":
            self.set_secure_cookie("user", user)
            self.redirect("/")
        else:
            self.redirect("/login")

ioloop = tornado.ioloop.IOLoop.instance()
hub = set()
agents = []
cnx = pq.connect('host=ryr.homeplex.org port=55443 dbname=asterisk user=asterisk password=$asterisk$123$')

#-------------------------------------------------- BEGIN [production connect] - (14-07-2018 - 14:03:56) {{
#cnx = pq.connect('host=172.16.16.9 port=5432 dbname=asterisk user=asterisk password=$asterisk$123$')
#-------------------------------------------------- END   [production connect] - (14-07-2018 - 14:03:56) }}

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
        #dispatchEvent('updateState', notify.payload)
        dispatchEvent('updateState',json.loads(notify.payload))

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
        #query = "select id,callerid,state,exten,to_char(starttime,'DD/MM/YYYY - HH:MI:SS') as starttime,to_char(endtime,'DD/MM/YYYY - HH:MI:SS') as endtime,to_char(totaltime,'HH:MI:SS') as totaltime,to_char(ringtime,'HH:MI:SS') as ringtime,to_char(answertime,'HH:MI:SS') as answertime,to_char(holdtime,'HH:MI:SS') as holdtime,to_char(day,'DD/MM/YYYY') as day from agent_state where day = now()::date"
        query = "select id,callerid,state,exten,calltype,(to_char(starttime,'DD/MM/YYYY - HH:MI:SS') is null) as starttime,(to_char(endtime,'DD/MM/YYYY - HH:MI:SS') is null) as endtime,(to_char(totaltime,'HH:MI:SS') is null) as totaltime,(to_char(ringtime,'HH:MI:SS') is null) as ringtime,(to_char(answertime,'HH:MI:SS') is null) as answertime,(to_char(holdtime,'HH:MI:SS') is null) as holdtime,(to_char(day,'DD/MM/YYYY') is null) as day from agent_state where day = now()::date"
        cur.execute(query)
        rows = cur.fetchall()
        #rows = cur.execute(query)
        ds = list(rows)

        #dump = json.dumps(cur.fetchall(), indent=2)
        dump = json.dumps(ds)
        print(type(dump))
        print(dump)
        """
        for r in rows:
            print(r['callerid'])
        """
        #self.write_message(json.dumps({'event': 'fillData', 'data': json.dumps(cur.fetchall())}))
        cur.close()
        self.write_message(json.dumps({'event': 'fillData', 'data': ds}))

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
    (r"/login", LoginHandler),
]

settings = dict(
    static_path = os.path.join(os.getcwd(), 'static'),
    template_path = os.path.join(os.getcwd(), 'templates'),
    debug = True,
    cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
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
