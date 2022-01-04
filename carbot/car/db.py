from typing import Any, Union
import sqlite3


# TODO: properly annotate types instead of just using Any
class Column:
    def __init__(self, name: str, default: Any,
                 primary_key: bool = False):
        self.name = name
        self.default = default
        self.primary_key = primary_key

    def sql_var(self) -> str:
        types = {
            int: "INTEGER",
            float: "REAL",
            str: "TEXT"
        }
        pr = "PRIMARY KEY" if self.primary_key else ""
        return f"{self.name} {types[type(self.default)]} {pr}"


class Table:
    def __init__(self, con: sqlite3.Connection, name: str,
                 columns: tuple[Column]):
        assert columns[0].primary_key
        self.con = con
        self.columns = {c.name: c for c in columns}
        self.primary_key = columns[0].name
        self.name = name

        cur = con.cursor()
        cur.execute(f"CREATE TABLE IF NOT EXISTS {self.name} ("
                    + ", ".join(c.sql_var() for c in self.columns.values())
                    + ")")
        cur.close()
        con.commit()

    def __contains__(self, key: Any) -> bool:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM {self.name} WHERE "
                    f"{self.primary_key} = ?", (key,))
        res = cur.fetchone()
        cur.close()
        return res is not None

    def cell(self, key: Any, column_name: str) -> Any:
        if column_name not in self.columns:
            raise KeyError(f"Invalid column name: '{column_name}'")
        cur = con.cursor()
        cur.execute(f"SELECT {column_name} FROM {self.name} WHERE "
                    f"{self.primary_key} = ?", (key,))
        res = cur.fetchone()
        cur.close()
        return res[0]

    def row(self, key: Any) -> tuple[Any]:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM {self.name} WHERE "
                    f"{self.primary_key} = ?", (key,))
        res = cur.fetchone()
        cur.close()
        return {name: val for name, val in zip(self.columns, res)}

    def update(self, key: Any, column_name: str, new_val: Any,
               commit: bool = True) -> None:
        if column_name not in self.columns:
            raise KeyError(f"Invalid column name: '{column_name}'")
        cur = con.cursor()
        cur.execute(f"UPDATE {self.name} SET {column_name} = ? WHERE "
                    f"{self.primary_key} = ?", (new_val, key))
        cur.close()
        if commit:
            con.commit()

    def insert(self, key: Any, vals: tuple = ()) -> None:
        if len(vals) == 0:
            vals = tuple(col.default for col in self.columns.values()
                         if not col.primary_key)
        elif len(vals) != len(self.columns)-1:
            raise ValueError

        cur = con.cursor()
        qs = ", ?" * len(vals)
        cur.execute(f"INSERT OR IGNORE INTO {self.name} VALUES (?{qs})",
                    (key,) + vals)
        cur.close()
        con.commit()


class PersistentStorage:
    def __init__(self, table: Table):
        self.table = table
        self.storage = {}

    def __contains__(self, key: Any) -> bool:
        return key in self.table

    def cell(self, key: Any, column_name: str) -> Any:
        return self.storage[key][column_name]

    def row(self, key: Any) -> tuple[Any]:
        return self.storage[key]

    def update(self, key: Any, column_name: str, new_val: Any,
               commit: bool = True) -> None:
        self.table.update(key, column_name, new_val)
        self.storage[key][column_name] = new_val

    def insert(self, key: Any, vals: tuple = ()) -> None:
        self.table.insert(key, vals)
        self.cache[key] = self.table.row(key)

