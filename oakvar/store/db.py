from typing import Optional
from typing import List
from typing import Tuple


def get_ov_store_cache_conn(conf=None):
    from sqlite3 import connect
    from .consts import ov_store_cache_fn
    from os.path import join
    from ..system import get_conf_dir

    conf_dir: Optional[str] = get_conf_dir(conf=conf)
    if conf_dir:
        ov_store_cache_path = join(conf_dir, ov_store_cache_fn)
        conn = connect(ov_store_cache_path)
        cursor = conn.cursor()
        return conn, cursor
    return None, None


def db_func(func):
    def encl_func(*args, conf=None, **kwargs):
        conn, cursor = get_ov_store_cache_conn(conf=conf)
        ret = func(*args, conn=conn, cursor=cursor, **kwargs)
        return ret

    return encl_func


@db_func
def find_name_store(
    module_name: str, conn=None, cursor=None
) -> Optional[Tuple[str, str]]:
    if not conn or not cursor:
        return None
    q = f"select name, store from summary where name=?"
    cursor.execute(q, (module_name,))
    ret = cursor.fetchall()
    name = None
    store = None
    for r in ret:
        if not name or r[1] == "ov":
            name = r[0]
            store = r[1]
    if name and store:
        return name, store
    else:
        return None


@db_func
def module_code_versions(module_name, conn=None, cursor=None) -> Optional[List[str]]:
    if not conn or not cursor:
        return None
    r = find_name_store(module_name)
    if not r:
        return None
    name, store = r
    q = f"select code_version from versions where name=? and store=?"
    cursor.execute(q, (name, store))
    values = [r[0] for r in cursor.fetchall()]
    return values


@db_func
def module_data_versions(module_name, conn=None, cursor=None) -> Optional[List[str]]:
    if not conn or not cursor:
        return None
    r = find_name_store(module_name)
    if not r:
        return None
    name, store = r
    q = f"select data_version from versions where name=? and store=?"
    cursor.execute(q, (name, store))
    values = [r[0] for r in cursor.fetchall()]
    return values


def module_data_sources(module_name, conn=None, cursor=None) -> Optional[List[str]]:
    if not conn or not cursor:
        return None
    r = find_name_store(module_name)
    if not r:
        return None
    name, store = r
    q = f"select data_source from versions where name=? and store=?"
    cursor.execute(q, (name, store))
    values = [r[0] for r in cursor.fetchall()]
    return values


@db_func
def module_sizes(
    module_name: str, code_version: str, conn=None, cursor=None
) -> Optional[Tuple[int, int]]:
    if not conn or not cursor:
        return None
    r = find_name_store(module_name)
    if not r:
        return None
    name, store = r
    q = f"select code_size, data_size from versions where name=? and store=? and code_version=?"
    cursor.execute(q, (name, store, code_version))
    r = cursor.fetchone()
    if not r:
        return None
    code_size, data_size = r
    return int(code_size), int(data_size)


@db_func
def module_data_source(
    module_name: str, code_version: str, conn=None, cursor=None
) -> Optional[str]:
    if not conn or not cursor:
        return None
    r = find_name_store(module_name)
    if not r:
        return None
    name, store = r
    q = f"select data_source from versions where name=? and store=? and code_version=?"
    cursor.execute(q, (name, store, code_version))
    r = cursor.fetchone()
    if not r:
        return None
    return r[0]


@db_func
def remote_module_data_version(
    module_name: str, code_version: str, conn=None, cursor=None
) -> Optional[str]:
    if not conn or not cursor:
        return None
    r = find_name_store(module_name)
    if not r:
        return None
    name, store = r
    q = f"select data_version from versions where name=? and store=? and code_version=?"
    cursor.execute(q, (name, store, code_version))
    r = cursor.fetchone()
    if not r:
        return None
    return r[0]


@db_func
def module_latest_code_version(module_name, conn=None, cursor=None):
    from ..util.util import get_latest_version

    if not conn or not cursor:
        return None
    r = find_name_store(module_name)
    if not r:
        return None
    name, store = r
    q = f"select code_version from versions where name=? and store=?"
    cursor.execute(q, (name, store))
    code_versions = [r[0] for r in cursor.fetchall()]
    latest_code_version = get_latest_version(code_versions)
    return latest_code_version


@db_func
def module_info(module_name, conn=None, cursor=None):
    import sqlite3
    from .consts import summary_table_cols
    from ..module.remote import RemoteModule

    if not conn or not cursor:
        return None
    cursor.row_factory = sqlite3.Row
    q = f"select { ', '.join(summary_table_cols) } from summary where name=?"
    cursor.execute(q, (module_name,))
    ret = cursor.fetchall()
    module_info = None
    for r in ret:
        info = {}
        for col in summary_table_cols:
            info[col] = r[col]
        if not module_info or info["store"] == "ov":
            module_info = RemoteModule("", **info)
    return module_info


@db_func
def summary_col_value(module_name: str, colname: str, conn=None, cursor=None):
    from json import loads

    if not conn or not cursor:
        return None
    q = f"select {colname}, store from summary where name=?"
    cursor.execute(q, (module_name,))
    ret = cursor.fetchall()
    out = None
    if ret:
        for r in ret:
            v, store = r
            if not v or store == "ov":
                out = v
    if out:
        if out[0] in ["[", "{"]:
            return loads(out)
        else:
            return out
    else:
        return None


@db_func
def module_list(conn=None, cursor=None) -> List[str]:
    if not conn or not cursor:
        return []
    q = f"select distinct(name) from summary"
    cursor.execute(q)
    ret = cursor.fetchall()
    l = set()
    for v in ret:
        l.add(v[0])
    return list(l)


@db_func
def table_exists(table: str, conf=None, conn=None, cursor=None) -> bool:
    if not conn or not cursor:
        return False
    if conf:
        pass
    q = f"select name from sqlite_master where type='table' and name=?"
    cursor.execute(q, (table,))
    ret = cursor.fetchone()
    if not ret:
        return False
    else:
        return True


@db_func
def drop_ov_store_cache(conf=None, conn=None, cursor=None, args={}):
    from os.path import exists
    from ..system import get_cache_dir
    from ..system.consts import cache_dirs
    from shutil import rmtree

    if not conn or not cursor:
        return
    if conf:
        pass
    if not args.get("clean"):
        return
    for table in ["summary", "versions", "info"]:
        if table_exists(table):
            q = f"drop table if exists {table}"
            cursor.execute(q)
            conn.commit()
    for cache_key in cache_dirs:
        fp = get_cache_dir(cache_key)
        if exists(fp):
            rmtree(fp)


@db_func
def create_ov_store_cache(conf=None, args={}, conn=None, cursor=None):
    from .consts import summary_table_cols
    from .consts import versions_table_cols
    from ..system.consts import cache_dirs
    from ..system import get_cache_dir
    from os.path import exists
    from os.path import join
    from os import mkdir

    if not conn or not cursor:
        return False
    if conf:
        pass
    clean = args.get("clean")
    if clean or not table_exists("summary"):
        q = f"create table summary ( { ', '.join([col + ' text' for col in summary_table_cols]) }, primary key ( name, store ) )"
        cursor.execute(q)
    if clean or not table_exists("versions"):
        q = f"create table versions ( { ', '.join([col + ' text' for col in versions_table_cols]) }, primary key ( name, store, code_version ) )"
        cursor.execute(q)
    if clean or not table_exists("info"):
        q = f"create table info ( key text primary key, value text )"
        cursor.execute(q)
    conn.commit()
    for cache_key in cache_dirs:
        fp = get_cache_dir(cache_key)
        if not exists(fp):
            mkdir(fp)
            mkdir(join(fp, "ov"))
            mkdir(join(fp, "oc"))


@db_func
def register(conn=None, cursor=None, args={}) -> bool:
    from requests import post
    from .ov.account import get_current_id_token
    from ..util.util import quiet_print
    from .ov import get_register_args_of_module
    from .ov import get_store_url
    from ..module.local import get_logo_b64
    from ..module.local import get_readme
    from ..module.local import get_code_size
    from ..module.local import get_data_size

    if not conn or not cursor:
        return False
    id_token = get_current_id_token()
    module_name = args.get("module_name")
    url = get_store_url() + "/register_module"
    try:
        params = get_register_args_of_module(module_name, args=args)
        if not params:
            return False
        params["idToken"] = id_token
        params["name"] = module_name
        params["readme"] = get_readme(module_name) or ""
        params["logo"] = get_logo_b64(module_name) or ""
        params["code_size"] = get_code_size(module_name)
        params["data_size"] = get_data_size(module_name)
        params["overwrite"] = args.get("overwrite")
        if not params["conf"]:
            quiet_print(f"no configuration file exists for {module_name}", args=args)
            return False
        res = post(url, data=params)
        if res.status_code == 200:
            quiet_print(f"success", args=args)
            return True
        else:
            quiet_print(f"{res.text}", args=args)
            return False
    except Exception as e:
        quiet_print(f"{e}", args=args)
        return False


@db_func
def fetch_ov_store_cache(
    conn=None,
    cursor=None,
    args={},
):
    from .consts import ov_store_last_updated_col
    from ..util.util import quiet_print
    from ..exceptions import StoreServerError
    from ..exceptions import AuthorizationError
    from .ov.account import login_with_token_set
    from .ov import get_server_last_updated
    from time import time

    if not conn or not cursor:
        return False
    if not login_with_token_set():
        quiet_print(f"not logged in", args=args)
        return False
    server_last_updated, status_code = get_server_last_updated()
    local_last_updated = get_local_last_updated()
    clean = args.get("clean")
    if not server_last_updated:
        if status_code == 401:
            raise AuthorizationError()
        elif status_code == 500:
            raise StoreServerError()
        return False
    if not clean and local_last_updated and local_last_updated >= server_last_updated:
        quiet_print("No store update to fetch", args=args)
        return True
    args["timestamp"] = time()
    fetch_summary_cache(args=args)
    fetch_versions_cache(args=args)
    fetch_readme_cache(args=args)
    fetch_logo_cache(args=args)
    fetch_conf_cache(args=args)
    q = f"insert or replace into info ( key, value ) values ( ?, ? )"
    cursor.execute(q, (ov_store_last_updated_col, str(server_last_updated)))
    conn.commit()
    quiet_print("OakVar store cache has been fetched.", args=args)


@db_func
def get_summary_module_store_list(conn=None, cursor=None):
    if not conn or not cursor:
        return
    q = "select name, store from summary"
    cursor.execute(q)
    ret = cursor.fetchall()
    out = []
    for r in ret:
        out.append({"name": r[0], "store": r[1]})
    return out


@db_func
def fetch_conf_cache(args={}, conn=None, cursor=None, conf={}):
    from requests import Session
    from .ov.account import get_current_id_token
    from ..system import get_cache_dir
    from .ov import get_store_url
    from os.path import join

    if not conn or not cursor:
        return
    module_stores = get_summary_module_store_list()
    if not module_stores:
        return
    id_token = get_current_id_token(args=args)
    params = {"idToken": id_token, "timestamp": args.get("timestamp")}
    s = Session()
    s.headers["User-Agent"] = "oakvar"
    for module_store in module_stores:
        name = module_store["name"]
        store = module_store["store"]
        url = f"{get_store_url()}/fetch_conf/{store}/{name}"
        res = s.post(url, data=params)
        if res.status_code == 200:
            fpath = join(get_cache_dir("conf", conf=conf), store, name + ".json")
            with open(fpath, "wb") as wf:
                wf.write(res.content)


@db_func
def fetch_logo_cache(args={}, conn=None, cursor=None, conf={}):
    from requests import Session
    from .ov.account import get_current_id_token
    from ..system import get_cache_dir
    from .ov import get_store_url
    from os.path import join

    if not conn or not cursor:
        return
    module_stores = get_summary_module_store_list()
    if not module_stores:
        return
    id_token = get_current_id_token(args=args)
    params = {"idToken": id_token, "timestamp": args.get("timestamp")}
    s = Session()
    s.headers["User-Agent"] = "oakvar"
    for module_store in module_stores:
        name = module_store["name"]
        store = module_store["store"]
        url = f"{get_store_url()}/fetch_logo/{store}/{name}"
        res = s.post(url, data=params)
        if res.status_code == 200:
            fpath = join(get_cache_dir("logo", conf=conf), store, name + ".png")
            with open(fpath, "wb") as wf:
                wf.write(res.content)


@db_func
def fetch_readme_cache(args={}, conn=None, cursor=None, conf={}):
    from requests import Session
    from .ov.account import get_current_id_token
    from ..system import get_cache_dir
    from .ov import get_store_url
    from os.path import join

    if not conn or not cursor:
        return
    module_stores = get_summary_module_store_list()
    if not module_stores:
        return
    id_token = get_current_id_token(args=args)
    params = {"idToken": id_token, "timestamp": args.get("timestamp")}
    s = Session()
    s.headers["User-Agent"] = "oakvar"
    for module_store in module_stores:
        name = module_store["name"]
        store = module_store["store"]
        url = f"{get_store_url()}/fetch_readme/{store}/{name}"
        res = s.post(url, data=params)
        if res.status_code == 200:
            fpath = join(get_cache_dir("readme", conf=conf), store, name)
            with open(fpath, "wb") as wf:
                wf.write(res.content)


@db_func
def fetch_summary_cache(args={}, conn=None, cursor=None):
    from requests import Session
    from .ov.account import get_current_id_token
    from ..exceptions import StoreServerError
    from ..exceptions import AuthorizationError
    from .ov import get_store_url

    if not conn or not cursor:
        return
    url = f"{get_store_url()}/fetch_summary"
    id_token = get_current_id_token(args=args)
    params = {"idToken": id_token, "timestamp": args.get("timestamp")}
    s = Session()
    s.headers["User-Agent"] = "oakvar"
    res = s.post(url, data=params)
    if res.status_code != 200:
        if res.status_code == 401:
            raise AuthorizationError()
        elif res.status_code == 500:
            raise StoreServerError()
        return False
    q = f"delete from summary"
    cursor.execute(q)
    conn.commit()
    res = res.json()
    cols = res["cols"]
    for row in res["data"]:
        q = f"insert into summary ( {', '.join(cols)} ) values ( {', '.join(['?'] * len(cols))} )"
        cursor.execute(q, row)
    conn.commit()


@db_func
def fetch_versions_cache(args={}, conn=None, cursor=None):
    from requests import Session
    from .ov.account import get_current_id_token
    from ..exceptions import StoreServerError
    from ..exceptions import AuthorizationError
    from .ov import get_store_url

    if not conn or not cursor:
        return
    url = f"{get_store_url()}/fetch_versions"
    id_token = get_current_id_token(args=args)
    params = {"idToken": id_token, "timestamp": args.get("timestamp")}
    s = Session()
    s.headers["User-Agent"] = "oakvar"
    res = s.post(url, data=params)
    if res.status_code != 200:
        if res.status_code == 401:
            raise AuthorizationError()
        elif res.status_code == 500:
            raise StoreServerError()
        return False
    q = f"delete from versions"
    cursor.execute(q)
    conn.commit()
    res = res.json()
    cols = res["cols"]
    for row in res["data"]:
        q = f"insert into versions ( {', '.join(cols)} ) values ( {', '.join(['?'] * len(cols))} )"
        cursor.execute(q, row)
    conn.commit()


@db_func
def get_local_last_updated(conn=None, cursor=None) -> Optional[float]:
    from .consts import ov_store_last_updated_col

    if not conn or not cursor:
        return None
    q = "select value from info where key=?"
    cursor.execute(q, (ov_store_last_updated_col,))
    res = cursor.fetchone()
    if not res:
        return None
    last_updated = float(res[0])
    return last_updated


@db_func
def get_manifest(conn=None, cursor=None) -> Optional[dict]:
    import sqlite3

    if not conn or not cursor:
        return None
    cursor.row_factory = sqlite3.Row
    q = f"select distinct(name) from summary"
    cursor.execute(q)
    res = cursor.fetchall()
    mi = {}
    for r in res:
        name = r[0]
        m = module_info(name)
        if m:
            mi[name] = m.to_dict()
    return mi


@db_func
def get_urls(module_name: str, code_version: str, args={}, conn=None, cursor=None):
    from requests import Session
    from .ov.account import get_current_id_token
    from ..exceptions import StoreServerError
    from ..exceptions import AuthorizationError
    from .ov import get_store_url

    if not conn or not cursor:
        return
    q = f"select store from versions where name=? and code_version=?"
    cursor.execute(q, (module_name, code_version))
    ret = cursor.fetchall()
    store = None
    for r in ret:
        if not store or r[0] == "ov":
            store = r[0]
    if not store:
        return None
    if not conn or not cursor:
        return
    url = f"{get_store_url()}/urls/{module_name}/{code_version}"
    id_token = get_current_id_token(args=args)
    params = {"idToken": id_token}
    s = Session()
    s.headers["User-Agent"] = "oakvar"
    res = s.post(url, data=params)
    if res.status_code == 200:
        return res.json()
    else:
        if res.status_code == 401:
            raise AuthorizationError()
        elif res.status_code == 500:
            raise StoreServerError()
        return
