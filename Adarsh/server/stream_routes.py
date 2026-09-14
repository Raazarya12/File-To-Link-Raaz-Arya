# Taken from megadlbot_oss
# https://github.com/eyaadh/megadlbot_oss/blob/master/mega/webserver/routes.py

import re
import time
import math
import asyncio
import logging
import secrets
import mimetypes

from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine

from Adarsh.bot import multi_clients, work_loads, StreamBot
from Adarsh.server.exceptions import FIleNotFound, InvalidHash
from Adarsh import StartTime, __version__

from ..utils.time_format import get_readable_time
from ..utils.custom_dl import ByteStreamer, offset_fix, chunk_size
from Adarsh.utils.render_template import render_page
from Adarsh.vars import Var


routes = web.RouteTableDef()


# ============================================================
# ROOT
# ============================================================

@routes.get("/", allow_head=True)
async def root_route_handler(_):
    return web.json_response(
        {
            "server_status": "running",
            "uptime": get_readable_time(time.time() - StartTime),
            "telegram_bot": "@" + StreamBot.username,
            "connected_bots": len(multi_clients),
            "loads": dict(
                ("bot" + str(c + 1), l)
                for c, (_, l) in enumerate(
                    sorted(
                        work_loads.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                )
            ),
            "version": __version__,
        }
    )


# ============================================================
# WATCH PAGE
# ============================================================

@routes.get(r"/watch/{path:\S+}", allow_head=True)
async def watch_handler(request: web.Request):
    try:
        path = request.match_info["path"]

        match = re.search(
            r"^([a-zA-Z0-9_-]{6})(\d+)$",
            path
        )

        if match:
            secure_hash = match.group(1)
            file_id = int(match.group(2))

        else:
            id_match = re.search(
                r"(\d+)(?:\/\S+)?",
                path
            )

            if not id_match:
                raise FIleNotFound

            file_id = int(id_match.group(1))
            secure_hash = request.rel_url.query.get("hash")

        if not secure_hash:
            raise InvalidHash

        html = await render_page(
            file_id,
            secure_hash
        )

        return web.Response(
            text=html,
            content_type="text/html"
        )

    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)

    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)

    except (
        AttributeError,
        BadStatusLine,
        ConnectionResetError
    ):
        pass

    except Exception as e:
        logging.exception("Watch route error")
        raise web.HTTPInternalServerError(text=str(e))


# ============================================================
# MEDIA / DOWNLOAD / STREAM
# ============================================================

@routes.get(r"/{path:\S+}", allow_head=True)
async def media_route_handler(request: web.Request):
    try:
        path = request.match_info["path"]

        match = re.search(
            r"^([a-zA-Z0-9_-]{6})(\d+)$",
            path
        )

        if match:
            secure_hash = match.group(1)
            file_id = int(match.group(2))

        else:
            id_match = re.search(
                r"(\d+)(?:\/\S+)?",
                path
            )

            if not id_match:
                raise FIleNotFound

            file_id = int(id_match.group(1))
            secure_hash = request.rel_url.query.get("hash")

        if not secure_hash:
            raise InvalidHash

        return await media_streamer(
            request,
            file_id,
            secure_hash
        )

    except InvalidHash as e:
        raise web.HTTPForbidden(text=e.message)

    except FIleNotFound as e:
        raise web.HTTPNotFound(text=e.message)

    except (
        AttributeError,
        BadStatusLine,
        ConnectionResetError
    ):
        pass

    except Exception as e:
        logging.exception("Media route error")
        raise web.HTTPInternalServerError(text=str(e))


# ============================================================
# CACHE
# ============================================================

class_cache = {}


# ============================================================
# MEDIA STREAMER
# ============================================================

async def media_streamer(
    request: web.Request,
    id: int,
    secure_hash: str
):

    # --------------------------------------------------------
    # Select fastest client
    # --------------------------------------------------------

    index = min(
        work_loads,
        key=work_loads.get
    )

    faster_client = multi_clients[index]

    if Var.MULTI_CLIENT:
        logging.info(
            f"Client {index} is serving {request.remote}"
        )

    # --------------------------------------------------------
    # ByteStreamer cache
    # --------------------------------------------------------

    if faster_client in class_cache:

        tg_connect = class_cache[faster_client]

    else:

        tg_connect = ByteStreamer(
            faster_client
        )

        class_cache[faster_client] = tg_connect

    # --------------------------------------------------------
    # File properties
    # --------------------------------------------------------

    file_data = await tg_connect.get_file_properties(
        id
    )

    # --------------------------------------------------------
    # Validate hash
    # --------------------------------------------------------

    if file_data.unique_id[:6] != secure_hash:
        raise InvalidHash

    file_size = file_data.file_size

    if not file_size:
        raise FIleNotFound

    # --------------------------------------------------------
    # RANGE
    # --------------------------------------------------------

    range_header = request.headers.get("Range")

    if range_header:

        try:

            range_value = range_header.replace(
                "bytes=",
                "",
                1
            )

            start_str, end_str = range_value.split(
                "-",
                1
            )

            # bytes=500-
            if start_str:

                from_bytes = int(start_str)

            # bytes=-500
            else:

                suffix_length = int(end_str)

                if suffix_length <= 0:
                    raise ValueError

                from_bytes = max(
                    file_size - suffix_length,
                    0
                )

            if end_str:

                until_bytes = int(end_str)

            else:

                until_bytes = file_size - 1

        except (
            ValueError,
            TypeError
        ):

            return web.Response(
                status=416,
                headers={
                    "Content-Range":
                        f"bytes */{file_size}"
                }
            )

        if (
            from_bytes < 0
            or from_bytes >= file_size
            or until_bytes < from_bytes
        ):

            return web.Response(
                status=416,
                headers={
                    "Content-Range":
                        f"bytes */{file_size}"
                }
            )

        until_bytes = min(
            until_bytes,
            file_size - 1
        )

        status_code = 206

    else:

        from_bytes = 0
        until_bytes = file_size - 1
        status_code = 200

    # --------------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------------

    req_length = (
        until_bytes
        - from_bytes
        + 1
    )

    # --------------------------------------------------------
    # Chunk calculation
    # --------------------------------------------------------

    new_chunk_size = await chunk_size(
        req_length
    )

    offset = await offset_fix(
        from_bytes,
        new_chunk_size
    )

    first_part_cut = (
        from_bytes
        - offset
    )

    last_part_cut = (
        until_bytes
        % new_chunk_size
    ) + 1

    part_count = math.ceil(
        req_length
        / new_chunk_size
    )

    # --------------------------------------------------------
    # Telegram async generator
    # --------------------------------------------------------

    body = tg_connect.yield_file(
        file_data,
        index,
        offset,
        first_part_cut,
        last_part_cut,
        part_count,
        new_chunk_size
    )

    # --------------------------------------------------------
    # MIME
    # --------------------------------------------------------

    mime_type = file_data.mime_type
    file_name = file_data.file_name

    if not mime_type:

        if file_name:

            mime_type = (
                mimetypes.guess_type(
                    file_name
                )[0]
                or "application/octet-stream"
            )

        else:

            mime_type = "application/octet-stream"

    if not file_name:

        extension = (
            mime_type.split("/", 1)[1]
            if "/" in mime_type
            else "bin"
        )

        file_name = (
            f"{secrets.token_hex(2)}."
            f"{extension}"
        )

    # --------------------------------------------------------
    # WATCH vs DOWNLOAD
    # --------------------------------------------------------

    is_stream = (
        request.rel_url.query.get(
            "stream"
        ) == "1"
    )

    if is_stream:

        disposition = "inline"

    else:

        disposition = "attachment"

    # --------------------------------------------------------
    # HEADERS
    # --------------------------------------------------------

    headers = {
        "Content-Type": mime_type,

        "Content-Disposition":
            f'{disposition}; filename="{file_name}"',

        "Accept-Ranges": "bytes",

        "Content-Length":
            str(req_length),
    }

    if status_code == 206:

        headers["Content-Range"] = (
            f"bytes "
            f"{from_bytes}-"
            f"{until_bytes}/"
            f"{file_size}"
        )

    # --------------------------------------------------------
    # REAL STREAMING RESPONSE
    # --------------------------------------------------------

    response = web.StreamResponse(
        status=status_code,
        headers=headers
    )

    await response.prepare(request)

    try:

        async for chunk in body:

            if chunk:

                await response.write(
                    chunk
                )

    except (
        ConnectionResetError,
        asyncio.CancelledError
    ):

        logging.info(
            "Client disconnected while streaming"
        )

    finally:

        try:
            await response.write_eof()
        except Exception:
            pass

    return response