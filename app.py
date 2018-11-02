# -*- coding: utf-8 -*-
import tornado.web
import tornado.websocket
import tornado.ioloop
from tornado import gen
from tornado.escape import json_decode
import json

import psycopg2 as pq
import psycopg2.extras
import os
#from datetime import datetime

#-------------------------------------------------- BEGIN [for download excel report] - (17-09-2018 - 03:39:29) {{
import openpyxl
import io
from datetime import datetime
#-------------------------------------------------- END   [for download excel report] - (17-09-2018 - 03:39:29) }}

import shutil

class c:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

debug = True

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

class DownloadHandler(BaseHandler):
    def get(self):
        if debug:
            query2 = """select callerid as "Agente", exten as "Teléfono", to_char(ins, 'HH:MI:SS') as "Inicio.Llamada", coalesce(to_char(upd, 'HH:MI:SS'),'') as "Fin.Llamada", coalesce(answeredtime,0) * '1 second'::interval || '' as "Tiempo.Hablado", coalesce(dtime-answeredtime,0) * '1 second'::interval || '' as "Tiempo.Timbrado", coalesce(dtime,0) * '1 second'::interval || '' as "Tiempo.Total", case dialstatus when 'ANSWER' then 'CONTESTADO' when 'CANCEL' then 'CANCELADO' ELSE COALESCE(dialstatus, 'CONGESTION-2') end  as "estado", calltype as "Tipo.Llamada" from calls where ins::date = now()::date-2 order by ins;"""
        else:
            query2 = """select callerid as "Agente", exten as "Teléfono", to_char(ins, 'HH:MI:SS') as "Inicio.Llamada", coalesce(to_char(upd, 'HH:MI:SS'),'') as "Fin.Llamada", coalesce(answeredtime,0) * '1 second'::interval || '' as "Tiempo.Hablado", coalesce(dtime-answeredtime,0) * '1 second'::interval || '' as "Tiempo.Timbrado", coalesce(dtime,0) * '1 second'::interval || '' as "Tiempo.Total", case dialstatus when 'ANSWER' then 'CONTESTADO' when 'CANCEL' then 'CANCELADO' ELSE COALESCE(dialstatus, 'CONGESTION-2') end  as "estado", calltype as "Tipo.Llamada" from calls where ins::date = now()::date order by ins;"""

        cursor = cnx.cursor()
        cursor.execute(query2)
        stats1 = cursor.fetchall();

        wb = openpyxl.Workbook()
        ws = wb.active

        colnames = tuple(desc[0] for desc in cursor.description)
        ws.append(colnames)

        for r in stats1:
            ws.append(r)

        #ws["A1"] = "Hello OPENPYXL"

        fs = io.BytesIO()
        wb.save(fs)
        self.set_header("ContentType", "application/vnd.ms-excel")
        self.set_header("Content-Disposition", "attachment; filename=" + datetime.strftime(datetime.now(), "amazon-aws-report-%Y%m%d-%H%M") + ".xlsx")
        self.write(fs.getvalue())


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
#-------------------------------------------------- BEGIN [development connect] - (15-09-2018 - 20:42:09) {{
#-------------------------------------------------- END   [development connect] - (15-09-2018 - 20:42:09) }}

if debug:
    cnx = pq.connect('host=ryr.homeplex.org port=55443 dbname=asterisk user=asterisk password=$asterisk$123$')
else:
    cnx = pq.connect('host=172.16.16.9 port=5432 dbname=asterisk user=asterisk password=$asterisk$123$')

#-------------------------------------------------- BEGIN [production connect] - (14-07-2018 - 14:03:56) {{
#-------------------------------------------------- END   [production connect] - (14-07-2018 - 14:03:56) }}

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
        print(c.WARNING + '>>>DB feeds!')
        #dispatchEvent('updateState', notify.payload)
        dispatchEvent('updateState',json.loads(notify.payload))
        print('>>>end DB feeds!' + c.ENDC)

def dispatchEvent(event, data):
    print('dispatching message to WS-clients [%s - %s]' % (event, data))
    for c in hub:
	c.write_message(json.dumps({'event':event, 'data': data}))

@gen.coroutine
def get_record_file(id):
    query = "select audiofile,dialstatus from calls where id = %d" % id
    cur = cnx.cursor()
    cur.execute(query)
    rows = cur.fetchone()
    audio_file = rows[0]
    state = rows[1]
    print(">>>>>>>>>[%s] - AUDIO-FILE: [%s]" % (state, audio_file))
    #if state == 'ANSWER':
    try:
        shutil.copy(audio_file, '/home/ftp/francisco/_audios/')
    	print("######################the audio files is [%s]" % audio_file)
    except Exception as e:
	pass

#class JSONEncoder(json.JSONEncoder):
    #def default(self, o):
        #if isinstance(o, datetime):
            #return o.isoformat()
        #return json.JSONEncoder.default(self, o)

@gen.coroutine
def send_agent_stats(callerID, self):
    if debug:
        query1 = """select count(id) as "Q.CALLS", sum(COALESCE(dtime,0))*'1 second'::interval || '' as "dialedtime",sum(COALESCE(dtime,0) - COALESCE(answeredtime,0))*'1 second'::interval || '' as "ringingtime", sum(COALESCE(answeredtime,0))*'1 second'::interval || '' as "answeredtime", case dialstatus when 'ANSWER' then 'CONTESTADO' when 'CANCEL' then 'CANCELADO' ELSE COALESCE(dialstatus, 'CONGESTION-2') end as "state" from calls where callerid = %d and ins::date = now()::date-2 group by dialstatus order by 1 desc""" % callerID
        query2 = """select callerid as "Agente", exten as "Teléfono", to_char(ins, 'HH:MI:SS') as "Inicio.Llamada", coalesce(to_char(upd, 'HH:MI:SS'),'') as "Fin.Llamada", coalesce(answeredtime,0) * '1 second'::interval || '' as "Tiempo.Hablado", coalesce(dtime-answeredtime,0) * '1 second'::interval || '' as "Tiempo.Timbrado", coalesce(dtime,0) * '1 second'::interval || '' as "Tiempo.Total", case dialstatus when 'ANSWER' then 'CONTESTADO' when 'CANCEL' then 'CANCELADO' ELSE COALESCE(dialstatus, 'CONGESTION-2') end  as "estado", calltype as "Tipo.Llamada" from calls where callerid = %d and ins::date = now()::date-2 order by ins;""" % callerID
    else:
        query1 = """select count(id) as "Q.CALLS", sum(COALESCE(dtime,0))*'1 second'::interval || '' as "dialedtime",sum(COALESCE(dtime,0) - COALESCE(answeredtime,0))*'1 second'::interval || '' as "ringingtime", sum(COALESCE(answeredtime,0))*'1 second'::interval || '' as "answeredtime", case dialstatus when 'ANSWER' then 'CONTESTADO' when 'CANCEL' then 'CANCELADO' ELSE COALESCE(dialstatus, 'CONGESTION-2') end as "state" from calls where callerid = %d and ins::date = now()::date group by dialstatus order by 1 desc""" % callerID
        query2 = """select callerid as "Agente", exten as "Teléfono", to_char(ins, 'HH:MI:SS') as "Inicio.Llamada", coalesce(to_char(upd, 'HH:MI:SS'),'') as "Fin.Llamada", coalesce(answeredtime,0) * '1 second'::interval || '' as "Tiempo.Hablado", coalesce(dtime-answeredtime,0) * '1 second'::interval || '' as "Tiempo.Timbrado", coalesce(dtime,0) * '1 second'::interval || '' as "Tiempo.Total", case dialstatus when 'ANSWER' then 'CONTESTADO' when 'CANCEL' then 'CANCELADO' ELSE COALESCE(dialstatus, 'CONGESTION-2') end  as "estado", calltype as "Tipo.Llamada" from calls where callerid = %d and ins::date = now()::date order by ins;""" % callerID

    cursor = cnx.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cursor.execute(query1)
    stats1 = list(cursor.fetchall());

    cursor.execute(query2)
    stats2 = list(cursor.fetchall());

    self.write_message(json.dumps({'event': 'showAgentStats', 'data': [stats1, stats2]}))

@gen.coroutine
def send_chart_data(callerID, self):
    if debug:
        query = """select count(id) as "qtyCalls", callerid, extract(hour from ins) as "hour" from calls where ins::date = now()::date-2  and callerid = %d group by callerid, extract(hour from ins) order by callerid""" % callerID
        query1 = """select count(id) as "Q.CALLS", sum(COALESCE(dtime,0))*'1 second'::interval || '' as "dialedtime",sum(COALESCE(dtime,0) - COALESCE(answeredtime,0))*'1 second'::interval || '' as "ringingtime", sum(COALESCE(answeredtime,0))*'1 second'::interval || '' as "answeredtime", case dialstatus when 'ANSWER' then 'CONTESTADO' when 'CANCEL' then 'CANCELADO' ELSE COALESCE(dialstatus, 'CONGESTION-2') end as "state" from calls where callerid = %d and ins::date = now()::date-2 group by dialstatus order by 1 desc""" % callerID
        query2 = """select callerid as "Agente", exten as "Teléfono", to_char(ins, 'HH:MI:SS') as "Inicio.Llamada", coalesce(to_char(upd, 'HH:MI:SS'),'') as "Fin.Llamada", coalesce(answeredtime,0) * '1 second'::interval || '' as "Tiempo.Hablado", coalesce(dtime-answeredtime,0) * '1 second'::interval || '' as "Tiempo.Timbrado", coalesce(dtime,0) * '1 second'::interval || '' as "Tiempo.Total", case dialstatus when 'ANSWER' then 'CONTESTADO' when 'CANCEL' then 'CANCELADO' ELSE COALESCE(dialstatus, 'CONGESTION-2') end  as "estado", calltype as "Tipo.Llamada" from calls where callerid = %d and ins::date = now()::date-2 order by ins;""" % callerID
    else:
        query = """select count(id) as "qtyCalls", callerid, extract(hour from ins) as "hour" from calls where ins::date = now()::date  and callerid = %d group by callerid, extract(hour from ins) order by callerid""" % callerID
        query1 = """select count(id) as "Q.CALLS", sum(COALESCE(dtime,0))*'1 second'::interval || '' as "dialedtime",sum(COALESCE(dtime,0) - COALESCE(answeredtime,0))*'1 second'::interval || '' as "ringingtime", sum(COALESCE(answeredtime,0))*'1 second'::interval || '' as "answeredtime", case dialstatus when 'ANSWER' then 'CONTESTADO' when 'CANCEL' then 'CANCELADO' ELSE COALESCE(dialstatus, 'CONGESTION-2') end as "state" from calls where callerid = %d and ins::date = now()::date group by dialstatus order by 1 desc""" % callerID
        query2 = """select callerid as "Agente", exten as "Teléfono", to_char(ins, 'HH:MI:SS') as "Inicio.Llamada", coalesce(to_char(upd, 'HH:MI:SS'),'') as "Fin.Llamada", coalesce(answeredtime,0) * '1 second'::interval || '' as "Tiempo.Hablado", coalesce(dtime-answeredtime,0) * '1 second'::interval || '' as "Tiempo.Timbrado", coalesce(dtime,0) * '1 second'::interval || '' as "Tiempo.Total", case dialstatus when 'ANSWER' then 'CONTESTADO' when 'CANCEL' then 'CANCELADO' ELSE COALESCE(dialstatus, 'CONGESTION-2') end  as "estado", calltype as "Tipo.Llamada" from calls where callerid = %d and ins::date = now()::date order by ins;""" % callerID

    cursor = cnx.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    cursor.execute(query1)
    stats1 = list(cursor.fetchall());

    cursor.execute(query2)
    stats2 = list(cursor.fetchall());

    cursor.execute(query)
    chartData = list(cursor.fetchall());

    print(c.HEADER + "\nbegin charting:\n")
    print(chartData)
    print("\nend charting:\n" + c.ENDC)

    self.write_message(json.dumps({'event': 'paintChart', 'data': [stats1, stats2, chartData]}))

def websocketManager(event, data, self=None):
    if event == '__get_recorded_file__':
	print("prepare work for retrieve record file [%s]" % data)
	#get_record_file(int(data))
    elif event == 'identify_android_device':
        print(">>>> connected android device with: %s" % data)
    elif event == 'getAgentStats':
        print(">>> sending stats for agent [%d]" % data)
        send_agent_stats(data, self)
    elif event == 'getChartData':
        send_chart_data(data, self)
    else:
	return
	print("normal event")
	for c in hub:
            c.write_message("")

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    #def initialize(self):
    #    self._closed = False

    def open(self):
        print(c.OKGREEN + "\n\n\n>>>>>>>>>new connection: from: [%s] with agent [%s] %s" % (self.request.remote_ip  ,self.request.headers.get('User-Agent',False), c.ENDC))
        agent = self.request.headers.get('User-Agent',False)
	if agent:
	    if agent == 'C-AsteriskClient':
		return

        hub.add(self)
        #cur = cnx.cursor(cursor_factory = psycopg2.extras.DictCursor)
        cur = cnx.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
        #query = "select id,callerid,state,exten,to_char(starttime,'DD/MM/YYYY - HH:MI:SS') as starttime,to_char(endtime,'DD/MM/YYYY - HH:MI:SS') as endtime,to_char(totaltime,'HH:MI:SS') as totaltime,to_char(ringtime,'HH:MI:SS') as ringtime,to_char(answertime,'HH:MI:SS') as answertime,to_char(holdtime,'HH:MI:SS') as holdtime,to_char(day,'DD/MM/YYYY') as day from agent_state where day = now()::date"
        if debug:
            query = "select id,callerid,state,exten,calltype,(to_char(starttime,'DD/MM/YYYY - HH:MI:SS') is null) as starttime,(to_char(endtime,'DD/MM/YYYY - HH:MI:SS') is null) as endtime,(to_char(totaltime,'HH:MI:SS') is null) as totaltime,(to_char(ringtime,'HH:MI:SS') is null) as ringtime,(to_char(answertime,'HH:MI:SS') is null) as answertime,(to_char(holdtime,'HH:MI:SS') is null) as holdtime,(to_char(day,'DD/MM/YYYY') is null) as day from agent_state where day = now()::date-2"
        else:
            query = "select id,callerid,state,exten,calltype,(to_char(starttime,'DD/MM/YYYY - HH:MI:SS') is null) as starttime,(to_char(endtime,'DD/MM/YYYY - HH:MI:SS') is null) as endtime,(to_char(totaltime,'HH:MI:SS') is null) as totaltime,(to_char(ringtime,'HH:MI:SS') is null) as ringtime,(to_char(answertime,'HH:MI:SS') is null) as answertime,(to_char(holdtime,'HH:MI:SS') is null) as holdtime,(to_char(day,'DD/MM/YYYY') is null) as day from agent_state where day = now()::date"
        cur.execute(query)
        rows = cur.fetchall()
        #rows = cur.execute(query)
        ds = list(rows)

        #dump = json.dumps(cur.fetchall(), indent=2)
        dump = json.dumps(ds)
        #print(type(dump))
        #print(dump)
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

        print(c.OKBLUE + 'message received from client [%s] %s' %(message, c.ENDC))
        websocketManager(event, data, self)

    def on_close(self):
        print(c.FAIL + "client disconnected:")
        print(self)
        print (c.ENDC)
	if self in hub:
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
    (r"/download", DownloadHandler),
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
