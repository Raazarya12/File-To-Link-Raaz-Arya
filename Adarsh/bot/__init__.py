# (c) adarsh-goel

from pyrogram import utils

# Fix: newer Telegram channel IDs with Pyrogram 2.0.106
def get_peer_type_new(peer_id: int) -> str:
    peer_id_str = str(peer_id)

    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    else:
        return "chat"


utils.get_peer_type = get_peer_type_new


from pyrogram import Client
import pyromod.listen
from ..vars import Var
from os import getcwd


StreamBot = Client(
    name='Web Streamer',
    api_id=Var.API_ID,
    api_hash=Var.API_HASH,
    bot_token=Var.BOT_TOKEN,
    sleep_threshold=Var.SLEEP_THRESHOLD,
    workers=Var.WORKERS
)


multi_clients = {}
work_loads = {}