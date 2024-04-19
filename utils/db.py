import json
from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, Generator, List, NoReturn, Optional, Tuple, Union

from mysql.connector import Error as MySQLError, InterfaceError, OperationalError
from mysql.connector import connect as mysql_connect
from mysql.connector.connection import MySQLConnection, MySQLCursor

_DB = None
_DB_CRED = None


class DisconnectSafeCursor(object):
    def __init__(self, db, cursor):
        self.db = db
        self.cursor: MySQLCursor = cursor

    def close(self):
        self.cursor.close()

    def execute(self, *args, **kwargs):
        try:
            return self.cursor.execute(*args, **kwargs)
        except OperationalError:
            self.db.reconnect()
            self.cursor = self.db.cursor()
            return self.cursor.execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):
        try:
            return self.cursor.executemany(*args, **kwargs)
        except OperationalError:
            self.db.reconnect()
            self.cursor = self.db.cursor()
            return self.cursor.executemany(*args, **kwargs)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def __iter__(self):
        """
        Iteration over the result set which calls self.fetchone()
        and returns the next row.
        """
        return iter(self.fetchone, None)

    def next(self):
        """Used for iterating over the result set."""
        return self.__next__()

    def __next__(self):
        """
        Used for iterating over the result set. Calles self.fetchone()
        to get the next row.
        """
        try:
            row = self.fetchone()
        except InterfaceError:
            raise StopIteration
        if not row:
            raise StopIteration
        return row

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


class DisconnectSafeConnection(object):
    def __init__(self, **kwargs):
        self.connect_kwargs = kwargs
        self.conn = None
        self.reconnect()

    def reconnect(self):
        self.conn = mysql_connect(**self.connect_kwargs)

    def cursor(self, *args, **kwargs):
        cur = self.conn.cursor(*args, **kwargs)
        return DisconnectSafeCursor(self, cur)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def ping(self, **kwargs):
        self.conn.ping(**kwargs)


def get_db(host: str = "", user: str = "", password: str = "", database: str = "", port: int = 0) -> MySQLConnection:
    """
    connects one time and returns the already saved variable if already connected

    :param host: the mysql servers host
    :param user: the username to connect with
    :param password: the password for the given user
    :param database: the name of the database to connect to
    :param port: the port
    :return: the database connection variable
    """
    global _DB, _DB_CRED
    if _DB is None:
        if host != "":
            _DB_CRED = {"host": host, "user": user, "password": password, "database": database, "port": port}
        _DB = DisconnectSafeConnection(**_DB_CRED)
        _DB.ping(reconnect=True, attempts=3, delay=1)

    return _DB


def cursor() -> MySQLCursor:
    """
    :return: creates a new cursor
    """
    global _DB
    try:
        get_db().ping(reconnect=True, attempts=3, delay=1)
    except MySQLError as err:
        _DB = None
        get_db()
    return get_db().cursor()


# noinspection PyShadowingNames
def execute_one(query: str, args: Union[Tuple, List, None] = None, commit: bool = False, **kwargs) -> \
        Union[MySQLCursor, int]:
    """
    executes a sql query. if commit=True is given, all cursors are automatically closed, so there is no need
    to close it manually (which should already have been concluded based on the fact that no cursor is returned).

    :param query: the sql query
    :param args: the actual values of all placeholders
    :param commit: if true commits all transactions after execution
    :param kwargs:
    :return: either the cursor or an integer, based of the `commit` argument
    """
    c = cursor()
    if args:
        c.execute(query, args, **kwargs)
    else:
        c.execute(query, **kwargs)
    if commit:
        get_db().commit()
        c.close()
        return inserted_id()
    return c


# noinspection PyShadowingNames
def execute_many(query: str, args: Union[List[Tuple], Tuple[List, ...], Tuple[Tuple, ...], List[List]],
                 commit: bool = False) -> Optional[MySQLCursor]:
    """
    executes a sql query multiple times

    :param query: the sql query
    :param args: the actual values of all placeholders ("%s")
    :param commit: if true commits all transactions after execution
    :return: the cursor
    """
    c = cursor()
    c.executemany(query, args)
    if commit:
        get_db().commit()
        c.close()
        return None
    return c


# noinspection PyShadowingBuiltins
def fetch(query: str, args: Union[Tuple, List, None] = None, all: bool = False, first: bool = False) -> Union[
    Tuple, Any]:
    """
    executes a sql query and closes the cursor

   :param query: the sql query
   :param args: the actual values of all placeholders
   :param all: if true returns `fetchall()`, otherwise `fetchone()` and assumes all results are read
   :param first: if true maps ...[0] onto everything returned
   :return:
   """
    with execute_one(query, args) as c:
        if all:
            if first:
                return tuple(e[0] for e in c.fetchall())
            else:
                return c.fetchall()
        else:
            if first:
                return c.fetchone()[0]
            else:
                return c.fetchone()


def inserted_id() -> int:
    """
    returns the PRIMARY KEY of the last row that you inserted.

    :return: the id of the last inserted element
    """
    return fetch("SELECT LAST_INSERT_ID()")[0]


def commit() -> NoReturn:
    """
    commits all database transactions.
    """
    get_db().commit()


def get_colors() -> Dict[str, Tuple[int, int, int]]:
    """
    :return: a dict with the classes as keys and their corresponding RGB-values as values
    """
    if "_get_colors_cache" not in globals():
        globals()["_get_colors_cache"] = {k[0]: k[1:] for k in fetch("SELECT * FROM colors", all=True)}
    return globals()["_get_colors_cache"]


def get_types() -> List[str]:
    """
    :return: all available classes
    """
    return list(get_colors().keys())


@dataclass
class Point:
    x: int
    y: int
    width: int
    height: int
    type: str

    def unpack(self):
        return self.x, self.y, self.width, self.height, self.type

    def distance(self, other: 'Point') -> int:
        """
        :param other: the other point
        :return: The manhattan distance between `self` and `other`.
        """
        return abs(other.x - self.x) + abs(other.y - self.y)

    def intersects(self, other: 'Point') -> bool:
        """
        TODO validate if this function works properly (95% confidence)

        :param other: the other point
        :return: True if `self` and `other` intersect.
        """
        # sx1, sx2 = self.x, self.x + self.width
        # sy1, sy2 = self.y, self.y + self.height
        # ox1, ox2 = other.x, other.x + other.width
        # oy1, oy2 = other.y, other.y + other.height

        # return not (self.x > other.x + other.width or self.x + self.width < other.x or self.y > other.y +
        # other.height or self.y + self.height < other.y)

        # x1 = max(min(sx1, sx2), min(ox1, ox2))
        # y1 = max(min(sy1, sy2), min(oy1, oy2))
        # x2 = min(max(sx1, sx2), max(ox1, ox2))
        # y2 = min(max(sy1, sy2), max(oy1, oy2))
        # return x1 < x2 and y1 < y2

        if self.x > other.x + other.width or other.x > self.x + self.width:
            return False

        if self.y > other.y + other.height or other.y > self.y + self.height:
            return False

        return True


def sector_xy_to_real(sector: int, x: int, y: int):
    """
    A shorter version of:
    ```
        if sector == 1:
            return x, y
        elif sector == 2:
            return x + 2000, y
        elif sector == 3:
            return x, y + 1500
        else:
            return x + 2000, y + 1500
    ```

    :param sector:  the sector id (1/2/3/4)
    :param x: the x-coordinate relative to the sectors root
    :param y: the y-coordinate relative to the sectors root
    :return: the x- and y-coordinates relative to the images root
    """
    assert 1 <= sector <= 4, "invalid sector id"
    assert x >= 0, "invalid x-coordinate"
    assert y >= 0, "invalid y-coordinate"

    dx = 2000 if sector % 2 == 0 else 0
    dy = 1500 if sector > 2 else 0
    return x + dx, y + dy


# TODO btw: db.py get points: wenn ein check von 1 section len(..)=0 hat, diese ignorieren, also kein avg
# noinspection PyShadowingBuiltins
def get_points(image_id: int, type: Optional[str] = None, unpacked: bool = False) -> \
        Generator[Union[Point, Tuple[int, int, int, int, str]], None, None]:
    """
    Returns all points associated with `image_id`.

    :param image_id: the image id you want to get all points of
    :param type: if given restricts the returned points to type X
    :param unpacked: if set to true, does not return a Point but x, y, width, height and type as a tuple
    :return: A instance of Point or (see :param unpacked)
    """
    assert image_id >= 0, "invalid image_id"

    type_query = ""
    args = (image_id,)
    if type is not None:
        type_query = "AND points.type=%s"
        args += (type,)

    points = fetch(
        f"SELECT sections.sector, points.x, points.y, points.width, points.height, points.type FROM sections JOIN "
        f"checks ON sections.id=checks.sector JOIN points ON points.check=checks.id WHERE image=%s {type_query} "
        f"ORDER BY sections.sector", args, all=True)
    for point in points:
        x, y = sector_xy_to_real(*point[:3])
        if unpacked:
            yield x, y, point[3], point[4], point[5]
        else:
            yield Point(x, y, point[3], point[4], point[5])


# noinspection PyShadowingBuiltins
def get_all_points(type: Optional[str] = None, checked: bool = True, unpacked: bool = False) -> \
        Generator[Tuple[str, List[Point]], None, None]:
    """
    Returns all (checked) images and their associated points.

    :param type: if given restricts the returned points to type X
    :param checked: if true, only returns images (and their points) when they are checked=1
    :param unpacked: if set to true, does not return a list of Points but x, y, width, height and type as a tuple
    :return: A generator of a tuple of the image name/path and its associated points
    """
    if checked:
        query = "SELECT * FROM images WHERE checked=1"
    else:
        query = """SELECT id, path
                   FROM (SELECT images.id, images.path, sum(sections.checks) as checks
                         FROM images
                         JOIN sections ON sections.image = images.id
                         GROUP BY images.path) as p
                   WHERE p.checks > 0"""

    for image in fetch(query, all=True):
        yield image[1], list(get_points(image[0], type=type, unpacked=unpacked))


def average_points(points, unpacked=False, ignore=None):
    if ignore is None:
        ignore = []

    deep_points = {}
    for x, y, w, h, t in points:
        if t not in deep_points:
            deep_points[t] = []
        deep_points[t].append(Point(x, y, w, h, t))

    all_averages = []

    for t, type_points in deep_points.copy().items():
        if t in ignore:
            if unpacked:
                all_averages += [e.unpack() for e in type_points]
            else:
                all_averages += type_points
            continue

        type_averages = []

        # iterate till there are no pairs (2-points) left
        while len(type_points) > 0:
            p: Point = type_points.pop()

            # p was last point, which means its solo
            if len(type_points) == 0:
                break

            # q = get closest point
            q: Point = min(type_points, key=lambda x: x.distance(p))

            # if the points roots are close enough, they are assumed to be enclosing the same object
            if p.distance(q) < 50:
                # calculate the mean values of the points x, y, width and height
                new_x, new_y = mean([p.x, q.x]), mean([p.y, q.y])
                new_width, new_height = mean([p.width, q.width]), mean([p.height, q.height])
                type_averages.append(Point(new_x, new_y, new_width, new_height, t))

                # remove the closest point as it now "used"
                type_points.remove(q)
            else:
                type_averages.append(p)

        if unpacked:
            type_averages = [e.unpack() for e in type_averages]
        all_averages += type_averages

    return all_averages


def save_all_points(file_path: str, average=False, ignore_average=None) -> NoReturn:
    """
    save all points to a file such that the mysql server has not to be used as a source while developing.

    :param file_path: the file where all necessary image and point data will be stored
    :param average: if the boxes should be averaged aka cleaned up
    :param ignore_average: the types that will be ignored for the averaging process
    :return:
    """
    register = {}
    for image_path, points in get_all_points(checked=False, unpacked=True):
        if average:
            register[image_path] = average_points(points, unpacked=True, ignore=ignore_average)
        else:
            register[image_path] = points
    with open(file_path, "w") as f:
        json.dump(register, f)


def load_all_points(file_path: str, unpacked=False):
    """
    load all points saved for a file. (For the reason why you should do that see `save_all_points`.)

    :param file_path: the file where all necessary image and point data will be loaded from
    :param unpacked: if set to true, does not return a list of Points but x, y, width, height and type as a tuple
    :return: all loaded points
    """

    with open(file_path, "r") as f:
        raw_points = json.load(f)
    for path, points in raw_points.items():
        if unpacked:
            yield path, [point for point in points]
        else:
            yield path, [Point(*point) for point in points]


def main():
    # everyone has access to the read only login data if he has access to this source code anyways so I can
    # let it exists in peace without fear of removal
    # noinspection SpellCheckingInspection
    get_db(host="peregrine.hndrk.xyz", user="ro",
           password="aSTART_PASSWORDbEND_NAMEVIk5IqLR2QK7WhLtRRatGInBJIgeh7CinMOG100ijn999lCWTrY0i9sdBoxy21IP72rNPG0QuV"
                    "m4eO5rj3xdrKhSbg7Gt9coeQK7cEND_PASSWORD",
           database="bwki", port=3301)

    # d = []
    # c = 0
    # for cid, count in fetch(
    #         "SELECT `check`, COUNT(*) as nr_points FROM points GROUP BY `check` ORDER BY nr_points DESC LIMIT 50",
    #         all=True):
    #     sector = fetch("SELECT sector FROM bwki.checks WHERE id=%s", (cid,), first=True)
    #     image = fetch("SELECT image FROM bwki.sections WHERE id=%s", (sector,), first=True)
    #     path, checked = fetch("SELECT path, checked FROM bwki.images WHERE id=%s", (image,))
    #     if checked == 1 and path not in d:
    #         print(f"python cli.py images visualize --ignore-checked {path} img{c}.JPG")
    #         d.append(path)
    #         c += 1

    save_all_points("./test.json", average=True, ignore_average=["background"])
    c = {}
    for path, points in load_all_points("./test.json", unpacked=True):
        for x, y, w, h, t in points:
            if t not in c:
                c[t] = 0
            c[t] += 1
    for k, v in c.items():
        print(k, "->", v)


if __name__ == '__main__':
    main()
