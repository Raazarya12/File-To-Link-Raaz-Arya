# Aadhi000

from Adarsh.bot import StreamBot
from Adarsh.vars import Var
import logging
import asyncio

from Adarsh.bot.plugins.stream import MY_PASS
from Adarsh.utils.human_readable import humanbytes
from Adarsh.utils.database import Database
from Adarsh.utils.file_properties import get_name, get_hash, get_media_file_size

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant

logger = logging.getLogger(__name__)

db = Database(Var.DATABASE_URL, Var.name)


# =========================================================
# DATABASE USER ADD
# =========================================================

async def register_user(bot, message):
    try:
        user_id = message.from_user.id

        if not await db.is_user_exist(user_id):
            await db.add_user(user_id)

            try:
                await bot.send_message(
                    Var.BIN_CHANNEL,
                    f"#NEW_USER:\n\n"
                    f"New User [{message.from_user.first_name}]"
                    f"(tg://user?id={user_id}) Started !!"
                )
            except Exception as e:
                logger.error(
                    f"BIN_CHANNEL ERROR: {e}"
                )

    except Exception as e:
        logger.error(
            f"DATABASE ERROR: {e}"
        )


# =========================================================
# BACKGROUND USER REGISTRATION
# =========================================================

def register_user_background(bot, message):
    """
    Register user in background.

    IMPORTANT:
    Do not wait for MongoDB here.
    This prevents /start, /help and /about
    from getting delayed by database connection timeout.
    """
    try:
        asyncio.create_task(
            register_user(bot, message)
        )
    except Exception as e:
        logger.error(
            f"BACKGROUND REGISTER ERROR: {e}"
        )


# =========================================================
# FORCE SUB CHECK
# =========================================================

async def force_sub(bot, message):

    if Var.UPDATES_CHANNEL is None:
        return True

    try:
        user = await bot.get_chat_member(
            Var.UPDATES_CHANNEL,
            message.chat.id
        )

        if user.status == "banned":
            await bot.send_message(
                chat_id=message.chat.id,
                text="**ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ../**",
                disable_web_page_preview=True
            )
            return False

        return True

    except UserNotParticipant:

        await bot.send_message(
            chat_id=message.chat.id,
            text=(
                "**ᴊᴏɪɴ ᴍʏ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴍᴇ..**\n\n"
                "**ᴅᴜᴇ ᴛᴏ ᴏᴠᴇʀʟᴏᴀᴅ ᴏɴʟʏ ᴄʜᴀɴɴᴇʟ sᴜʙsᴄʀɪʙᴇʀs "
                "ᴄᴀɴ ᴜsᴇ ᴍᴇ..!**"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "ᴊᴏɪɴ ᴍʏ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ",
                            url="https://t.me/Latest_Movies_FreeOnNet"
                        )
                    ]
                ]
            )
        )

        return False

    except Exception as e:

        logger.error(
            f"FORCE SUB ERROR: {e}"
        )

        await bot.send_message(
            chat_id=message.chat.id,
            text="**𝙰𝙳𝙳 𝙵𝙾𝚁𝙲𝙴 𝚂𝚄𝙱 𝚃𝙾 𝙰𝙽𝚈 𝙲𝙷𝙰𝙽𝙽𝙴𝙻**",
            disable_web_page_preview=True
        )

        return False


# =========================================================
# START
# =========================================================

@StreamBot.on_message(
    filters.command("start") & filters.private
)
async def start(bot, message):

    # -----------------------------------------------------
    # REGISTER USER IN BACKGROUND
    # -----------------------------------------------------
    # MongoDB will NOT block /start response.
    # -----------------------------------------------------

    register_user_background(
        bot,
        message
    )

    usr_cmd = message.text.split("_")[-1]

    # -----------------------------------------------------
    # NORMAL /START
    # -----------------------------------------------------

    if usr_cmd == "/start":

        if not await force_sub(
            bot,
            message
        ):
            return

        await message.reply_photo(
            photo="https://telegra.ph/file/3cd15a67ad7234c2945e7.jpg",

            caption=(
                "**ʜᴇʟʟᴏ...⚡\n\n"
                "ɪᴀᴍ ᴀ sɪᴍᴘʟᴇ ᴛᴇʟᴇɢʀᴀᴍ ғɪʟᴇ/ᴠɪᴅᴇᴏ "
                "ᴛᴏ ᴘᴇʀᴍᴀɴᴇɴᴛ ʟɪɴᴋ ᴀɴᴅ sᴛʀᴇᴀᴍ ʟɪɴᴋ "
                "ɢᴇɴᴇʀᴀᴛᴏʀ ʙᴏᴛ.**\n\n"

                "**ᴜsᴇ /help ғᴏʀ ᴍᴏʀᴇ ᴅᴇᴛᴀɪʟs\n\n"
                "sᴇɴᴅ ᴍᴇ ᴀɴʏ ᴠɪᴅᴇᴏ / ғɪʟᴇ ᴛᴏ sᴇᴇ ᴍʏ "
                "ᴘᴏᴡᴇʀᴢ...**"
            ),

            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⚡ ᴜᴘᴅᴀᴛᴇᴢ ⚡",
                            url="https://t.me/Latest_Movies_FreeOnNet"
                        ),
                        InlineKeyboardButton(
                            "⚡ sᴜᴘᴘᴏʀᴛ ⚡",
                            url="https://t.me/mix_cinema_Box"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "💸 ᴅᴏɴᴀᴛᴇ 💸",
                            url="https://t.me/Finding_Movies"
                        ),
                        InlineKeyboardButton(
                            "💠 ɢɪᴛʜᴜʙ 💠",
                            url="https://github.com/Aadhi000"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "💌 sᴜʙsᴄʀɪʙᴇ 💌",
                            url="https://youtube.com/@latest_movies_freeonnet"
                        )
                    ]
                ]
            )
        )

        return

    # -----------------------------------------------------
    # START WITH FILE ID
    # -----------------------------------------------------

    if not await force_sub(
        bot,
        message
    ):
        return

    try:

        msg_id = int(usr_cmd)

        get_msg = await bot.get_messages(
            chat_id=Var.BIN_CHANNEL,
            ids=msg_id
        )

    except Exception as e:

        logger.error(
            f"GET MESSAGE ERROR: {e}"
        )

        await message.reply_text(
            "**❌ File not found or link is invalid.**"
        )

        return

    file_size = None
    file_name = None

    if get_msg.video:

        file_size = humanbytes(
            get_msg.video.file_size
        )

        file_name = (
            get_msg.video.file_name
        )

    elif get_msg.document:

        file_size = humanbytes(
            get_msg.document.file_size
        )

        file_name = (
            get_msg.document.file_name
        )

    elif get_msg.audio:

        file_size = humanbytes(
            get_msg.audio.file_size
        )

        file_name = (
            get_msg.audio.file_name
        )

    else:

        await message.reply_text(
            "**❌ This message does not contain a supported file.**"
        )

        return

    # -----------------------------------------------------
    # STREAM LINK
    # -----------------------------------------------------

    if Var.ON_HEROKU or Var.NO_PORT:

        stream_link = "https://{}/{}".format(
            Var.FQDN,
            get_msg.id
        )

    else:

        stream_link = "http://{}:{}/{}".format(
            Var.FQDN,
            Var.PORT,
            get_msg.id
        )

    # -----------------------------------------------------
    # MESSAGE
    # -----------------------------------------------------

    msg_text = (
        "**ᴛᴏᴜʀ ʟɪɴᴋ ɪs ɢᴇɴᴇʀᴀᴛᴇᴅ...⚡\n\n"
        "📧 ғɪʟᴇ ɴᴀᴍᴇ :-\n{}\n\n"
        "📦 ғɪʟᴇ sɪᴢᴇ :- {}\n\n"
        "💌 ᴅᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ :- {}\n\n"
        "♻️ ᴛʜɪs ʟɪɴᴋ ɪs ᴘᴇʀᴍᴀɴᴇɴᴛ "
        "ᴀɴᴅ ᴡᴏɴ'ᴛ ɢᴇᴛ ᴇxᴘɪʀᴇᴅ ♻️\n\n"
        "<b>❖ YouTube.com/@latest_movies_freeonnet</b>**"
    )

    await message.reply_text(
        text=msg_text.format(
            file_name,
            file_size,
            stream_link
        ),

        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⚡ ᴅᴏᴡɴʟᴏᴀᴅ ɴᴏᴡ ⚡",
                        url=stream_link
                    )
                ]
            ]
        )
    )


# =========================================================
# HELP
# =========================================================

@StreamBot.on_message(
    filters.command("help") & filters.private
)
async def help_handler(bot, message):

    # Register user without waiting for MongoDB
    register_user_background(
        bot,
        message
    )

    if not await force_sub(
        bot,
        message
    ):
        return

    await message.reply_photo(
        photo="https://telegra.ph/file/3cd15a67ad7234c2945e7.jpg",

        caption=(
            "**┣⪼ sᴇɴᴅ ᴍᴇ ᴀɴʏ ғɪʟᴇ/ᴠɪᴅᴇᴏ ᴛʜᴇɴ ɪ ᴡɪʟʟ "
            "ɢɪᴠᴇ ʏᴏᴜ ᴀ ᴘᴇʀᴍᴀɴᴇɴᴛ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ ᴏғ ɪᴛ...\n\n"

            "┣⪼ ᴛʜɪs ʟɪɴᴋ ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ "
            "ᴏʀ ᴛᴏ sᴛʀᴇᴀᴍ ᴜsɪɴɢ ᴇxᴛᴇʀɴᴀʟ ᴠɪᴅᴇᴏ ᴘʟᴀʏᴇʀs...\n\n"

            "┣⪼ ᴛʜɪs ʙᴏᴛ ᴀʟsᴏ sᴜᴘᴘᴏʀᴛs ᴄʜᴀɴɴᴇʟs. "
            "ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴀs ᴀᴅᴍɪɴ...\n\n"

            "┣⪼ ғᴏʀ ᴍᴏʀᴇ ɪɴғᴏʀᴍᴀᴛɪᴏɴ :- /about\n\n"

            "ᴘʟᴇᴀsᴇ sʜᴀʀᴇ ᴀɴᴅ sᴜʙsᴄʀɪʙᴇ**"
        ),

        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⚡ ᴜᴘᴅᴀᴛᴇᴢ ⚡",
                        url="https://t.me/Latest_movies_FreeOnNet"
                    ),
                    InlineKeyboardButton(
                        "⚡ sᴜᴘᴘᴏʀᴛ ⚡",
                        url="https://t.me/mix_cinema_Box"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "💸 ᴅᴏɴᴀᴛᴇ 💸",
                        url="https://t.me/Finding_Movies"
                    ),
                    InlineKeyboardButton(
                        "💠 ɢɪᴛʜᴜʙ 💠",
                        url="https://github.com/Aadhi000"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "💌 sᴜʙsᴄʀɪʙᴇ 💌",
                        url="https://youtube.com/@latest_movies_freeonnet"
                    )
                ]
            ]
        )
    )


# =========================================================
# ABOUT
# =========================================================

@StreamBot.on_message(
    filters.command("about") & filters.private
)
async def about_handler(bot, message):

    # Register user without waiting for MongoDB
    register_user_background(
        bot,
        message
    )

    if not await force_sub(
        bot,
        message
    ):
        return

    await message.reply_photo(
        photo="https://telegra.ph/file/3cd15a67ad7234c2945e7.jpg",

        caption="""<b>sᴏᴍᴇ ʜɪᴅᴅᴇɴ ᴅᴇᴛᴀɪʟs 😜</b>

<b>╭━━━━━━━〔ғɪʟᴇ ᴛᴏ ʟɪɴᴋ ʙᴏᴛ〕</b>
┃
┣⪼ <b>ʙᴏᴛ ɴᴀᴍᴇ : <a href='https://github.com/Aadhi000/File-To-Link'>ғɪʟᴇ ᴛᴏ ʟɪɴᴋ</a></b>
┣⪼ <b>ᴜᴘᴅᴀᴛᴇᴢ : <a href='https://t.me/Latest_Movies_FreeOnNet'>ᴍᴡ ᴜᴘᴅᴀᴛᴇᴢ</a></b>
┣⪼ <b>sᴜᴘᴘᴏʀᴛ : <a href='https://t.me/mix_cinema_Box'>ᴏᴘᴜs ᴛᴇᴄʜᴢ</a></b>
┣⪼ <b>sᴇʀᴠᴇʀ : ʜᴇʀᴜᴋᴏ / ᴋᴏʏᴇʙ</b>
┣⪼ <b>ʟɪʙʀᴀʀʏ : ᴘʏʀᴏɢʀᴀᴍ</b>
┣⪼ <b>ʟᴀɴɢᴜᴀɢᴇ : ᴘʏᴛʜᴏɴ 3</b>
┣⪼ <b>sᴏᴜʀᴄᴇ-ᴄᴏᴅᴇ : <a href='https://github.com/Aadhi000/File-To-Link'>ғɪʟᴇ ᴛᴏ ʟɪɴᴋ</a></b>
┣⪼ <b>ʏᴏᴜᴛᴜʙᴇ : <a href='https://youtube.com/@latest_movies_freeonnet'>Titanoboa</a></b>
┃
<b>╰━━━━━━━〔ᴘʟᴇᴀsᴇ sᴜᴘᴘᴏʀᴛ〕</b>""",

        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⚡ ᴜᴘᴅᴀᴛᴇᴢ ⚡",
                        url="https://t.me/Latest_movies_FreeOnnet"
                    ),
                    InlineKeyboardButton(
                        "💸 ᴅᴏɴᴀᴛᴇ 💸",
                        url="none"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "💌 sᴜʙsᴄʀɪʙᴇ 💌",
                        url="https://youtube.com@latest_movies_freeonnet"
                    )
                ]
            ]
        )
    )