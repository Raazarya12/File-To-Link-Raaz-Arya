# (c) Adarsh-Goel

import os
import asyncio
from asyncio import TimeoutError

from Adarsh.bot import StreamBot
from Adarsh.utils.database import Database
from Adarsh.utils.human_readable import humanbytes
from Adarsh.vars import Var
from Adarsh.utils.file_properties import (
    get_name,
    get_hash,
    get_media_file_size
)

from urllib.parse import quote_plus

from pyrogram import filters, Client
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


# =========================================================
# DATABASE
# =========================================================

db = Database(
    Var.DATABASE_URL,
    Var.name
)

MY_PASS = os.environ.get(
    "MY_PASS",
    None
)

pass_dict = {}

pass_db = Database(
    Var.DATABASE_URL,
    "ag_passwords"
)


# =========================================================
# FORCE SUB CACHE
# =========================================================
#
# User ka force-sub status kuch time ke liye cache rahega.
# Isse har file par Telegram get_chat_member call nahi hoga.
#
# Format:
# {user_id: timestamp}
# =========================================================

force_sub_cache = {}

FORCE_SUB_CACHE_TIME = 300


# =========================================================
# BACKGROUND USER REGISTRATION
# =========================================================

async def register_user_background(bot, message):

    try:

        user_id = message.from_user.id

        # -------------------------------------------------
        # Check user
        # -------------------------------------------------

        exists = await db.is_user_exist(
            user_id
        )

        if exists:
            return

        # -------------------------------------------------
        # Add user
        # -------------------------------------------------

        await db.add_user(
            user_id
        )

        # -------------------------------------------------
        # Notify BIN CHANNEL
        # -------------------------------------------------

        try:

            await bot.send_message(
                Var.BIN_CHANNEL,

                f"Nᴇᴡ Usᴇʀ Jᴏɪɴᴇᴅ :\n\n"
                f"Nᴀᴍᴇ : [{message.from_user.first_name}]"
                f"(tg://user?id={user_id}) "
                f"Sᴛᴀʀᴛᴇᴅ Yᴏᴜʀ Bᴏᴛ !!"
            )

        except Exception as e:

            print(
                f"BIN CHANNEL ERROR: {e}"
            )

    except Exception as e:

        # -------------------------------------------------
        # IMPORTANT:
        # Database error must NEVER block file processing.
        # -------------------------------------------------

        print(
            f"DATABASE BACKGROUND ERROR: {e}"
        )


def start_user_registration(
    bot,
    message
):

    try:

        asyncio.create_task(
            register_user_background(
                bot,
                message
            )
        )

    except Exception as e:

        print(
            f"BACKGROUND TASK ERROR: {e}"
        )


# =========================================================
# LOGIN
# =========================================================

@StreamBot.on_message(
    (
        filters.regex("login🔑")
        | filters.command("login")
    ),
    group=4
)
async def login_handler(
    c: Client,
    m: Message
):

    try:

        try:

            ag = await m.reply_text(
                "Now send me password.\n\n"
                "If You don't know check the "
                "MY_PASS Variable in heroku\n\n"
                "(You can use /cancel command "
                "to cancel the process)"
            )

            _text = await c.listen(
                m.chat.id,
                filters=filters.text,
                timeout=90
            )

            if _text.text:

                textp = _text.text

                if textp == "/cancel":

                    await ag.edit(
                        "Process Cancelled Successfully"
                    )

                    return

            else:

                return

        except TimeoutError:

            await ag.edit(
                "I can't wait more for password, "
                "try again"
            )

            return

        if textp == MY_PASS:

            await pass_db.add_user_pass(
                m.chat.id,
                textp
            )

            ag_text = (
                "yeah! you entered the "
                "password correctly"
            )

        else:

            ag_text = (
                "Wrong password, try again"
            )

        await ag.edit(
            ag_text
        )

    except Exception as e:

        print(
            f"LOGIN ERROR: {e}"
        )


# =========================================================
# PRIVATE FILE RECEIVE
# =========================================================

@StreamBot.on_message(
    (filters.private)
    & (
        filters.document
        | filters.video
        | filters.audio
        | filters.photo
    ),
    group=4
)
async def private_receive_handler(
    c: Client,
    m: Message
):

    # =====================================================
    # PASSWORD CHECK
    # =====================================================

    if MY_PASS:

        try:

            check_pass = await asyncio.wait_for(
                pass_db.get_user_pass(
                    m.chat.id
                ),
                timeout=5
            )

        except asyncio.TimeoutError:

            await m.reply_text(
                "⚠️ Database connection timeout.\n"
                "Please try again."
            )

            return

        except Exception as e:

            print(
                f"PASSWORD DATABASE ERROR: {e}"
            )

            await m.reply_text(
                "⚠️ Database error.\n"
                "Please try again later."
            )

            return

        if check_pass is None:

            await m.reply_text(
                "Login first using /login cmd\n"
                "Don't know the password contact "
                "@ArjunVR_AVR"
            )

            return

        if check_pass != MY_PASS:

            try:

                await pass_db.delete_user(
                    m.chat.id
                )

            except Exception as e:

                print(
                    f"PASSWORD DELETE ERROR: {e}"
                )

            return

    # =====================================================
    # DATABASE USER REGISTRATION
    # =====================================================
    #
    # IMPORTANT:
    # DO NOT await database here.
    #
    # This was causing the ~30 second delay.
    #
    # File processing continues immediately.
    # =====================================================

    start_user_registration(
        c,
        m
    )

    # =====================================================
    # FORCE SUB
    # =====================================================

    if Var.UPDATES_CHANNEL:

        user_id = m.from_user.id

        current_time = asyncio.get_running_loop().time()

        cached_time = force_sub_cache.get(
            user_id
        )

        # -------------------------------------------------
        # Use cached force-sub status
        # -------------------------------------------------

        if (
            cached_time is None
            or current_time - cached_time
            > FORCE_SUB_CACHE_TIME
        ):

            try:

                user = await asyncio.wait_for(
                    c.get_chat_member(
                        Var.UPDATES_CHANNEL,
                        m.chat.id
                    ),
                    timeout=5
                )

                if user.status == "kicked":

                    await c.send_message(
                        chat_id=m.chat.id,

                        text=(
                            "𝚈𝙾𝚄 𝙰𝚁𝙴 "
                            "𝙱𝙰𝙽𝙽𝙴𝙳../**"
                        ),

                        disable_web_page_preview=True
                    )

                    return

                # -------------------------------------------------
                # Cache successful force-sub check
                # -------------------------------------------------

                force_sub_cache[
                    user_id
                ] = current_time

            except UserNotParticipant:

                await c.send_message(
                    chat_id=m.chat.id,

                    text=(
                        "<i>"
                        "ᴊᴏɪɴ ᴍʏ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ "
                        "ᴛᴏ ᴜsᴇ ᴍᴇ..**"
                        "</i>"
                    ),

                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "ᴊᴏɪɴ ɴᴏᴡ",
                                    url=(
                                        f"https://t.me/Latest_movies_FreeOnnet"
                                        f"{Var.UPDATES_CHANNEL}"
                                    )
                                )
                            ]
                        ]
                    )
                )

                return

            except asyncio.TimeoutError:

                print(
                    "FORCE SUB CHECK TIMEOUT"
                )

                await m.reply_text(
                    "⚠️ Unable to verify channel "
                    "subscription. Please try again."
                )

                return

            except Exception as e:

                print(
                    f"FORCE SUB ERROR: {e}"
                )

                await c.send_message(
                    chat_id=m.chat.id,

                    text=(
                        "**𝙰𝙳𝙳 𝙵𝙾𝚁𝙲𝙴 𝚂𝚄𝙱 "
                        "𝚃𝙾 𝙰𝙽𝚈 𝙲𝙷𝙰𝙽𝙽𝙴𝙻**"
                    ),

                    disable_web_page_preview=True
                )

                return

    # =====================================================
    # GENERATE LINK
    # =====================================================

    try:

        # -------------------------------------------------
        # Forward file to BIN CHANNEL
        # -------------------------------------------------

        log_msg = await m.forward(
            chat_id=Var.BIN_CHANNEL
        )

        # -------------------------------------------------
        # Generate WATCH link
        # -------------------------------------------------

        file_hash = get_hash(
            log_msg
        )

        file_name = get_name(
            log_msg
        )

        encoded_name = quote_plus(
            file_name
        )

        stream_link = (
            f"{Var.URL}"
            f"watch/"
            f"{str(log_msg.id)}/"
            f"{encoded_name}"
            f"?hash={file_hash}"
        )

        # -------------------------------------------------
        # Generate DOWNLOAD link
        # -------------------------------------------------

        online_link = (
            f"{Var.URL}"
            f"{str(log_msg.id)}/"
            f"{encoded_name}"
            f"?hash={file_hash}"
        )

        # -------------------------------------------------
        # Thumbnail / image
        # -------------------------------------------------

        photo_xr = (
            "https://telegra.ph/file/"
            "3cd15a67ad7234c2945e7.jpg"
        )

        # -------------------------------------------------
        # Message
        # -------------------------------------------------

        msg_text = """
<b>ʏᴏᴜʀ ʟɪɴᴋ ɪs ɢᴇɴᴇʀᴀᴛᴇᴅ...⚡

<b>📧 ғɪʟᴇ ɴᴀᴍᴇ :- </b>
<i><b>{}</b></i>

<b>📦 ғɪʟᴇ sɪᴢᴇ :- </b>
<i><b>{}</b></i>

<b>💌 ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ :- </b>
<i><b>{}</b></i>

<b>🖥 ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ :- </b>
<i><b>{}</b></i>

<b>♻️ ᴛʜɪs ʟɪɴᴋ ɪs ᴘᴇʀᴍᴀɴᴇɴᴛ
ᴀɴᴅ ᴡᴏɴ'ᴛ ɢᴇᴛs ᴇxᴘɪʀᴇᴅ ♻️

❖ YouTube.com/@latest_movies_freeonnet</b>
"""

        # -------------------------------------------------
        # BIN CHANNEL LOG
        # -------------------------------------------------

        await log_msg.reply_text(
            text=(
                f"**RᴇQᴜᴇꜱᴛᴇᴅ ʙʏ :** "
                f"[{m.from_user.first_name}]"
                f"(tg://user?id={m.from_user.id})\n"
                f"**Uꜱᴇʀ ɪᴅ :** "
                f"`{m.from_user.id}`\n"
                f"**Stream ʟɪɴᴋ :** "
                f"{stream_link}"
            ),

            disable_web_page_preview=True,
            quote=True
        )

        # -------------------------------------------------
        # SEND RESULT TO USER
        # -------------------------------------------------

        await m.reply_text(

            text=msg_text.format(
                file_name,
                humanbytes(
                    get_media_file_size(m)
                ),
                online_link,
                stream_link
            ),

            quote=True,

            disable_web_page_preview=True,

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⚡ ᴡᴀᴛᴄʜ ⚡",
                            url=stream_link
                        ),

                        InlineKeyboardButton(
                            "⚡ ᴅᴏᴡɴʟᴏᴀᴅ ⚡",
                            url=online_link
                        )
                    ]
                ]
            )
        )

    # =====================================================
    # FLOOD WAIT
    # =====================================================

    except FloodWait as e:

        print(
            f"Sleeping for {str(e.x)}s"
        )

        await asyncio.sleep(
            e.x
        )

        await c.send_message(
            chat_id=Var.BIN_CHANNEL,

            text=(
                f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ "
                f"{str(e.x)}s from "
                f"[{m.from_user.first_name}]"
                f"(tg://user?id={m.from_user.id})\n\n"
                f"**𝚄𝚜𝚎𝚛 𝙸𝙳 :** "
                f"`{str(m.from_user.id)}`"
            ),

            disable_web_page_preview=True
        )

    except Exception as e:

        print(
            f"PRIVATE FILE ERROR: {e}"
        )


# =========================================================
# CHANNEL RECEIVE
# =========================================================

@StreamBot.on_message(
    filters.channel
    & ~filters.group
    & (
        filters.document
        | filters.video
        | filters.photo
    )
    & ~filters.forwarded,
    group=-1
)
async def channel_receive_handler(
    bot,
    broadcast
):

    # =====================================================
    # PASSWORD CHECK
    # =====================================================

    if MY_PASS:

        try:

            check_pass = await asyncio.wait_for(
                pass_db.get_user_pass(
                    broadcast.chat.id
                ),
                timeout=5
            )

        except asyncio.TimeoutError:

            await broadcast.reply_text(
                "⚠️ Database connection timeout."
            )

            return

        except Exception as e:

            print(
                f"CHANNEL PASSWORD DB ERROR: {e}"
            )

            await broadcast.reply_text(
                "⚠️ Database error. "
                "Please try again later."
            )

            return

        if check_pass is None:

            await broadcast.reply_text(
                "Login first using /login cmd\n"
                "don't know the pass? "
                "request it from @opustechz"
            )

            return

        if check_pass != MY_PASS:

            await broadcast.reply_text(
                "Wrong password, login again"
            )

            try:

                await pass_db.delete_user(
                    broadcast.chat.id
                )

            except Exception as e:

                print(
                    f"PASSWORD DELETE ERROR: {e}"
                )

            return

    # =====================================================
    # BANNED CHANNEL
    # =====================================================

    if int(broadcast.chat.id) in Var.BANNED_CHANNELS:

        await bot.leave_chat(
            broadcast.chat.id
        )

        return

    # =====================================================
    # GENERATE CHANNEL LINK
    # =====================================================

    try:

        log_msg = await broadcast.forward(
            chat_id=Var.BIN_CHANNEL
        )

        file_hash = get_hash(
            log_msg
        )

        file_name = get_name(
            log_msg
        )

        encoded_name = quote_plus(
            file_name
        )

        stream_link = (
            f"{Var.URL}"
            f"watch/"
            f"{str(log_msg.id)}/"
            f"{encoded_name}"
            f"?hash={file_hash}"
        )

        online_link = (
            f"{Var.URL}"
            f"{str(log_msg.id)}/"
            f"{encoded_name}"
            f"?hash={file_hash}"
        )

        # -------------------------------------------------
        # BIN CHANNEL LOG
        # -------------------------------------------------

        await log_msg.reply_text(

            text=(
                f"**Cʜᴀɴɴᴇʟ Nᴀᴍᴇ:** "
                f"`{broadcast.chat.title}`\n"
                f"**Cʜᴀɴɴᴇʟ ID:** "
                f"`{broadcast.chat.id}`\n"
                f"**Rᴇǫᴜᴇsᴛ ᴜʀʟ:** "
                f"{stream_link}"
            ),

            quote=True
        )

        # -------------------------------------------------
        # EDIT ORIGINAL CHANNEL MESSAGE
        # -------------------------------------------------

        await bot.edit_message_reply_markup(

            chat_id=broadcast.chat.id,

            id=broadcast.id,

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⚡ ᴡᴀᴛᴄʜ ⚡",
                            url=stream_link
                        ),

                        InlineKeyboardButton(
                            "⚡ ᴅᴏᴡɴʟᴏᴀᴅ ⚡",
                            url=online_link
                        )
                    ]
                ]
            )
        )

    # =====================================================
    # FLOOD WAIT
    # =====================================================

    except FloodWait as w:

        print(
            f"Sleeping for {str(w.x)}s"
        )

        await asyncio.sleep(
            w.x
        )

        await bot.send_message(

            chat_id=Var.BIN_CHANNEL,

            text=(
                f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ "
                f"{str(w.x)}s from "
                f"{broadcast.chat.title}\n\n"
                f"**Cʜᴀɴɴᴇʟ ID:** "
                f"`{str(broadcast.chat.id)}`"
            ),

            disable_web_page_preview=True
        )

    except Exception as e:

        await bot.send_message(

            chat_id=Var.BIN_CHANNEL,

            text=(
                f"**#ᴇʀʀᴏʀ_ᴛʀᴀᴄᴇʙᴀᴄᴋ:** "
                f"`{e}`"
            ),

            disable_web_page_preview=True
        )

        print(
            "Cᴀɴ'ᴛ Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ!\n"
            f"Eʀʀᴏʀ: "
            f"Give me edit permission in updates "
            f"and bin Channel {e}"
        )