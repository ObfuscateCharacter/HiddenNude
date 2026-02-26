import asyncio

import aiofiles
import orjson

import string
import random
from aiogram import Bot, Router, filters, F, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent,InputMediaPhoto, InputMediaVideo
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram_media_group import media_group_handler

TOKEN = "7968510511:AAEFty5Tup8aRaYgQrb1VdyXXwAXwdlkoCI"
bot = Bot(token=TOKEN)
dp = Dispatcher()


async def return_file_content(fname: str):
    async with aiofiles.open(file = fname, mode = "rb") as f:
        return orjson.loads(await f.read())


async def checkJoin(chat_id: int):
     try:
        member = await bot.get_chat_member(chat_id = -1002599159800, user_id = chat_id)
        if member.status not in ["member", "administrator", "creator"]:
            return False
     except TelegramBadRequest:
        return False
     return True


def return_user_log(chat_id, log_data):
   try:
       return log_data[str(chat_id)]
   except:
       return {}

def makeGroupMediaObject(list_file_id):
     return [InputMediaPhoto(media = f.replace("photo-",'')) if f.startswith('photo') else InputMediaVideo(media = f.replace('video-','')) for f in list_file_id]

async def addToDatabase(fname, Data):
    async with aiofiles.open(fname,mode = "rb+") as f:
        content: bytes = await f.read()
        media_json: dict[str, str] = orjson.loads(content)
        media_json.update(Data)
        await f.seek(0)
        await f.write(orjson.dumps(media_json, option = orjson.OPT_INDENT_2))


async def removeMedia(fname, key):
    async with aiofiles.open(fname, mode = "rb+") as r:
        content: bytes = await f.read()
        file_json: dict[str, str] = orjson.loads(content)
        del file_json[key]
        await r.seek(0)
        await r.write(orjson.dumps(file_json, option = orjson.OPT_INDENT_2))



@dp.message(F.media_group_id, F.content_type.in_({'photo','video'}))
@media_group_handler
async def album_handler(messages):
    random_name = 'list-'+''.join(random.sample(string.ascii_letters, 8))
    result = ['photo-'+m.photo[0].file_id if m.photo else 'video-'+m.video.file_id for m in messages]
    await addToDatabase("nude.json",{random_name:result})
    await bot.send_message(messages[0].chat.id, f"https://t.me/HiddenNude_Bot?start={random_name}")


@dp.message(F.chat.type == ChatType.PRIVATE and F.content_type.in_({"video", "photo"}))
async def command_start_handler(message: Message) -> None:
    media_fid,media_uid,type_media = None, None,""
    try:
        media_fid,media_uid = message.photo[0].file_id, message.photo[0].file_unique_id
        type_media = "photo"
    except TypeError:
        media_fid,media_uid = message.video.file_id,message.video.file_unique_id
        type_media = "video"
    log_result = await return_file_content("userlog.json")
    if str(message.chat.id) not in log_result:
        await addToDatabase("userlog.json",{f"{message.chat.id}": [type_media + '-' + media_uid]})
    else:
        log_result[str(message.chat.id)].append(f"{type_media}-{media_uid}")
        await addToDatabase("userlog.json",{str(message.chat.id):log_result[str(message.chat.id)]})
    await addToDatabase("nude.json", {type_media + "-" + media_uid:media_fid})
    await bot.send_message(message.chat.id, f"https://t.me/hiddenNude_bot?start={type_media}-{media_uid}")

@dp.message(F.chat.type == ChatType.PRIVATE and F.text.startswith("/start "))
async def sendMedia(message: Message):
    if await checkJoin(message.chat.id):
        target = message.text.split(' ')[1]
        task_allNude,task_user_received = asyncio.create_task(return_file_content("nude.json")),asyncio.create_task(return_file_content("user-recevied.json"))
        await task_user_received, task_allNude
        if str(message.chat.id) not in task_user_received.result():
              await addToDatabase("user-recevied.json",{str(message.chat.id):[target]})
        else:
              task_user_received.result()[str(message.chat.id)].append(target)
              await addToDatabase("user-recevied.json",{str(message.chat.id):task_user_received.result()[str(message.chat.id)]})
        if target.startswith("photo"):
            await bot.send_photo(message.chat.id, photo = task_allNude.result()[target])
        elif target.startswith("video"):
            await bot.send_video(message.chat.id, video = task_allNude.result()[target])
        else:
            await bot.send_media_group(message.chat.id, media = makeGroupMediaObject(task_allNude.result()[target]))
    else:
        await bot.send_message(chat_id = message.chat.id, text = "لطفا ابتدا در کانال\n@BdsmUniversity\n عضود شوید و سپس دوباره از طریق لینک مدیا ربات را استارت بکنید")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
