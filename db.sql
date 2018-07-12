drop table if exists calltrack;
create table calltrack(
    id serial primary key,
    callerid char(5),
    starttime timestamp default current_timestamp,
    endtime timestamp,
    totaltime time,
    ringtime time,
    answertime time,
    holdtime time
);

--psql -U termux -d termux -a -f db2.sql
--[\i | -i | -c | @db2.sql] db2.sql
/*CREATE OR REPLACE FUNCTION notify_trigger() RETURNS trigger AS $$
	DECLARE
		channel_name varchar DEFAULT (TG_TABLE_NAME || '_changes');
		dato record;
	BEGIN
		IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN -- OR TG_OP = 'DELETE'
			dato := NEW;
                ELSE
			dato := OLD;
		END IF;
		--PERFORM pg_notify(channel_name, '{"id": "' || NEW.id || '"}');
		PERFORM pg_notify(channel_name, json_build_object('table', TG_TABLE_NAME, 'id', dato.id, 'type', TG_OP, 'row', row_to_json(dato))::text);
		return dato;
	END;
	$$ LANGUAGE plpgsql;
*/
DROP TRIGGER IF EXISTS calltrack_changes_trigger on calltrack;
CREATE TRIGGER calltrack_changes_trigger AFTER INSERT OR UPDATE OR DELETE ON calltrack FOR EACH ROW EXECUTE PROCEDURE notify_trigger();
