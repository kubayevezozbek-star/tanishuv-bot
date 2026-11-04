from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError

import database as db
from keyboards import (
    get_main_menu_keyboard,
    get_search_keyboard,
    get_chat_keyboard,
    get_vip_filter_keyboard
)

router = Router()

async def connect_and_notify(bot: Bot, user1_id: int, user2_id: int):
    await db.connect_users(user1_id, user2_id)
    u1 = await db.get_user(user1_id)
    u2 = await db.get_user(user2_id)

    # User 1 ga xabar
    u1_vip = bool(u1.get("is_vip"))
    msg1 = "🎉 <b>Suhbatdosh topildi!</b>\n\nMarhamat, salom deb yozishingiz mumkin."
    if u1_vip and u2:
        g = "👨 Yigit" if u2.get("gender") == "male" else "👩 Qiz"
        msg1 += (
            f"\n\n🌟 <b>Suhbatdosh ma'lumotlari (VIP):</b>\n"
            f"👤 Ismi: {u2.get('full_name')}\n"
            f"🎂 Yoshi: {u2.get('age')}\n"
            f"📍 Shahar: {u2.get('city')}\n"
            f"⚧ Jinsi: {g}"
        )
    try:
        await bot.send_message(user1_id, msg1, parse_mode="HTML", reply_markup=get_chat_keyboard(u1_vip))
    except Exception:
        pass

    # User 2 ga xabar
    u2_vip = bool(u2.get("is_vip"))
    msg2 = "🎉 <b>Suhbatdosh topildi!</b>\n\nMarhamat, salom deb yozishingiz mumkin."
    if u2_vip and u1:
        g = "👨 Yigit" if u1.get("gender") == "male" else "👩 Qiz"
        msg2 += (
            f"\n\n🌟 <b>Suhbatdosh ma'lumotlari (VIP):</b>\n"
            f"👤 Ismi: {u1.get('full_name')}\n"
            f"🎂 Yoshi: {u1.get('age')}\n"
            f"📍 Shahar: {u1.get('city')}\n"
            f"⚧ Jinsi: {g}"
        )
    try:
        await bot.send_message(user2_id, msg2, parse_mode="HTML", reply_markup=get_chat_keyboard(u2_vip))
    except Exception:
        pass

async def execute_search(bot: Bot, user_id: int, search_gender: str = 'any'):
    user = await db.get_user(user_id)
    if not user:
        return

    # Sherik qidirish
    partner_id = await db.find_partner(user_id, user.get("gender", "male"), search_gender)

    if partner_id:
        # Sherik topildi!
        await connect_and_notify(bot, user_id, partner_id)
    else:
        # Navbatga qo'yish
        await db.set_searching(user_id, True, search_gender)
        await bot.send_message(
            user_id,
            "🔎 <b>Suhbatdosh qidirilmoqda...</b>\n\n"
            "Mos sherik topilganda bot sizni avtomatik bog'laydi. Iltimos kuting...",
            parse_mode="HTML",
            reply_markup=get_search_keyboard()
        )

# "💬 Suhbat boshlash" tugmasi
@router.message(F.text == "💬 Suhbat boshlash")
async def start_chat_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        await message.answer("⚠️ Iltimos, avval ro'yxatdan o'tish uchun /start bosing.")
        return

    if user.get("partner_id"):
        await message.answer("⚠️ Siz hozirda suhbatdasiz!", reply_markup=get_chat_keyboard(bool(user.get("is_vip"))))
        return

    if user.get("is_searching"):
        await message.answer("🔎 Suhbatdosh allaqachon qidirilmoqda...", reply_markup=get_search_keyboard())
        return

    is_vip = bool(user.get("is_vip"))
    if is_vip:
        # VIP foydalanuvchiga kim bilan tanishishni tanlash imkonini beramiz
        await message.answer(
            "⭐ <b>VIP Suhbat filtri:</b>\n\n"
            "Kim bilan muloqot qilishni xohlaysiz?",
            parse_mode="HTML",
            reply_markup=get_vip_filter_keyboard()
        )
    else:
        # Oddiy foydalanuvchi ixtiyoriy navbatga qo'yiladi
        await execute_search(bot, user_id, search_gender='any')

# VIP filtr tanlanganda
@router.callback_query(F.data.startswith("filter_"))
async def filter_chosen(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    user_id = callback.from_user.id
    filter_type = callback.data.split("_")[1] # 'any', 'female', 'male'
    
    await callback.message.delete()
    await execute_search(bot, user_id, search_gender=filter_type)

# "❌ Qidiruvni bekor qilish"
@router.message(F.text == "❌ Qidiruvni bekor qilish")
async def cancel_search_handler(message: Message):
    user_id = message.from_user.id
    await db.set_searching(user_id, False)
    user = await db.get_user(user_id)
    is_vip = bool(user.get("is_vip")) if user else False

    await message.answer(
        "❌ Qidiruv bekor qilindi.",
        reply_markup=get_main_menu_keyboard(is_vip)
    )

# "❌ Suhbatni to'xtatish"
@router.message(F.text == "❌ Suhbatni to'xtatish")
async def stop_chat_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    partner_id = await db.disconnect_user(user_id)

    user = await db.get_user(user_id)
    is_vip = bool(user.get("is_vip")) if user else False
    await message.answer("❌ Suhbat yakunlandi.", reply_markup=get_main_menu_keyboard(is_vip))

    if partner_id:
        partner = await db.get_user(partner_id)
        p_vip = bool(partner.get("is_vip")) if partner else False
        try:
            await bot.send_message(
                partner_id,
                "❌ Suhbatdosh muloqotni yakunladi.",
                reply_markup=get_main_menu_keyboard(p_vip)
            )
        except Exception:
            pass

# "➡️ Keyingisi"
@router.message(F.text == "➡️ Keyingisi")
async def next_chat_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    partner_id = await db.disconnect_user(user_id)

    if partner_id:
        partner = await db.get_user(partner_id)
        p_vip = bool(partner.get("is_vip")) if partner else False
        try:
            await bot.send_message(
                partner_id,
                "❌ Suhbatdosh yangi suhbatga o'tdi.",
                reply_markup=get_main_menu_keyboard(p_vip)
            )
        except Exception:
            pass

    # Yangi qidiruv boshlash
    user = await db.get_user(user_id)
    is_vip = bool(user.get("is_vip")) if user else False
    if is_vip:
        await message.answer(
            "⭐ <b>VIP Suhbat filtri:</b>\nKim bilan suhbatlashmoqchisiz?",
            parse_mode="HTML",
            reply_markup=get_vip_filter_keyboard()
        )
    else:
        await execute_search(bot, user_id, search_gender='any')

# "👤 Suhbatdosh anketasi" (VIP imtiyozi)
@router.message(F.text == "👤 Suhbatdosh anketasi")
async def partner_profile_handler(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user or not user.get("is_vip"):
        await message.answer("🔒 Suhbatdosh anketasini ko'rish faqat VIP foydalanuvchilar uchun!")
        return

    partner_id = user.get("partner_id")
    if not partner_id:
        await message.answer("⚠️ Hozirda suhbatda emassiz.")
        return

    partner = await db.get_user(partner_id)
    if not partner:
        await message.answer("⚠️ Suhbatdosh ma'lumotlari topilmadi.")
        return

    g = "👨 Yigit" if partner.get("gender") == "male" else "👩 Qiz"
    text = (
        f"🌟 <b>Suhbatdosh anketasi:</b>\n\n"
        f"👤 <b>Ismi:</b> {partner.get('full_name')}\n"
        f"🎂 <b>Yoshi:</b> {partner.get('age')}\n"
        f"📍 <b>Manzili:</b> {partner.get('city')}\n"
        f"⚧ <b>Jinsi:</b> {g}"
    )
    await message.answer(text, parse_mode="HTML")

# Xabarlarni bir-biriga yo'naltirish (Relay)
@router.message()
async def relay_messages_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        return

    partner_id = user.get("partner_id")
    if not partner_id:
        # Suhbatda bo'lmagan foydalanuvchi tasodifiy matn yozsa
        return

    # Sherikka xabarni yuborish
    try:
        if message.text:
            await bot.send_message(partner_id, message.text)
        elif message.photo:
            await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
        elif message.voice:
            await bot.send_voice(partner_id, message.voice.file_id, caption=message.caption)
        elif message.video_note:
            await bot.send_video_note(partner_id, message.video_note.file_id)
        elif message.sticker:
            await bot.send_sticker(partner_id, message.sticker.file_id)
        elif message.video:
            await bot.send_video(partner_id, message.video.file_id, caption=message.caption)
        elif message.audio:
            await bot.send_audio(partner_id, message.audio.file_id, caption=message.caption)
        elif message.animation:
            await bot.send_animation(partner_id, message.animation.file_id, caption=message.caption)
    except TelegramAPIError:
        # Agar suhbatdosh botni bloklagan yoki xabar yetkazib bo'lmasa
        await db.disconnect_user(user_id)
        is_vip = bool(user.get("is_vip"))
        await message.answer(
            "⚠️ Suhbatdosh bilan aloqa uzildi (botni bloklagan yoki chiqib ketgan).",
            reply_markup=get_main_menu_keyboard(is_vip)
        )
