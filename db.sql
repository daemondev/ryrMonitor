drop table if exists calls;
create table calls(
    id serial primary key,
    exten varchar(12),
    callerid int,
    dialstart int,
    dialend int,
    dialedtime int,
    dtime int,
    answeredtime int,
    dialstatus varchar(12),
    hangupcause varchar(15),
    audiofile varchar(100),
    calltype varchar(20),
    ins timestamp default current_timestamp,
    upd timestamp
);

drop table if exists agent_state;
create table agent_state(
    id serial primary key,
    callerid int,
    state varchar(20),
    exten varchar(11),
    calltype varchar(15),
    starttime timestamp default current_timestamp,
    endtime timestamp,
    totaltime time,
    ringtime time,
    answertime time,
    holdtime time,
    day date default current_date
);

CREATE OR REPLACE FUNCTION set_agent_state_trigger() RETURNS trigger AS $$
DECLARE
        channel_name varchar DEFAULT (TG_TABLE_NAME || '_changes');
        row record;
BEGIN
        IF TG_OP = 'INSERT' THEN -- OR TG_OP = 'DELETE'
                row := NEW;
                if(select count(id) from agent_state where callerid=NEW.callerid and day=now()::date)then
                    update agent_state set state='RINGING',exten=NEW.exten, calltype=NEW.calltype where callerid=NEW.callerid and day=now()::date;
                else
                    insert into agent_state(callerid, state, exten, calltype) values(NEW.callerid, 'RINGING', NEW.exten, NEW.calltype);
                end if;
        ELSIF TG_OP = 'UPDATE' THEN
                row := NEW;
                --update agent_state set state='IDLE', exten='', calltype='', answertime=answertime+NEW.answeredtime where callerid=NEW.callerid and day=now()::date;
                update agent_state set state='IDLE', exten='', calltype='' where callerid=NEW.callerid and day=now()::date;
        ELSIF TG_OP = 'DELETE' THEN
            row := OLD;
        END IF;
        return row;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS calls_changes_trigger on calls;
CREATE TRIGGER calls_changes_trigger AFTER INSERT OR UPDATE OR DELETE ON calls FOR EACH ROW EXECUTE PROCEDURE set_agent_state_trigger();


CREATE OR REPLACE FUNCTION notify_trigger() RETURNS trigger AS $$
	DECLARE
		channel_name varchar DEFAULT (TG_TABLE_NAME || '_changes');
		row record;
	BEGIN
		IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN -- OR TG_OP = 'DELETE'
			row := NEW;
                ELSE
			row := OLD;
		END IF;
		PERFORM pg_notify(channel_name, json_build_object('table', TG_TABLE_NAME, 'id', row.id, 'type', TG_OP, 'row', row_to_json(row))::text);
		return row;
	END;
	$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS agent_state_changes_trigger on agent_state;
CREATE TRIGGER agent_state_changes_trigger AFTER INSERT OR UPDATE OR DELETE ON agent_state FOR EACH ROW EXECUTE PROCEDURE notify_trigger();

/*
before Dial
exten => _XXXXXXXXX,n,Agi(pggo,i,${EXTEN},${CALLERID(num)},${EPOCH},${AUDIOFILE},m)
exten => h,1,Agi(pggo,u,${EPOCH},${DIALEDTIME},$[${EPOCH}-${DIALSTART}],${ANSWEREDTIME},${DIALSTATUS},${HANGUPCAUSE},${PGID})
exten => h,n,Hangup(16)
*/
