import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_STR = os.getenv("ADMIN_ID")
ADMIN_ID = int(ADMIN_ID_STR) if ADMIN_ID_STR else 0

router = Router()


class OrderState(StatesGroup):
    waiting_for_comment = State()


SERVICES = {
    "app_tg": {"name": "Мини-апп Telegram", "price": 25000},
    "app_max": {"name": "Мини-апп MAX", "price": 32000},
    "bot_tg": {"name": "Бот Telegram", "price": 8000},
    "bot_max": {"name": "Бот MAX", "price": 10000},
    "landing": {"name": "Лендинг", "price": 15000},
    "site": {"name": "Сайт (до 5 страниц)", "price": 25000},
    "stickers": {"name": "Пак стикеров (6 шт.)", "price": 3500},
}


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💼 Мои услуги и цены", callback_data="services")],
            [InlineKeyboardButton(text="🧮 Рассчитать стоимость", callback_data="calc")],
            [InlineKeyboardButton(text="👤 Обо мне", callback_data="about")],
            [InlineKeyboardButton(text="🌐 Наш сайт", url="https://джессилис.рф")],
            [InlineKeyboardButton(text="✍️ Написать мне напрямую", url="https://t.me/JessiLis")],
        ]
    )


@router.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я официальный помощник веб-разработчицы **JessiLis** (@JessiLisBot).\n"
        "Здесь вы можете посмотреть мои услуги, рассчитать примерную стоимость проекта или оставить заявку."
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="Markdown")


@router.message(Command("services"))
async def cmd_services(message: Message):
    text = "📋 **Мои услуги и стартовые цены:**\n\n"
    for key, val in SERVICES.items():
        price_formatted = f"{val['price']:,}".replace(",", " ")
        text += f"• {val['name']} — **от {price_formatted} ₽**\n"
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("calc"))
async def cmd_calc(message: Message):
    await message.answer("🧮 Воспользуйтесь калькулятором через главное меню:", reply_markup=main_menu())


@router.message(Command("about"))
async def cmd_about(message: Message):
    text = (
        "👩‍💻 **Обо мне:**\n\n"
        "Я веб-разработчик (JessiLis). Работаю одна, поэтому вы общаетесь напрямую со мной на всех этапах.\n"
        "• 5 лет опыта в разработке\n"
        "• Официально (самозанятая: договор и чек)\n"
        "• Гарантия 14 дней после сдачи\n\n"
        "🌐 Сайт: https://джессилис.рф"
    )
    await message.answer(text, parse_mode="Markdown")


@router.callback_query(F.data == "about")
async def process_about(callback: CallbackQuery):
    text = (
        "👩‍💻 **Обо мне:**\n\n"
        "Я веб-разработчик (JessiLis). Работаю одна, поэтому вы общаетесь напрямую со мной на всех этапах.\n"
        "• 5 лет опыта в разработке\n"
        "• Официально (самозанятая: договор и чек)\n"
        "• Гарантия 14 дней после сдачи"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "services")
async def process_services(callback: CallbackQuery):
    text = "📋 **Мои услуги и стартовые цены:**\n\n"
    for key, val in SERVICES.items():
        price_formatted = f"{val['price']:,}".replace(",", " ")
        text += f"• {val['name']} — **от {price_formatted} ₽**\n"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧮 Перейти к калькулятору", callback_data="calc")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "calc")
async def process_calc(callback: CallbackQuery):
    kb_list = []
    for key, val in SERVICES.items():
        price_formatted = f"{val['price']:,}".replace(",", " ")
        kb_list.append([InlineKeyboardButton(text=f"{val['name']} ({price_formatted} ₽)", callback_data=f"sel_{key}")])
    kb_list.append([InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main")])

    await callback.message.edit_text(
        "🧮 **Калькулятор стоимости**\n\nВыберите основную услугу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sel_"))
async def process_service_selected(callback: CallbackQuery, state: FSMContext):
    service_key = callback.data.split("_")[1]
    service_info = SERVICES.get(service_key)

    await state.update_data(service=service_info["name"], price=service_info["price"])
    price_formatted = f"{service_info['price']:,}".replace(",", " ")

    text = (
        f"Вы выбрали: **{service_info['name']}** (от {price_formatted} ₽)\n\n"
        "Напишите короткий комментарий к вашему заказу (опишите задачу) или нажмите кнопку ниже, чтобы пропустить:"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⏭ Пропустить и отправить заявку", callback_data="skip_comment")]]
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await state.set_state(OrderState.waiting_for_comment)
    await callback.answer()


@router.message(OrderState.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    await send_order_result(message, data, comment=message.text)
    await state.clear()


@router.callback_query(F.data == "skip_comment")
async def process_skip_comment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await send_order_result(callback.message, data, comment="Без комментариев")
    await state.clear()
    await callback.answer()


async def send_order_result(message: Message, data: dict, comment: str):
    user = message.from_user
    price_formatted = f"{data.get('price', 0):,}".replace(",", " ")
    
    client_text = (
        f"🎉 **Ваша заявка успешно отправлена!**\n\n"
        f"• Услуга: {data.get('service')}\n"
        f"• Ориентировочная цена: от {price_formatted} ₽\n"
        f"• Комментарий: {comment}\n\n"
        "Я уже получила уведомление и скоро свяжусь с вами!"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_main")]]
    )
    
    if isinstance(message, Message):
        await message.answer(client_text, reply_markup=kb, parse_mode="Markdown")
        bot_instance = message.bot
    else:
        await message.message.edit_text(client_text, reply_markup=kb, parse_mode="Markdown")
        bot_instance = message.bot

    admin_text = (
        f"🔔 **Новая заявка из бота (@JessiLisBot)!**\n\n"
        f"👤 Клиент: {user.full_name} (@{user.username if user.username else 'нет юзернейма'})\n"
        f"🆔 ID: `{user.id}`\n"
        f"💼 Услуга: {data.get('service')}\n"
        f"💰 Цена: от {price_formatted} ₽\n"
        f"💬 Комментарий: {comment}"
    )
    
    try:
        if ADMIN_ID:
            await bot_instance.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Не удалось отправить уведомление админу: {e}")


@router.callback_query(F.data == "back_to_main")
async def process_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "Главное меню. Выберите, что вас интересует:",
        reply_markup=main_menu(),
    )
    await callback.answer()


async def handle(request):
    return web.Response(text="JessiLis Bot is running!")

async def web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()


async def main():
    logging.basicConfig(level=logging.INFO)
    if not TOKEN:
        logging.error("Токен бота не найден! Проверьте переменные окружения BOT_TOKEN.")
        return
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    await web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
