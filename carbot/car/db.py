import json
from typing import Any, Callable, ValuesView
import sqlite3


__all__ = [
    'DBColumn',
    'DBTable',
]


class DBType:
    def __init__(self, sql_name: str,
                 to_db: Callable[[Any], Any] = lambda x: x,
                 to_py: Callable[[Any], Any] = lambda x: x):
        self.sql_name = sql_name
        self.to_db = to_db
        self.to_py = to_py

json_type = DBType('JSON', lambda x: json.dumps(x), lambda x: json.loads(x))

db_types = {
    int: DBType('INTEGER'),
    bool: DBType('INTEGER', lambda x: int(x), lambda x: bool(x)),
    float: DBType('FLOAT'),
    str: DBType('STRING'),
    list: json_type,
    dict: json_type
}


class DBColumn:
    def __init__(self, key: str, default: Any, *, is_primary=False,
                 is_unique=False):
        self.key = key
        self.default = default
        self.data_type = db_types[type(self.default)]
        self.is_primary = is_primary
        self.is_unique = is_unique

    @property
    def sql_def(self) -> str:
        if self.is_primary:
            constraint = "PRIMARY KEY"
        elif self.is_unique:
            constraint = "UNIQUE"
        else:
            constraint = ""
        
        return f"{self.key} {self.data_type.sql_name} {constraint}"


class DBTable:
    def __init__(self, con: sqlite3.Connection, name: str,
                 columns: tuple[DBColumn, ...]):
        assert columns[0].is_primary

        self.columns = {c.key: c for c in columns}
        self.con = con
        self.primary_key = columns[0].key
        columns[0].default = None
        self.name = name

        self.con.execute(f"CREATE TABLE IF NOT EXISTS {self.name}("
                         + ", ".join(c.sql_def for c in self.columns.values())
                         + ")")
        self.con.commit()

    def __contains__(self, key: Any) -> bool:
        return self.con.execute(f"SELECT * FROM {self.name} WHERE "
                                f"{self.primary_key} = ?", (key,)).fetchone() \
            is not None

    def select(self, to_select: str, conditions: str = '', tup: tuple = (), *,
               flatten: bool = True) -> Any:

        query = f"SELECT {to_select} FROM {self.name} {conditions}"

        res = self.con.execute(query, tup).fetchall()

        if to_select == '*':
            spl = self.columns.keys()
        else:
            spl = [col.strip() for col in to_select.split(',')]

        res = [{col: self.columns[col].data_type.to_db(data)
                     for col, data in zip(spl, row)}
               for row in res]

        for row in res:
            row = tuple()

        if not flatten:
            return res
        
        if len(res) == 1:
            res = res[0]
            if len(res) == 1:
                return next(iter(res.values()))

        return res

    def update(self, key: Any, **to_set: Any) -> None:
        # if col not in self.columns:
            # raise KeyError(f"Invalid column name: '{col}'")

        updates = ', '.join(f"{col} = ?" for col in to_set)

        new_vals = tuple(self.columns[col].data_type.to_db(new_val)
                         for col, new_val in to_set.items())

        self.con.execute(f"UPDATE {self.name} SET {updates} WHERE "
                         f"{self.primary_key} = ?", new_vals + (key,))
        self.con.commit()

    def insert(self, **vals) -> sqlite3.Cursor:
        assert self.primary_key in vals

        to_ins = tuple(
            col.data_type.to_db(x) for x, col in
            (
                (vals.get(key) if vals.get(key) is not None
                 else col.default, col)
                for key, col in self.columns.items()
            )
        )

        qs = "?" + ", ?" * (len(self.columns)-1)

        cur = self.con.execute(f"INSERT OR IGNORE INTO {self.name} VALUES ({qs})",
                               to_ins)
        self.con.commit()
        return cur

    def delete(self, conditions: str, tup: tuple = ()) -> None:
        self.con.execute(f"DELETE FROM {self.name} {conditions}", tup)
        self.con.commit()

