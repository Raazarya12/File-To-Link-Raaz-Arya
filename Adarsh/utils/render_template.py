from Adarsh.vars import Var
from Adarsh.bot import StreamBot
from Adarsh.utils.human_readable import humanbytes
from Adarsh.utils.file_properties import get_file_ids
from Adarsh.server.exceptions import InvalidHash

import urllib.parse
import aiofiles
import logging
import aiohttp


async def render_page(id, secure_hash):
    file_data = await get_file_ids(
        StreamBot,
        int(Var.BIN_CHANNEL),
        int(id)
    )

    if file_data.unique_id[:6] != secure_hash:
        logging.debug(
            f'link hash: {secure_hash} - {file_data.unique_id[:6]}'
        )
        logging.debug(
            f"Invalid hash for message with - ID {id}"
        )
        raise InvalidHash

    # WATCH / STREAM URL
    src = urllib.parse.urljoin(
        Var.URL,
        f'{secure_hash}{str(id)}?hash={secure_hash}&stream=1'
    )

    # VIDEO
    if str(file_data.mime_type.split('/')[0].strip()) == 'video':

        async with aiofiles.open(
            'Adarsh/template/req.html'
        ) as r:

            heading = 'Watch {}'.format(
                file_data.file_name
            )

            tag = file_data.mime_type.split('/')[0].strip()

            html = (
                await r.read()
            ).replace(
                'tag',
                tag
            ) % (
                heading,
                file_data.file_name,
                src
            )

    # AUDIO
    elif str(file_data.mime_type.split('/')[0].strip()) == 'audio':

        async with aiofiles.open(
            'Adarsh/template/req.html'
        ) as r:

            heading = 'Listen {}'.format(
                file_data.file_name
            )

            tag = file_data.mime_type.split('/')[0].strip()

            html = (
                await r.read()
            ).replace(
                'tag',
                tag
            ) % (
                heading,
                file_data.file_name,
                src
            )

    # OTHER FILES = DOWNLOAD
    else:

        # Normal download URL
        download_src = urllib.parse.urljoin(
            Var.URL,
            f'{secure_hash}{str(id)}?hash={secure_hash}'
        )

        async with aiofiles.open(
            'Adarsh/template/dl.html'
        ) as r:

            async with aiohttp.ClientSession() as s:

                async with s.get(
                    download_src
                ) as u:

                    heading = 'Download {}'.format(
                        file_data.file_name
                    )

                    content_length = u.headers.get(
                        'Content-Length'
                    )

                    if content_length:
                        file_size = humanbytes(
                            int(content_length)
                        )
                    else:
                        file_size = humanbytes(
                            int(file_data.file_size)
                        )

                    html = (
                        await r.read()
                    ) % (
                        heading,
                        file_data.file_name,
                        download_src,
                        file_size
                    )

    return html