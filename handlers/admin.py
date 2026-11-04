from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

import database as db
from config import ADMIN_ID, TARIFS
from keyboards import get_main_menu_keyboard

router = Router()

# Admin boshqaruv paneli
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        # Oddiy foydalanuvchilarga hech narsa ko'rsatmaymiz
        return

    stats = await db.get_stats()

    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        "📊 <b>Bot statistikasi:</b>\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total']}</b> ta\n"
        f"👨 Yigitlar: <b>{stats['males']}</b> ta\n"
        f"👩 Qizlar: <b>{stats['females']}</b> ta\n"
        f"⭐ VIP a'zolar: <b>{stats['vip_count']}</b> ta\n"
        f"💬 Hozir suhbatlashayotgan juftliklar: <b>{stats['active_chats']}</b> ta\n"
        f"⏳ Qidiruv navbatidagilar: <b>{stats['searching_count']}</b> ta\n"
    )
    await message.answer(text, parse_mode="HTML")

# To'lovni tasdiqlash
@router.callback_query(F.data.startswith("admin_approve_"))
async def approve_payment_handler(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    receipt_id = int(callback.data.split("_")[2])
    receipt = await db.get_receipt(receipt_id)
    if not receipt:
        await callback.answer("Chek topilmadi!", show_alert=True)
        return

    plan_key = receipt.get("plan_key", "3_days")
    days = TARIFS.get(plan_key, TARIFS["3_days"])["days"]

    res = await db.approve_receipt(receipt_id, days)
    if not res:
        await callback.answer("Bu chek allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    user_id, vip_until = res
    await callback.answer("✅ To'lov tasdiqlandi!")
    
    # Admin xabarini yangilash
    new_caption = (
        f"{callback.message.caption or ''}\n\n"
        f"✅ <b>TASDIQLANDI!</b>\n"
        f"Foydalanuvchiga VIP berildi.\nMuddati: <b>{vip_until}</b>"
    )
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchiga xabar yuborish
    try:
        user_msg = (
            "🎉 <b>Tabriklaymiz! Sizning to'lovingiz tasdiqlandi!</b>\n\n"
            f"⭐ <b>VIP maqomingiz faollashtirildi!</b>\n"
            f"⏳ Amal qilish muddati: <b>{vip_until}</b> gacha.\n\n"
            "Endi siz:\n"
            "• Suhbat boshlashda qizlar yoki yigitlarni alohida tanlashingiz;\n"
            "• Suhbatdosh anketasini ko'rishingiz mumkin!"
        )
        await bot.send_message(user_id, user_msg, parse_mode="HTML", reply_markup=get_main_menu_keyboard(is_vip=True))
    except Exception as e:
        print(f"Foydalanuvchiga VIP xabari yetmadi: {e}")

# To'lovni rad etish
@router.callback_query(F.data.startswith("admin_reject_"))
async def reject_payment_handler(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    receipt_id = int(callback.data.split("_")[2])
    user_id = await db.reject_receipt(receipt_id)
    if not user_id:
        await callback.answer("Bu chek allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await callback.answer("❌ To'lov rad etildi.")
    new_caption = (
        f"{callback.message.caption or ''}\n\n"
        f"❌ <b>RAD ETILDI!</b>"
    )
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchiga rad javobini yuborish
    try:
        reject_msg = (
            "⚠️ <b>Afsuski, yuborgan to'lov chekingiz tasdiqlanmadi.</b>\n\n"
            "Agar xatolik yuz bergan bo'lsa, iltimos to'g'ri to'lov chekini qaytadan yuboring."
        )
        await bot.send_message(user_id, reject_msg, parse_mode="HTML")
    except Exception:
        pass
