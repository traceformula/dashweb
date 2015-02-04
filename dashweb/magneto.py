import MySQLdb as mysql
from f import config
import sys

class Magneto:

    _db_host = config.get_db_host()

    def __init__(self, transaction=False, dbname=None):

        self.db_host = Magneto._db_host
        self.db_credential = config.get_db_credential()
        self.set_dbname_credential(dbname)
        self.mysql = mysql
        self.transaction = transaction
        self.con = mysql.connect(self.db_host[0], *self.db_credential, charset="utf8", use_unicode=True)
        self.cur = self.con.cursor(mysql.cursors.DictCursor)

    def set_dbname_credential(self, dbname):
        if dbname is not None:
            self.db_credential = self.db_credential[:2] + (dbname,)

    def __del__(self):
        try:
            self.con.close()
        except:
            pass

    @classmethod
    def create_db(self, database_name=None):
        db_user, db_pass, db_name = config.get_db_credential()
        db_name = db_name if database_name is None else database_name
        db_host = config.get_db_host()[0]
        self.con = mysql.connect(db_host, db_user, db_pass)
        self.cur = self.con.cursor()
        try:
            self.cur.execute("CREATE DATABASE " + db_name)
            print "Database : " + db_name + " is created"
        except mysql.Error, e:
            if "database exists" in e.args[1]:
                print "Database " + db_name + " is already exists"
            else:
                print "Error %d: %s" % (e.args[0], e.args[1])
                print "Create Table Failed"
                sys.exit(1)

    def create_table(self, table_name, created_at=True, updated_at=True):
        if not self._is_table_exists(table_name):
            init_column_sql = self.init_column(table_name, created_at, updated_at)
            self.cur.execute("CREATE TABLE IF NOT EXISTS " + table_name + init_column_sql)
        self.current_table_name = table_name
        self.table_properties = self._table_props()
        return WithMagneto(table_name)

    def drop_table(self, table_name):
        self.cur.execute("drop table %s" % table_name)

    def init_column(self, table_name, created_at, updated_at):
        sql = "(id INT PRIMARY KEY AUTO_INCREMENT"
        if updated_at:
            sql += ", updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        if created_at:
            sql += ", created_at TIMESTAMP DEFAULT 0"
        sql += ")"
        return sql

    def add_index(self, index_name, column_names):
        table_name = self.current_table_name
        error = False
        columns_query = []
        for column_name in column_names:
            if not self._is_column_exists(column_name):
                error = True
                print "Error in index addition, Column " + column_name + " not exists for table " + table_name
                break
            else:
                columns_query.append(column_name)
        if error:
            print "Migration Failed"
            sys.exit(1)
        columns_query = ','.join(columns_query)
        try:
            self.cur.execute("ALTER TABLE " + table_name + " ADD INDEX " + index_name + " (" + columns_query + ")")
            print "Add index " + columns_query + " To Table " + table_name + " with index name " + index_name

        except mysql.Error, e:
            if "Duplicate" in e.args[1]:
                print "%s" % (e.args[1])
            else:
                self.con.rollback()
                print "Error %d: %s" % (e.args[0], e.args[1])
                print "Migration Failed"
                sys.exit(1)


    def add_column(self, column_name, column_type, default=None):
        table_name = self.current_table_name
        try:
            if not self._is_column_exists(column_name):
                if default is None:
                    self.cur.execute("ALTER TABLE " + table_name + " ADD " + column_name + " " + column_type)
                    print "Add Column " + column_name + " To Table " + table_name + " with type " + column_type
                else:
                    self.cur.execute("ALTER TABLE " + table_name + " ADD " + column_name + " " + column_type + " DEFAULT " + str(default))
                    print "Add Column " + column_name + " To Table " + table_name + " with type " + column_type + " and default " + str(default)
            else:
                if self._is_column_props_changed(column_name, column_type, default):
                    if default is not None:
                        self.cur.execute("ALTER TABLE " + table_name + " CHANGE " + column_name + " " + column_name \
                                + " " + column_type + " DEFAULT " + str(default))
                    print "Change Column " + column_name + " To Table " + table_name + " with type " + column_type + " and default " + str(default)

                    current_default = "is NULL" if self.table_properties[column_name]['default'] is None else \
                        ("=" + str(self.table_properties[column_name]['default']) )

                    # change all the row that has old default value into new default value. need to work on this later
                    #if default is not None:
                    #    self.cur.execute("UPDATE " + table_name + " set " + column_name + "=" + str(default) \
                    #            + " where " + column_name + str(current_default))

                    print "Update row in Change Column " + column_name + " To Table " + table_name + " with type " + column_type + " and default " + str(default)

        except mysql.Error, e:
            if "Duplicate" in e.args[1]:
                print "%s" % (e.args[1])
            else:
                self.con.rollback()
                print "Error %d: %s" % (e.args[0], e.args[1])
                print "Migration Failed"
                sys.exit(1)

    def _is_column_exists(self, column_name):
        existance = False
        if column_name in self.table_properties:
            existance = True
        return existance

    def _is_column_props_changed(self, column_name, column_type, default):
        #only handle default value properties for now 
        #TODO : handle type change, and all important keys
        changed = True
        props = self.table_properties[column_name]
        if props['default'] == default or default is None:
            changed = False
        return changed

    def _is_table_exists(self, table_name):
        existance = False
        try:
            self.cur.execute("show tables")
            result = self.cur.fetchall()
            for data in result:
                for key in data:
                    if data[key] == table_name:
                        existance = True
        except:
            print "Query error in table exists checking"
        return existance

    def _table_props(self):
        try:
            self.cur.execute("DESCRIBE " + self.current_table_name)
            result = self.cur.fetchall()
            props = dict()
            for data in result:
                field = dict()
                field['type'] = data['Type']
                field['default'] = str(data['Default']) if type(data['Default']) is not int \
                        else int(data['Default'])
                field['key'] = str(data['Key'])
                field['extra'] = str(data['Extra'])
                props[data['Field']] = field
        except:
            print "Exception in declaring table properties"
            props = dict()
        return props

    def close(self):
        self.con.commit()
        self.cur.close()
        self.con.close()

    @classmethod
    def query(cls, action, dbname=None):
        m = Magneto(dbname=dbname)
        m.cur.execute(action)
        return m

    @classmethod
    def update(cls, id, table_name, dbname=None, **kwargs):
        m = Magneto(dbname=dbname)
        query = ""
        if len(kwargs)>=1:
            first_key = kwargs.keys()[0]
            query = "update %s set %s='%s'" % (table_name, first_key, m.con.escape_string(Magneto.stringify(kwargs[first_key])))
            for i in range(1, len(kwargs)):
                ith_key = kwargs.keys()[i]
                if kwargs[ith_key] == None: continue
                query +=  " , %s='%s'" %(ith_key, m.con.escape_string(Magneto.stringify(kwargs[ith_key])))
            query += " where id=%d" % id
            m.cur.execute(query)
            m.close()

    @classmethod
    def stringify(cls, v, encode_type="utf-8"):
        primitive = (int, str, bool, float, long)
        if type(v) in primitive:
            return str(v)
        elif type(v) is unicode:
            return v.encode("utf-8")
        elif v == None:
            return v
        elif encode_type != "":
            return str(v.encode(encode_type))
        else:
            return v

    #only escape string need to fix later
    @classmethod
    def escape(cls, value):
        return mysql.escape_string(Magneto.stringify(value))

    @classmethod
    def insert(cls, table_name, dbname=None, **kwargs):
        m = Magneto(dbname=dbname)
        query = "insert into %s (" % table_name
        accepted_keys = kwargs.keys()
        query += " %s" % accepted_keys[0]
        query += ", created_at"
        for i in range(1, len(accepted_keys)):
            query += ", %s " % accepted_keys[i]
        query += ") values("
        query += " '%s'" % m.con.escape_string(Magneto.stringify(kwargs[accepted_keys[0]]))
        query += ", CURRENT_TIMESTAMP"
        for i in range(1, len(accepted_keys)):
            query += ", '%s' " % m.con.escape_string(Magneto.stringify(kwargs[accepted_keys[i]]))
        query += ")"
        m.cur.execute(query)
        id = m.cur.lastrowid
        m.close()
        return id

    #for transaction
    def execute(self, action):
        self.cur.execute(action)
        return self

    def fetchall(self):
        result = self.cur.fetchall()
        if not self.transaction:
            self.close
        return result

    def fetchone(self):
        result = self.cur.fetchone()
        if not self.transaction:
            self.close
        return result

    def rollback(self):
        self.con.rollback()
        self.cur.close()
        self.con.close()
        print "Rolling Back"

    def commit(self):
        self.con.commit()

class WithMagneto:

    def __init__(self, table_name):
        self.table_name = table_name

    def __enter__(self):
        print "Migrate Table : " + self.table_name

    def __exit__(self, type, value, traceback):
        print "Finish Migrate Table : " + self.table_name


class Model:

    def save(self):
        keys = self.__dict__.keys()
        table_name = self.__dict__['table_name']
        accepted_keys = []
        for key in keys:
            if self.__dict__[key] is not None and key != "table_name":
                accepted_keys.append(key)
        if len(accepted_keys) == 0:
            return False
        query = "insert into %s (" % table_name
        query += " %s" % accepted_keys[0]
        for i in range(1, len(accepted_keys)):
            query += ", %s " % accepted_keys[i]
        query += ") values("
        query += " '%s'" % str(self.__dict__[accepted_keys[0]])
        for i in range(1, len(accepted_keys)):
            query += ", '%s' " % str(self.__dict__[accepted_keys[i]])
        query += ")"
        m = Magneto.query(query)
        id = m.cur.lastrowid
        m.close()
        return id
