import asyncio
import logging
import pprint
import sys
from os import getenv

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from pydantic import BaseModel

TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()


class FoodService:

    async def validate_token(self, token: str) -> bool:
        # TODO mocked token validation
        if token == 'kitty-newyork13-caesar197-mustard10':
            return True
        return False


class DealDTO(BaseModel):
    id: int
    rating: int
    price: float  # TODO
    description: str
    amount: int

    def __str__(self):
        return f"Описание: {self.description} \nРейтинг: {self.rating} \nЦена: {self.price}"

    def __repr__(self):
        return f"Описание: {self.description} \nРейтинг: {self.rating} \nЦена: {self.price}"


class AccountDTO(BaseModel):
    account: str
    description: str

    def __str__(self):
        return f"Счет: {self.account} \nСпособ перевода: {self.description}"

    def __repr__(self):
        return f"Счет: {self.account} \nСпособ перевода: {self.description}"


class SellerListService:

    async def get_best_deal(self, amount: int | str) -> DealDTO:
        return DealDTO(id=1, rating=10, price=1.1, description="Перевод по СБП", amount=int(amount))

    async def notify_seller(self, seller_id: int) -> bool:
        await asyncio.sleep(5)
        return True

    async def get_seller_account(self, seller_id: int) -> AccountDTO:
        return AccountDTO(account="8-999-999-99-99", description="Перевод по СБП")

    async def perform_deal(self):
        await asyncio.sleep(5)


food_service = FoodService()
seller_service = SellerListService()


class MessageService:
    # TODO Working only for one active session!
    def __init__(self):
        self._message_list = []

    async def answer_message(self, message: Message, text: str, **kwargs):
        answer_message = await message.answer(text, **kwargs)
        self._message_list.append(answer_message)

    async def delete_messages(self):
        for message in self._message_list:
            try:
                await message.delete()
            except Exception:  #TODO only expired messages
                pass

    def add_user_message(self, message: Message):
        self._message_list.append(message)


message_service = MessageService()


class BuyState(StatesGroup):
    INPUT_TOKEN = State()
    INPUT_AMOUNT = State()
    VALIDATE_SELLER = State()
    MONEY_TRANSFER = State()
    SUCCESS = State()


@dp.message(Command("cancel"))
@dp.message(F.text.casefold() == "cancel")
@dp.message(F.text.casefold() == "отмена")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    message_service.add_user_message(message)
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message_service.answer_message(message,
                                         "Отменено, для начала напишите /start",
                                         reply_markup=ReplyKeyboardRemove(),
                                         )
    await message_service.delete_messages()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    message_service.add_user_message(message)
    await message_service.answer_message(message, f"Привет! Пришли мне имя котика",
                                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(BuyState.INPUT_TOKEN)


@dp.message(BuyState.INPUT_TOKEN)
async def input_token_handler(message: Message, state: FSMContext) -> None:
    message_service.add_user_message(message)
    await state.update_data(token=message.text)
    await message_service.answer_message(message, "Имя получено, валидация что котик хочет есть")
    is_valid_token = await food_service.validate_token(token=message.text)
    if not is_valid_token:
        await message_service.answer_message(message, "Этот котик не голоден")
        await state.clear()
        return
    await message_service.answer_message(message, "Котик голоден")
    await message_service.answer_message(message, "Введите желаемую сумму покупки корма")
    await state.set_state(BuyState.INPUT_AMOUNT)


@dp.message(BuyState.INPUT_AMOUNT)
async def input_amount_handler(message: Message, state: FSMContext) -> None:
    message_service.add_user_message(message)
    await state.update_data(amount=message.text)
    await message_service.answer_message(message, f"Вы хотите отправить {message.text}")
    await message_service.answer_message(message, f"Ищу лучшее предложение из доступных")
    deal = await seller_service.get_best_deal(message.text)
    await message_service.answer_message(message, "Найдено предложение для вас:")
    await message_service.answer_message(message, pprint.pformat(deal),
                                         reply_markup=ReplyKeyboardMarkup(
                                             keyboard=[
                                                 [
                                                     KeyboardButton(text="Да")
                                                 ]
                                             ],
                                             resize_keyboard=True,
                                         ),
                                         )
    await state.set_state(BuyState.VALIDATE_SELLER)
    await state.update_data(seller_id=deal.id)


@dp.message(BuyState.VALIDATE_SELLER)
async def input_amount_handler(message: Message, state: FSMContext) -> None:
    message_service.add_user_message(message)
    await message_service.answer_message(message, "Отлично! Вы выбрали этого продавца!",
                                         reply_markup=ReplyKeyboardRemove())
    await message_service.answer_message(message, "Ожидаю ответа от продавца корма")
    is_seller_available = await seller_service.notify_seller((await state.get_data())["seller_id"])
    if not is_seller_available:
        await message_service.answer_message(message, "Продавец не ответил. Начните сначала. ")
        await state.clear()
        return

    await message_service.answer_message(message, "Продавец подтвердил сделку")
    account = await seller_service.get_seller_account((await state.get_data())["seller_id"])
    await message_service.answer_message(message, "Переведите сумму по указанным реквизитам")
    await message_service.answer_message(message, pprint.pformat(account),
                                         reply_markup=ReplyKeyboardMarkup(
                                             keyboard=[
                                                 [
                                                     KeyboardButton(text="Готово")
                                                 ]
                                             ],
                                             resize_keyboard=True,
                                         ),
                                         )
    await state.set_state(BuyState.MONEY_TRANSFER)


@dp.message(BuyState.MONEY_TRANSFER, F.text.casefold() == "готово")
async def input_money_handler(message: Message, state: FSMContext) -> None:
    message_service.add_user_message(message)
    await message_service.answer_message(message, "Ожидание перевода со стороны продавца",
                                         reply_markup=ReplyKeyboardRemove())
    await seller_service.perform_deal()

    await message_service.answer_message(message, "Ура! Котик будет накормлен!")
    await message_service.answer_message(message, "Вы хотите получить напоминание через месяц?",
                                         reply_markup=ReplyKeyboardMarkup(
                                             keyboard=[
                                                 [
                                                     KeyboardButton(text="Да!"),
                                                     KeyboardButton(text="Нет (")
                                                 ]
                                             ],
                                             resize_keyboard=True,
                                         )
                                         )
    await state.set_state(BuyState.SUCCESS)


@dp.message(BuyState.SUCCESS)
async def input_success_handler(message: Message, state: FSMContext) -> None:
    message_service.add_user_message(message)
    await message_service.answer_message(message, "Договорились!", reply_markup=ReplyKeyboardRemove())
    await message_service.answer_message(message, "Удаляюсь!")
    await message_service.answer_message(message, "Для безопасности сами удалите этот диалог из своей истории!")
    await asyncio.sleep(10)
    await message_service.delete_messages()
    await state.clear()


async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    asyncio.run(main())
