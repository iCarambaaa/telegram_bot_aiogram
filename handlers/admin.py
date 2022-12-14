from ast import In
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram import types, Dispatcher
from create_bot import dp, bot
from database import sqlite_db
from keyboards import admin_kb
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

ID = None


class FSMAdmin(StatesGroup):
    photo = State()
    name = State()
    description = State()
    price = State()


# get moderator ID
async def make_changes_command(message: types.Message):
    global ID
    ID = message.from_user.id
    await bot.send_message(message.from_user.id, "happy to serve human master, what can I do for you?", reply_markup=admin_kb.button_case_admin)
    await message.delete()


# handler for starting dialog to save new menu items
# @dp.message_handler(commands='upload', state=None)

async def cm_start(message: types.Message):
    if message.from_user.id == ID:
        await FSMAdmin.photo.set()
        await message.reply("upload photo")


# cancel state
async def cancel_handler(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.finish()
        await message.reply("OK")


# handler for first answer
# @dp.message_handler(content_types=["photo"], state=FSMAdmin.photo)

async def load_photo(message: types.Message, state=FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data["photo"] = message.photo[0].file_id
        await FSMAdmin.next()
        await message.reply("Enter the name")

# handler for second answer
# @dp.message_handler(state=FSMAdmin.name)


async def load_name(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data["name"] = message.text
        await FSMAdmin.next()
        await message.reply("Enter the description")

# handler for third answer
# @dp.message_handler(state=FSMAdmin.description)


async def load_description(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data["description"] = message.text
        await FSMAdmin.next()
        await message.reply("Enter the price")

# handler for fourth answer and usage of data
# @dp.message_handler(state=FSMAdmin.price)


async def load_price(message: types.Message, state: FSMContext):
    if message.from_user.id == ID:
        async with state.proxy() as data:
            data["price"] = float(message.text)

        await sqlite_db.sql_add_command(state)
        await state.finish()
        await message.reply("thank you")

# implement delete button


@dp.callback_query_handler(lambda x: x.data and x.data.startswith("del "))
async def del_callback_run(callback_query: types.CallbackQuery):
    await sqlite_db.sql_delete_command(callback_query.data.replace("del ", ""))
    await callback_query.answer(text=f'{callback_query.data.replace("del ", "")} deleted!', show_alert=True)


@dp.message_handler(commands="delete")
async def delete_item(message: types.Message):
    if message.from_user.id == ID:
        read = await sqlite_db.sql_read2()
        for ret in read:
            await bot.send_photo(message.from_user.id, ret[0], f'{ret[1]}\ndescription: {ret[2]}\nprice: {ret[-1]}')
            await bot.send_message(message.from_user.id, text='^^^', reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton(f'delete {ret[1]}', callback_data=f'del {ret[1]}')))


# register the handlers
def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(make_changes_command, commands=[
                                "admin"], is_chat_admin=True)
    dp.register_message_handler(cm_start, commands=["new_item"], state=None)
    dp.register_message_handler(cancel_handler, Text(
        equals="cancel", ignore_case=True), state="*")
    dp.register_message_handler(load_photo, content_types=[
                                "photo"], state=FSMAdmin.photo)
    dp.register_message_handler(load_name, state=FSMAdmin.name)
    dp.register_message_handler(load_description, state=FSMAdmin.description)
    dp.register_message_handler(load_price, state=FSMAdmin.price)
    dp.register_message_handler(cancel_handler, state="*", commands="cancel")
