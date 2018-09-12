var ws = null;
var URL = 'ws://localhost:8000/ws';
//var URL = 'ws://190.117.161.6:8000/ws';
//#-------------------------------------------------- BEGIN [production URL] - (14-07-2018 - 14:03:05) {{
//var URL = 'ws://ryr.progr.am/ws'; //PRODUCTION URL
//#-------------------------------------------------- END   [production URL] - (14-07-2018 - 14:03:05) }}

var agents = [];
var agents_talking = [];
var agents_ringing = [];
var agents_idle = [];
var log_color = {"C": "#89FF28", "E": "#FF2828"};

function setLog(message, color){
    div_log = document.getElementById('div_log');
    div_log.innerHTML = message;
    div_log.style.backgroundColor = log_color[color];
}

function close_agents_stats(){
    document.getElementById("div_agent_stats").style.display = 'none';
}

function onOpen(){
    setLog("> CONNECTED TO SERVER!!!", "C");
}

var state_colors_dict = {"IDLE": "#C7E6F7", "RINGING": "#FCFFC3", "TALKING": "#A7FF81"};

function updateState(data){
    if (agents.indexOf(data['row']['callerid']) < 0) {
        updateCards(data['row']);
        resumeAgents();
        return;
    }

    target_exten = document.getElementById(data["row"]["callerid"]+"");

    if(data["type"] == "DELETE"){
        target_exten.remove();
        agents.splice(agents.indexOf(data["row"]["callerid"]), 1);
        resumeAgents();
    } else{
        target_exten.getElementsByClassName('state')[0].innerHTML = data["row"]['state'];
        target_exten.getElementsByClassName('calltype')[0].innerHTML = data["row"]['calltype'];
        target_exten.getElementsByClassName('exten')[0].innerHTML = data["row"]['exten'];
        target_exten.style.backgroundColor = state_colors_dict[data.row.state];
    }
}

function displayMessage(data){
	alert('displayMessage');
}

function updateCards(callerID){
    div_dataContainner = document.getElementById('dataContainner');
    div_dataContainner.innerHTML = div_dataContainner.innerHTML + buildCard(callerID);
}

function getAgentStats (callerID) {
    send('getAgentStats', callerID);
}

function buildCard(caller){
        agents.push(caller['callerid']);
        return "<div style='background-color:" + state_colors_dict[caller['state']] + ";' onclick='getAgentStats(" + caller["callerid"] + ");' class='div_exten' id='" + caller['callerid'] + "'><span>AGENT: " + caller['callerid'] + " STATUS: <strong class='state'>" + caller['state'] + "</strong> CALLTYPE: <span class='calltype'>" + caller['calltype'] + "</span> PHONE: <span class='exten'>" + caller["exten"] + "</span></span></div>";
}

function populateCards(data){
    card = "<div id='dataContainner'>";
    for (var i = 0; i < data.length; i++) {
        card = card + buildCard(data[i]);
    }
    resumeAgents();
    return card + "</div>";
}

function fillData (data) {
    div_data = document.getElementById('div_data');
    div_data.innerHTML = populateCards(data);
}

function resumeAgents(){
    document.getElementById("div_total").innerHTML = agents.length;
}

function showAgentStats(data){
    div_agent_stats = document.getElementById("div_agent_stats");
    var table_stats1 = "<div class='center'><table align='center' class='tbl_agent_stats'><tr><th>Q.TOTAL.LLAMADAS</th><th>TIEMPO.TOTAL.LLAMADAS</th><th>TIEMPO.TOTAL.TIMBRADO</th><th>FIN.LLAMADA</th><th>ESTADO</th></tr>";

    data[0].map(function(v, i){
        table_stats1 = table_stats1 + "<tr><td>" + v["Q.CALLS"] + "</td><td>" + v["dialedtime"] + "</td><td>" + v["ringingtime"] + "</td><td>" + v["answeredtime"] + "</td><td>" + v["state"] + "</td></tr>";
    });

    table_stats1 = table_stats1 + "</table></br></hr>";
    var table_stats2 = table_stats1 + "<table align='center' class='tbl_agent_stats'><tr><th>AGENTE</th><th>TEL&Eacute;FONO</th><th>INICIO.LLAMADA</th><th>FIN.LLAMADA</th><th>TIEMPO.HABLADO</th><th>TIEMPO.TIMBRADO</th><th>TIEMPO.TOTAL</th><th>ESTADO</th><th>TIPO.LLAMADA</th></tr>";

    data[1].map(function(v, i){
        table_stats2 = table_stats2 + "<tr><td>" + v["Agente"] + "</td><td>" + v["Teléfono"] + "</td><td>" + v["Inicio.Llamada"] + "</td><td>" + v["Fin.Llamada"] + "</td><td>" + v["Tiempo.Hablado"] + "</td><td>" + v["Tiempo.Timbrado"] + "</td><td>" + v["Tiempo.Total"] + "</td><td>" + v["estado"] + "</td><td>" + v["Tipo.Llamada"] + "</td></tr>";
    });
    table_stats2 = table_stats2 + "</table></div>";
    div_close = "<div onclick='close_agents_stats();' id='div_close_agent_stats'>&#x2715;</div>";
    div_agent_stats.innerHTML = div_close + table_stats2;
    div_agent_stats.style.display = 'block';
}

handlers = {
	'updateState': updateState,
	'displayMessage': displayMessage,
        'fillData': fillData,
        'showAgentStats': showAgentStats
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
