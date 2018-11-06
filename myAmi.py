import socket

EOL = '\r\n'

class MyAmi(object):
    def __init__(self, host='190.117.113.7', port=5038):
        self._socket = None
        self.host = host
        self.port = port

    def connect(self, host=None, port=None):
        host, port = host, port
        if not host:
            host = self.host
        if not port:
            port = self.port

        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _socket.connect((host, port))
        self.socket = _socket.makefile()
        _socket.close()

    def send_action(self, cdict):
        clist = []
        for k, v in cdict.items():
            if isinstance(v, list):
                for item in v:
                    item = tuple([k, v])
                    clist.append("%s: %s" % item)
            else:
                item = tuple([k, v])
                clist.append("%s: %s" % item)
        clist.append(EOL)
        command = EOL.join(clist)
        print(command)
        self.socket.write(command)
        self.socket.flush()

    def originate(self, caller_id, context, number):
        cdict = {"Action":"Originate", "Channel": "SIP/%d" % caller_id, "Context": context, "Exten": number, "Priority": "1", "CallerID": caller_id, "TimeOut": "50000"}
        self.send_action(cdict)

    def chanspy(self, caller_id, context, to_exten):
        cdict = {"Action":"Originate", "Channel": "SIP/%s" % caller_id, "Context": context, "Exten": to_exten, "Priority": "1", "CallerID": caller_id, "TimeOut": "50000"}
        #cdict = {"Action":"Originate", "Application": "ChanSpy" ,"Channel": "SIP/%s" % caller_id, "Context": context, "Data": "SIP/%s" % to_exten, "Priority": "1", "CallerID": caller_id, "TimeOut": "50000"}

        #cdict = {"Action":"Originate", "Application": "ChanSpy" ,"Channel": "SIP/%s" % caller_id, "Data": "SIP/%s" % to_exten, "Priority": "1", "CallerID": caller_id, "Variable": "wq" }
        self.send_action(cdict)

    def login(self, user='richar', password="@admjds.progressive"):
        cdict = {'Action':'Login'}
        cdict['Username'] = user
        cdict['Secret'] = password

        self.send_action(cdict)

    def hangup(self, channel):
        cdict = {'Action':'Hangup'}
        cdict['Channel'] = channel
        response = self.send_action(cdict)

        return response
    def logoff(self):
        cdict = {'Action':'Logoff'}
        response = self.send_action(cdict)

#ami = MyAmi()
#ami.connect()
#ami.login()
##ami.originate(1777, "call-asesor", 982929041)
##ami.originate(1777, "superM", 982929041)
##ami.chanspy(1777, "call-monitor", "015")
#ami.chanspy(1777, "call-monitor", "1777")
#ami.logoff()
