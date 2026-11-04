from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import database as db
from keyboards import (
    get_gender_keyboard, 
    get_main_menu_keyboard
)

router = Router()

class RegistrationStates(StatesGroup):
    full_name = State()
    age = State()
    city = State()
    gender = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    # Agar oldin ro'yxatdan o'tgan bo'lsa
    if user:
        is_vip = bool(user.get("is_vip"))
        vip_status = "⭐ VIP Obunachi" if is_vip else "Oddiy a'zo"
        await message.answer(
            f"Assalomu alaykum, {user.get('full_name')}!\n"
            f"Tanishuv botiga xush kelibsiz.\n\n"
            f"📌 Sizning maqomingiz: <b>{vip_status}</b>\n\n"
            f"Muloqotni boshlash uchun quyidagi menyudan foydalaning:",
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(is_vip)
        )
        return

    # Yangi foydalanuvchi bo'lsa ro'yxatdan o'tkazamiz
    await message.answer(
        "👋 <b>Assalomu alaykum! Tanishuv botimizga xush kelibsiz.</b>\n\n"
        "Botdan foydalanish uchun bir martalik qisqa anketani to'ldiring.\n\n"
        "Iltimos, <b>Ismingiz va Familiyangizni</b> kiriting (Masalan: Ali Valiyev):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegistrationStates.full_name)

@router.message(RegistrationStates.full_name)
async def process_full_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 60:
        await message.answer("⚠️ Iltimos, to'g'ri ism va familiya kiriting:")
        return

    await state.update_data(full_name=name)
    await message.answer("🎂 Yoshingizni kiriting (Masalan: 20):")
    await state.set_state(RegistrationStates.age)

@router.message(RegistrationStates.age)
async def process_age(message: Message, state: FSMContext):
    age_text = message.text.strip()
    if not age_text.isdigit() or not (12 <= int(age_text) <= 90):
        await message.answer("⚠️ Iltimos, yoshingizni raqamda to'g'ri kiriting (12 dan 90 gacha):")
        return

    await state.update_data(age=int(age_text))
    await message.answer("📍 Qaysi viloyat yoki shahardansiz? (Masalan: Toshkent):")
    await state.set_state(RegistrationStates.city)

@router.message(RegistrationStates.city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    if len(city) < 2 or len(city) > 40:
        await message.answer("⚠️ Iltimos, shahar yoki viloyatingizni to'g'ri kiriting:")
        return

    await state.update_data(city=city)
    await message.answer(
        "⚧ Jinsingizni tanlang:",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(RegistrationStates.gender)

@router.message(RegistrationStates.gender)
async def process_gender(message: Message, state: FSMContext):
    text = message.text
    if text == "👨 Yigitman":
        gender = "male"
    elif text == "👩 Qizman":
        gender = "female"
    else:
        await message.answer("⚠️ Iltimos, quyidagi tugmalardan birini tanlang:", reply_markup=get_gender_keyboard())
        return

    data = await state.get_data()
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""

    await db.create_user(
        user_id=user_id,
        first_name=first_name,
        username=username,
        full_name=data["full_name"],
        age=data["age"],
        city=data["city"],
        gender=gender
    )

    await state.clear()
    await message.answer(
        "🎉 <b>Anketangiz muvaffaqiyatli saqlandi!</b>\n\n"
        "Endi bemalol tanishuv va suhbatlarni boshlashingiz mumkin.",
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard(is_vip=False)
    )

# Profilni ko'rish
@router.message(F.text == "👤 Profilim")
async def show_profile(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("⚠️ Siz hali ro'yxatdan o'tmagansiz. Qaytadan /start bosing.")
        return

    gender_str = "👨 Yigit" if user.get("gender") == "male" else "👩 Qiz"
    is_vip = bool(user.get("is_vip"))
    
    if is_vip:
        vip_info = f"⭐ VIP Faol (Muddati: {user.get('vip_until')})"
    else:
        vip_info = "❌ Oddiy (VIP mavjud emas)"

    text = (
        f"👤 <b>Sizning profilingiz:</b>\n\n"
        f"📝 <b>Ism-familiya:</b> {user.get('full_name')}\n"
        f"🎂 <b>Yosh:</b> {user.get('age')}\n"
        f"📍 <b>Manzil:</b> {user.get('city')}\n"
        f"⚧ <b>Jins:</b> {gender_str}\n"
        f"💎 <b>Maqom:</b> {vip_info}\n"
    )
    await message.answer(text, parse_mode="HTML")

# Ma'lumotlarni tahrirlash
@router.message(F.text == "✏️ Ma'lumotlarni tahrirlash")
async def edit_profile_start(message: Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if user and user.get("partner_id"):
        await message.answer("⚠️ Suhbat vaqtida anketani o'zgartirib bo'lmaydi. Avval suhbatni to'xtating.")
        return

    await state.clear()
    await message.answer(
        "✏️ <b>Ma'lumotlarni yangilash</b>\n\n"
        "Yangi <b>Ism va Familiyangizni</b> kiriting:",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(RegistrationStates.full_name)
