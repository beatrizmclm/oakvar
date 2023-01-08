from typing import Optional
from typing import List
from typing import Tuple
from . import account as account


def module_code_url(module_name: str, version=None) -> Optional[str]:
    from requests import Session
    from .account import get_current_id_token
    from ...exceptions import AuthorizationError
    from ...exceptions import StoreServerError

    id_token = get_current_id_token()
    if not id_token:
        raise AuthorizationError()
    s = Session()
    s.headers["User-Agent"] = "oakvar"
    url = get_store_url() + f"/code_url/{module_name}/{version}"
    params = {"idToken": id_token}
    res = s.post(url, json=params)
    if res.status_code == 200:
        code_url = res.text
        return code_url
    elif res.status_code == 401:
        raise AuthorizationError()
    elif res.status_code == 500:
        raise StoreServerError()
    else:
        return None


def module_data_url(module_name: str, version=None) -> Optional[str]:
    from requests import Session
    from .account import get_current_id_token
    from ...exceptions import AuthorizationError
    from ...exceptions import StoreServerError

    id_token = get_current_id_token()
    if not id_token:
        raise AuthorizationError()
    s = Session()
    s.headers["User-Agent"] = "oakvar"
    url = get_store_url() + f"/data_url/{module_name}/{version}"
    params = {"idToken": id_token}
    res = s.post(url, json=params)
    if res.status_code == 200:
        data_url = res.text
        return data_url
    elif res.status_code == 401:
        raise AuthorizationError()
    elif res.status_code == 500:
        raise StoreServerError()
    else:
        return None


def setup_ov_store_cache(
    refresh_db: bool = False,
    clean_cache_files: bool = False,
    clean: bool = False,
    publish_time: str = "",
    outer=None,
):
    from ..db import fetch_ov_store_cache

    fetch_ov_store_cache(
        refresh_db=refresh_db,
        clean_cache_files=clean_cache_files,
        clean=clean,
        publish_time=publish_time,
        outer=outer,
    )


def url_is_valid(url: str) -> bool:
    from requests import head

    res = head(url)
    status_code = res.status_code
    if status_code >= 200 and status_code < 400:
        return True
    else:
        return False


def get_version_from_url(url: str):
    basename = url.split("/")[-1]
    words = basename.split("__")
    return words[1]


def get_register_args_of_module(
    module_name: str,
    url_file: Optional[str] = None,
    code_url: List[str] = [],
    data_url: List[str] = [],
    overwrite: bool = False,
    outer=None,
    error=None,
) -> Optional[dict]:
    from json import dumps
    from oyaml import safe_load
    from pathlib import Path
    from ...module.local import get_remote_manifest_from_local
    from ...exceptions import ArgumentError
    from ...util.util import is_url
    from ...module.local import get_local_module_info
    from ..ov import module_data_url

    rmi = get_remote_manifest_from_local(module_name, error=error)
    if not rmi:
        return None
    data_version = rmi.get("data_version")
    no_data = rmi.get("no_data")
    if not data_version and not no_data:
        mi = get_local_module_info(module_name)
        if mi and error:
            error.write(
                f"data_version should be given or no_data should be set to true in {mi.conf_path}.\n",
            )
        return None
    if url_file and Path(url_file).exists():
        with open(url_file) as f:
            j = safe_load(f)
            rmi["code_url"] = j.get("code_url", [])
            rmi["data_url"] = j.get("data_url", [])
    else:
        rmi["code_url"] = code_url
        rmi["data_url"] = data_url
    if not rmi["code_url"]:
        if error:
            error.write(
                f"--code-url or -f with a file having code_url should be given.\n"
            )
        return None
    for kind in ["code", "data"]:
        k = f"{kind}_url"
        if len(rmi[k]) > 0:
            for url in rmi[k]:
                if outer:
                    outer.write(f"Validating {url}...")
                try:
                    valid = is_url(url) and url_is_valid(url)
                except:
                    valid = False
                if not valid:
                    raise ArgumentError(msg=f"invalid {kind} URL: {url}")
                if outer:
                    outer.write(f"Validated")
    if not rmi.get("data_url") and no_data and data_version:
        data_url_s = module_data_url(module_name, version=data_version)
        if not data_url_s:
            raise ArgumentError(msg=f"--data-url should be given for new data.")
    rmi["code_url"] = dumps(rmi["code_url"])
    rmi["data_url"] = dumps(rmi["data_url"])
    rmi["overwrite"] = overwrite
    rmi["conf"] = dumps(rmi["conf"])
    rmi["developer"] = dumps(rmi["developer"])
    del rmi["output_columns"]
    del rmi["groups"]
    del rmi["requires"]
    del rmi["tags"]
    return rmi


def make_remote_module_info_from_local(module_name: str) -> Optional[dict]:
    from ...module.local import get_local_module_info
    from ...consts import publish_time_fmt
    from datetime import datetime

    mi = get_local_module_info(module_name)
    if not mi:
        return None
    versions = {}
    latest_version = ""
    ty = mi.type
    title = mi.title
    description = mi.description
    size = mi.size
    code_size = 0
    data_size = 0
    datasource = mi.data_source
    hidden = mi.conf.get("hidden", False)
    developer = mi.developer
    data_versions = {}
    data_sources = {}
    tags = mi.tags
    publish_time = datetime.now().strftime(publish_time_fmt)
    rmi = {
        "versions": versions,
        "latest_version": latest_version,
        "type": ty,
        "title": title,
        "description": description,
        "size": size,
        "code_size": code_size,
        "data_size": data_size,
        "datasource": datasource,
        "hidden": hidden,
        "developer": developer,
        "data_versions": data_versions,
        "data_sources": data_sources,
        "tags": tags,
        "publish_time": publish_time,
    }
    return rmi


def get_server_last_updated() -> Tuple[str, int]:
    from requests import Session
    from .account import get_current_id_token

    id_token = get_current_id_token()
    s = Session()
    s.headers["User-Agent"] = "oakvar"
    url = get_store_url() + "/last_updated"
    params = {"idToken": id_token}
    res = s.post(url, json=params)
    if res.status_code != 200:
        return "", res.status_code
    server_last_updated = res.text
    return server_last_updated, res.status_code


def make_module_info_from_table_row(row: dict) -> dict:
    d = {
        "name": row["name"],
        "type": row["type"],
        "code_version": row["code_version"],
        "data_version": row["data_version"],
        "tags": row["tags"],
        "code_size": row["code_size"],
        "data_size": row["data_size"],
        "logo_url": row["logo_url"],
        "description": row["description"],
        "readme": row["readme"],
        "logo": row["logo"],
        "conf": row["conf"],
        "store": row["store"],
    }
    return d


def get_store_url() -> str:
    from ...system import get_system_conf
    from ...store.consts import store_url_key

    sys_conf = get_system_conf()
    store_url = sys_conf[store_url_key]
    return store_url


def register(
    module_name: str,
    url_file: Optional[str] = None,
    code_url: List[str] = [],
    data_url: List[str] = [],
    overwrite: bool = False,
    outer=None,
    error=None,
) -> bool:
    from requests import post
    from .account import get_current_id_token
    from ...module.local import get_logo_b64
    from ...module.local import get_readme
    from ...module.local import get_code_size
    from ...module.local import get_data_size
    from ...consts import publish_time_fmt
    from datetime import datetime

    id_token = get_current_id_token()
    url = get_store_url() + "/register_module"
    try:
        params = get_register_args_of_module(
            module_name,
            url_file=url_file,
            code_url=code_url,
            data_url=data_url,
            overwrite=overwrite,
            outer=outer,
            error=error,
        )
        if not params:
            return False
        params["idToken"] = id_token
        params["name"] = module_name
        params["readme"] = get_readme(module_name) or ""
        params["logo"] = get_logo_b64(module_name) or ""
        params["code_size"] = get_code_size(module_name)
        params["data_size"] = get_data_size(module_name) or 0
        params["overwrite"] = overwrite
        params["publish_time"] = datetime.now().strftime(publish_time_fmt)
        if not params["conf"]:
            if error:
                error.write(f"No configuration file exists for {module_name}.\n")
            return False
        res = post(url, json=params)
        if res.status_code == 200:
            if outer:
                outer.write(f"Success")
            return True
        else:
            if outer:
                outer.write(
                    f"Error from the store server: {res.status_code} {res.text}\n"
                )
            return False
    except Exception:
        import traceback

        traceback.print_exc()
        return False


def delete(
    module_name: str,
    code_version: Optional[str] = None,
    all: bool = False,
    keep_only_latest: bool = False,
    outer=None,
    error=None,
):
    from requests import post
    from .account import get_current_id_token

    id_token = get_current_id_token()
    if not code_version and not keep_only_latest and not all:
        if outer:
            outer.write(
                "Either --version, --all, or --keep-only-latest should be given.\n"
            )
        return False
    url = get_store_url() + "/delete_module"
    try:
        params = {}
        params["idToken"] = id_token
        params["name"] = module_name
        params["code_version"] = code_version
        params["all"] = all
        params["keep_only_latest"] = keep_only_latest
        res = post(url, json=params)
        if res.status_code == 200:
            if outer:
                outer.write("Success")
            return True
        else:
            if outer:
                outer.write(
                    "Error from the store server: {res.status_code}: {res.text}\n"
                )
            return False
    except:
        import traceback

        if error:
            error.write(traceback.format_exc())
            error.write("\n")
        return False
