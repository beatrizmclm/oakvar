from multiprocessing.managers import DictProxy


class WebSocketHandlers:
    def __init__(self, system_worker_state=None, wss=None, logger=None):
        self.routes = []
        self.system_worker_state = system_worker_state
        self.wss = wss
        self.logger = logger
        self.add_routes()

    def add_routes(self):
        self.routes = []
        self.routes.append(["GET", "/ws", self.connect])

    async def connect(self, request):
        import asyncio
        from aiohttp.web import WebSocketResponse
        import concurrent.futures
        from uuid import uuid4
        from .consts import WS_COOKIE_KEY
        from .consts import SYSTEM_STATE_CONNECTION_KEY
        from .consts import SYSTEM_MSG_KEY

        assert self.system_worker_state is not None
        ws_id = request.cookies.get(WS_COOKIE_KEY)
        if ws_id and ws_id in self.wss:
            del self.wss[ws_id]
        ws_id = str(uuid4())
        ws = WebSocketResponse(timeout=60 * 60 * 24 * 365)
        self.wss[ws_id] = ws
        await ws.prepare(request)
        try:
            await ws.send_json(
                {SYSTEM_MSG_KEY: SYSTEM_STATE_CONNECTION_KEY, WS_COOKIE_KEY: ws_id}
            )
        except ConnectionResetError:
            print(f"@@@ ConnectionResetError")
            raise
        except Exception as e:
            print(f"@@@ e={e}")
            raise
        to_dels = []
        for ws_id in self.wss:
            ws_t = self.wss[ws_id]
            print(f"@ ws_t={ws_t}. {ws_t.closed}")
            if ws_t.closed:
                to_dels.append(ws_id)
        print(f"@ to_dels={to_dels}. wss={self.wss}. ws={ws}")
        for ws_id in to_dels:
            del self.wss[ws_id]
        while True:
            try:
                await asyncio.sleep(1)
                if ws.closed:
                    print(f"@ ws closed")
                    break
                await self.process_system_worker_state(ws=ws)
            except concurrent.futures._base.CancelledError:
                print(f"@@@ CancelledError")
                pass
            except ConnectionResetError:
                print(f"@@@ ConnectionResetError")
                break
            except Exception as e:
                print(f"@@@ e={e}")
                if self.logger:
                    self.logger.exception(e)
        print(f"@@@ returning ws: {ws}")
        return ws

    async def process_setup_state(self, ws=None):
        from .consts import SYSTEM_STATE_SETUP_KEY
        from .consts import SYSTEM_STATE_MESSAGE_KEY
        from .consts import SYSTEM_MSG_KEY

        if ws is None or not self.system_worker_state:
            return
        if SYSTEM_STATE_SETUP_KEY not in self.system_worker_state:
            return
        data = self.system_worker_state[SYSTEM_STATE_SETUP_KEY]
        if data.get(SYSTEM_STATE_MESSAGE_KEY):
            msgs = data.get(SYSTEM_STATE_MESSAGE_KEY)
            while msgs:
                msg = msgs[0]
                await ws.send_json({SYSTEM_MSG_KEY: SYSTEM_STATE_SETUP_KEY, "msg": msg})
                msgs.pop(0)

    async def process_install_state(self, ws=None):
        from .consts import SYSTEM_STATE_INSTALL_KEY

        if ws is None or not self.system_worker_state:
            return
        if SYSTEM_STATE_INSTALL_KEY not in self.system_worker_state:
            return
        install_datas = self.system_worker_state[SYSTEM_STATE_INSTALL_KEY]
        for _, data in install_datas.items():
            await ws.send_json(data)
        await self.delete_done_install_states()

    async def delete_done_install_states(self):
        from .consts import SYSTEM_STATE_INSTALL_KEY

        if SYSTEM_STATE_INSTALL_KEY not in self.system_worker_state:
            return
        install_datas: DictProxy = self.system_worker_state[SYSTEM_STATE_INSTALL_KEY]
        to_del = []
        for module_name, data in install_datas.items():
            if data["stage"] in ["finish", "error", "skip", "killed"]:
                to_del.append(module_name)
        for module_name in to_del:
            del install_datas[module_name]

    async def process_system_worker_state(self, ws=None):
        if ws is None:
            return
        await self.process_setup_state(ws=ws)
        await self.process_install_state(ws=ws)
