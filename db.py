import sqlite3
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Dict


class Database(ABC):
    @abstractmethod
    def connection(self) -> sqlite3.Connection:
        pass


@dataclass
class SqliteDatabase(Database):
    dbname: str

    def connection(self):
        return sqlite3.connect(self.dbname)


@dataclass
class InitedDatabase(Database):
    database: Database
    sql_requests: Iterable[str]

    def connection(self):
        c = self.database.connection()
        for r in self.sql_requests:
            c.execute(r)
        c.commit()
        return c


@dataclass
class CachedConnection(Database):
    database: Database
    __cache: Dict[int, sqlite3.Connection] = field(default_factory=lambda: {})

    def connection(self):
        thread_id = threading.current_thread().ident
        if thread_id not in self.__cache:
            self.__cache[thread_id] = self.database.connection()
        return self.__cache[thread_id]
