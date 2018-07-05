var ws = null;
var URL = 'ws://190.117.161.6:8000/ws';

function onOpen(){
	
}

function updateState(data){
	alert('from DB: ' +  data);
}

function displayMessage(data){
	alert('displayMessage');
}

handlers = {
	'updateState': updateState, 
	'displayMessage': displayMessage
}

function onMessage(message){
	raw = eval('(' + message.data + ')');
	if (raw.event == 'multi'){
		raw = raw.data;
		for(i=0; raw.length; i++){
			handlers[raw[i].event](raw[i].data);
		}
	}else{
		handlers[raw.event](raw.data);
	}
}

function send(event, data){
	ws.send(JSON.stringify({'event': event, 'data': data}));
}

function __init__(){
	ws = new WebSocket(URL);
	ws.onopen = onOpen;
	ws.onmessage = onMessage;
	alert('ready!!!');
}

window.onload = __init__;
