var ws = null;
var URL = 'ws://localhost:8000/ws';
//var URL = 'ws://190.117.161.6:8000/ws';
//#-------------------------------------------------- BEGIN [production URL] - (14-07-2018 - 14:03:05) {{
//var URL = 'ws://ryr.progr.am/ws'; //PRODUCTION URL
//#-------------------------------------------------- END   [production URL] - (14-07-2018 - 14:03:05) }}

var agents = [];
var log_color = {"C": "#89FF28", "E": "#FF2828"};

function setLog(message, color){
    div_log = document.getElementById('div_log');
    div_log.innerHTML = message;
    div_log.style.backgroundColor = log_color[color];
}

function onOpen(){
    setLog("> CONNECTED TO SERVER!!!", "C");
}

var state_colors_dict = {"IDLE": "#C7E6F7", "RINGING": "#FCFFC3", "TALKING": "#A7FF81"};

function updateState(data){
    if (agents.indexOf(data['row']['callerid']) < 0) {
        alert("insert new callerid: " + data['row']['callerid']);
        updateCards(data['row']);
    }
    target_exten = document.getElementById(data["row"]["callerid"]+"");
    target_exten.getElementsByClassName('state')[0].innerHTML = data["row"]['state'];
    target_exten.getElementsByClassName('calltype')[0].innerHTML = data["row"]['calltype'];
    target_exten.getElementsByClassName('exten')[0].innerHTML = data["row"]['exten'];
    target_exten.style.backgroundColor = state_colors_dict[data.row.state];
}

function displayMessage(data){
	alert('displayMessage');
}

function updateCards(callerID){
    div_dataContainner = document.getElementById('dataContainner');
    div_dataContainner.innerHTML = div_dataContainner.innerHTML + buildCard(callerID);
}

function buildCard(caller){
        return "<div style='background-color:" + state_colors_dict[caller['state']] + ";' class='div_exten' id='" + caller['callerid'] + "'><span>AGENT: " + caller['callerid'] + " STATUS: <strong class='state'>" + caller['state'] + "</strong> CALLTYPE: <span class='calltype'>" + caller['calltype'] + "</span> PHONE: <span class='exten'>" + caller["exten"] + "</span></span></div>";
}

function populateCards(data){
    card = "<div id='dataContainner'>";
    for (var i = 0; i < data.length; i++) {
        agents.push(data[i]['callerid']);
        //card = card + "<div style='background-color:" + state_colors_dict[data[i]['state']] + ";' class='div_exten' id='" + data[i]['callerid'] + "'><span>AGENT: " + data[i]['callerid'] + " STATUS: <strong class='state'>" + data[i]['state'] + "</strong> CALLTYPE: <span class='calltype'>" + data[i]['calltype'] + "</span> PHONE: <span class='exten'>" + data[i]["exten"] + "</span></span></div>";
        card = card + buildCard(data[i]);
    }
    return card + "</div>";
}

function fillData (data) {
    div_data = document.getElementById('div_data');
    div_data.innerHTML = populateCards(data);
}

handlers = {
	'updateState': updateState,
	'displayMessage': displayMessage,
        'fillData': fillData
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

function onClose(e) {
    console.log("Socket is closed, reconnect will attempted IN 1 second.", e.reason);
    setLog("> CLOSED CONNECTION!!!", "E");
    setTimeout(function(){
        __init__();
    }, 1000);
}

function onError(err) {
    console.error("Error in Socket: ", err.message, "Closing socket");
    setLog("> ERROR IN CONNECTION WITH SERVER!!!", "E");
    ws.close();
}

function __init__(){
	ws = new WebSocket(URL);
	ws.onopen = onOpen;
	ws.onmessage = onMessage;
        ws.onclose = onClose;
        ws.onerror = onError;
}

window.onload = __init__;
