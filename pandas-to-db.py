from sqlalchemy import create_engine
import psycopg2
import io

engine = create_engine('postgresql+psycopg2://username:password@host:port/database')
conn = engine.raw_connection()
cur = conn.cursor()
output = io.StringIO()
df.to_csv(output, sep='\t', header=False, index=False)
output.seek(0)
contents = output.getvalue()
cur.copy_from(output, 'table_name', null="") # null values become ''
conn.commit()

#-------------------------------------------------- BEGIN [2nd] - (16-07-2018 - 23:08:19) {{
#from sqlalchemy import create_engine
#engine = create_engine('postgresql://scott:tiger@localhost:5432/mydatabase')
#df.to_sql('table_name', engine)
#-------------------------------------------------- END   [2nd] - (16-07-2018 - 23:08:19) }}
#-------------------------------------------------- BEGIN [3rd] - (16-07-2018 - 23:08:51) {{
#import sql  # the patched version (file is named sql.py)
#sql.write_frame(df, 'table_name', con, flavor='postgresql')
#-------------------------------------------------- END   [3rd] - (16-07-2018 - 23:08:51) }}
