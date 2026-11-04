from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import database as db
from config import ADMIN_ID, CARD_NUMBER, CARD_HOLDER, TARIFS
from keyboards import (
    get_tarifs_keyboard,
    get_cancel_payment_keyboard,
    get_admin_receipt_keyboard,
    get_main_menu_keyboard
)

router = Router()

class VipStates(StatesGroup):
    waiting_for_receipt = State()

# VIP menyusini ko'rsatish
@router.message(F.text.startswith("⭐ VIP Obuna"))
async def show_vip_menu(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    is_vip = bool(user.get("is_vip")) if user else False
    
    status_text = ""
    if is_vip:
        status_text = f"🌟 <b>Sizda hozirda VIP obuna faol!</b>\nMuddati: <code>{user.get('vip_until')}</code>\n\n"

    caption = (
        f"{status_text}"
        "👑 <b>VIP Obunachi imtiyozlari:</b>\n\n"
        "1️⃣ <b>Jins bo'yicha saralash:</b> Faqat qizlar yoki faqat yigitlar bilan suhbat qurish imkoni.\n"
        "2️⃣ <b>Sherik anketasini ko'rish:</b> Suhbatdoshning ismi, yoshi va qayerdanligini bila olasiz.\n"
        "3️⃣ <b>Ustuvor ulanish:</b> Navbat kutmasdan tezkor suhbatdosh topish.\n\n"
        "💰 <b>Quyidagi tariflardan birini tanlang:</b>"
    )
    await message.answer(caption, parse_mode="HTML", reply_markup=get_tarifs_keyboard())

# Tarif tanlanganda to'lov ma'lumotlarini berish
@router.callback_query(F.data.startswith("buy_"))
async def process_buy_tariff(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    plan_key = callback.data.replace("buy_", "")
    tarif = TARIFS.get(plan_key)
    if not tarif:
        return

    await state.set_state(VipStates.waiting_for_receipt)
    await state.update_data(plan_key=plan_key)

    text = (
        f"💳 <b>{tarif['name']} uchun to'lov</b>\n\n"
        f"💰 Narxi: <b>{tarif['price']} so'm</b>\n"
        f"💳 Karta raqam: <code>{CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: <b>{CARD_HOLDER}</b>\n\n"
        "📌 <i>To'lovni amalga oshirgach, to'lov cheki skrinshotini (rasmini) shu yerga yuboring:</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_cancel_payment_keyboard())

# To'lovni bekor qilish
@router.callback_query(F.data == "cancel_payment")
async def cancel_payment_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("To'lov bekor qilindi.")
    await callback.message.edit_text("❌ To'lov bekor qilindi.")

# Chek rasmini qabul qilish
@router.message(VipStates.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    plan_key = data.get("plan_key", "3_days")
    tarif = TARIFS.get(plan_key, TARIFS["3_days"])

    file_id = message.photo[-1].file_id
    user_id = message.from_user.id
    user = await db.get_user(user_id)

    # Chekni bazaga saqlash
    receipt_id = await db.create_receipt(user_id, plan_key, file_id)
    await state.clear()

    # Foydalanuvchiga xabar
    await message.answer(
        "✅ <b>To'lov chekingiz qabul qilindi!</b>\n\n"
        "Chek adminga yuborildi. Administrator tekshirib tasdiqlaganidan so'ng, "
        "VIP maqomingiz avtomatik ishga tushadi.",
        parse_mode="HTML"
    )

    # Adminga yuborish
    admin_caption = (
        f"🔔 <b>Yangi VIP to'lov cheki! (№{receipt_id})</b>\n\n"
        f"👤 <b>Ism:</b> {user.get('full_name') if user else message.from_user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> @{message.from_user.username or 'yoq'}\n"
        f"📦 <b>Tanlangan tarif:</b> {tarif['name']}\n"
        f"💰 <b>Kutilayotgan summa:</b> {tarif['price']} so'm\n\n"
        "Chekni tekshirib, quyidagi tugmalar orqali tasdiqlang yoki rad eting:"
    )

    try:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=admin_caption,
            parse_mode="HTML",
            reply_markup=get_admin_receipt_keyboard(receipt_id)
        )
    except Exception as e:
        print(f"Adminga chek yuborishda xatolik: {e}")

@router.message(VipStates.waiting_for_receipt)
async def wrong_receipt_format(message: Message):
    await message.answer(
        "⚠️ Iltimos, to'lov chekini <b>rasm (skrinshot)</b> ko'rinishida yuboring yoki bekor qilish tugmasini bosing.",
        parse_mode="HTML",
        reply_markup=get_cancel_payment_keyboard()
    )
