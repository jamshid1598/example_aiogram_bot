import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Initialize router and dispatcher
router = Router()
dp = Dispatcher(storage=MemoryStorage())

# Define states for form data collection
class FormStates(StatesGroup):
    Name = State()
    Age = State()
    Confirmation = State()

# Define states for response mode
class ModeStates(StatesGroup):
    Text = State()
    Voice = State()

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Create inline keyboard with Back button
def get_back_button(target_state: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅ Back", callback_data=f"back_{target_state}")]
    ])

# Handler for /start command
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await message.answer(
        "Hello! Let's start by choosing your response mode. "
        "Do you prefer text or voice responses? (Type 'text' or 'voice')",
        reply_markup=get_back_button("start")
    )
    await state.set_state(ModeStates.Text)  # Default to Text state

# Handler for setting response mode
@router.message(ModeStates.Text)
async def process_mode(message: Message, state: FSMContext) -> None:
    mode = message.text.lower()
    if mode not in ["text", "voice"]:
        await message.answer("Please type 'text' or 'voice'.", reply_markup=get_back_button("start"))
        return
    await state.update_data(response_mode=mode)
    await state.set_state(ModeStates.Voice if mode == "voice" else ModeStates.Text)
    await message.answer(
        f"Got it! You chose {mode} mode. Now, let's collect some info. What's your name?",
        reply_markup=get_back_button("mode")
    )
    await state.set_state(FormStates.Name)

# Handler for name input
@router.message(FormStates.Name)
async def process_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await message.answer("Great! How old are you?", reply_markup=get_back_button("name"))
    await state.set_state(FormStates.Age)

# Handler for age input
@router.message(FormStates.Age)
async def process_age(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit():
        await message.answer("Please enter a valid number for age.", reply_markup=get_back_button("name"))
        return
    await state.update_data(age=int(message.text))
    user_data = await state.get_data()
    name = user_data.get("name")
    age = user_data.get("age")
    await message.answer(
        f"Please confirm your details:\nName: {name}\nAge: {age}\n"
        "Reply 'yes' to confirm or 'no' to restart.",
        reply_markup=get_back_button("age")
    )
    await state.set_state(FormStates.Confirmation)

# Handler for confirmation
@router.message(FormStates.Confirmation)
async def process_confirmation(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    response_mode = user_data.get("response_mode", "text")
    if message.text.lower() == "yes":
        await message.answer(
            f"Confirmed! Your details:\nName: {user_data['name']}\nAge: {user_data['age']}\n"
            f"Response mode: {response_mode}"
        )
        await state.clear()  # Reset all states
    else:
        await message.answer("Let's start over. What's your name?", reply_markup=get_back_button("mode"))
        await state.set_state(FormStates.Name)

# Handler for back button callbacks
# @router.inline_query(F.data.startswith("back_"))
@router.callback_query(F.data.startswith("back_"))
async def process_back_button(callback: CallbackQuery, state: FSMContext) -> None:
    target = callback.data.split("_")[1]
    if target == "start":
        await callback.message.answer(
            "Let's start over. Do you prefer text or voice responses? (Type 'text' or 'voice')",
            reply_markup=get_back_button("start")
        )
        await state.set_state(ModeStates.Text)
    elif target == "mode":
        await callback.message.answer(
            "Choose your response mode again. Type 'text' or 'voice'.",
            reply_markup=get_back_button("start")
        )
        await state.set_state(ModeStates.Text)
    elif target == "name":
        await callback.message.answer("What's your name again?", reply_markup=get_back_button("mode"))
        await state.set_state(FormStates.Name)
    elif target == "age":
        await callback.message.answer("How old are you?", reply_markup=get_back_button("name"))
        await state.set_state(FormStates.Age)
    await callback.answer()  # Acknowledge the callback

# Main function to start the bot
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
