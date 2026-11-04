import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                full_name TEXT,
                age INTEGER,
                city TEXT,
                gender TEXT,
                is_vip INTEGER DEFAULT 0,
                vip_until TEXT DEFAULT NULL,
                is_searching INTEGER DEFAULT 0,
                partner_id INTEGER DEFAULT NULL,
                search_gender TEXT DEFAULT 'any',
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan_key TEXT,
                file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        """)
        # Reset searching and partner states on bot restart
        await db.execute("UPDATE users SET is_searching = 0, partner_id = NULL")
        await db.commit()

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                user = dict(row)
                # VIP muddati tugaganini tekshirish
                if user.get("is_vip") and user.get("vip_until"):
                    try:
                        until_dt = datetime.fromisoformat(user["vip_until"])
                        if datetime.now() > until_dt:
                            await db.execute("UPDATE users SET is_vip = 0, vip_until = NULL WHERE user_id = ?", (user_id,))
                            await db.commit()
                            user["is_vip"] = 0
                            user["vip_until"] = None
                    except Exception:
                        pass
                return user
            return None

async def create_user(user_id: int, first_name: str, username: str, full_name: str, age: int, city: str, gender: str):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, first_name, username, full_name, age, city, gender, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name=excluded.first_name,
                username=excluded.username,
                full_name=excluded.full_name,
                age=excluded.age,
                city=excluded.city,
                gender=excluded.gender
        """, (user_id, first_name, username, full_name, age, city, gender, now))
        await db.commit()

async def set_searching(user_id: int, is_searching: bool, search_gender: str = 'any'):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_searching = ?, search_gender = ? WHERE user_id = ?",
            (1 if is_searching else 0, search_gender, user_id)
        )
        await db.commit()

async def find_partner(user_id: int, user_gender: str, search_gender: str) -> Optional[int]:
    """
    Qidiruv navbatidagi mos sherikni topadi.
    Moslik shartlari:
    1. is_searching = 1 va o'zi emas va partner_id IS NULL
    2. Men tanlagan jins (search_gender) uning jinsiga (gender) mos bo'lishi kerak.
    3. U tanlagan jins (partner_search_gender) mening jinsimga (user_gender) mos bo'lishi kerak.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = """
            SELECT user_id, gender, search_gender 
            FROM users 
            WHERE is_searching = 1 
              AND partner_id IS NULL 
              AND user_id != ?
            ORDER BY created_at ASC
        """
        async with db.execute(query, (user_id,)) as cursor:
            candidates = await cursor.fetchall()
            for cand in candidates:
                cand_id = cand["user_id"]
                cand_gender = cand["gender"]
                cand_search_gender = cand["search_gender"]

                # 1. Men u bilan gaplashmoqchimanmi?
                match_for_me = (search_gender == 'any' or search_gender == cand_gender)

                # 2. U men bilan gaplashmoqchimanmi?
                match_for_cand = (cand_search_gender == 'any' or cand_search_gender == user_gender)

                if match_for_me and match_for_cand:
                    return cand_id
    return None

async def connect_users(user1_id: int, user2_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_searching = 0, partner_id = ? WHERE user_id = ?",
            (user2_id, user1_id)
        )
        await db.execute(
            "UPDATE users SET is_searching = 0, partner_id = ? WHERE user_id = ?",
            (user1_id, user2_id)
        )
        await db.commit()

async def disconnect_user(user_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT partner_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or not row["partner_id"]:
                await db.execute("UPDATE users SET is_searching = 0, partner_id = NULL WHERE user_id = ?", (user_id,))
                await db.commit()
                return None
            
            partner_id = row["partner_id"]
            await db.execute("UPDATE users SET is_searching = 0, partner_id = NULL WHERE user_id = ?", (user_id,))
            await db.execute("UPDATE users SET is_searching = 0, partner_id = NULL WHERE user_id = ?", (partner_id,))
            await db.commit()
            return partner_id

async def create_receipt(user_id: int, plan_key: str, file_id: str) -> int:
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO receipts (user_id, plan_key, file_id, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, plan_key, file_id, now))
        await db.commit()
        return cursor.lastrowid

async def get_receipt(receipt_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def approve_receipt(receipt_id: int, days: int) -> Optional[Tuple[int, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,)) as cursor:
            receipt = await cursor.fetchone()
            if not receipt or receipt["status"] != "pending":
                return None

        user_id = receipt["user_id"]
        # Mavjud VIP muddati bo'lsa shunga qo'shish, bo'lmasa hozirdan
        async with db.execute("SELECT vip_until FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_row = await cursor.fetchone()
            base_time = datetime.now()
            if user_row and user_row["vip_until"]:
                try:
                    curr_until = datetime.fromisoformat(user_row["vip_until"])
                    if curr_until > base_time:
                        base_time = curr_until
                except Exception:
                    pass

        new_vip_until = (base_time + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

        await db.execute("UPDATE receipts SET status = 'approved' WHERE id = ?", (receipt_id,))
        await db.execute("UPDATE users SET is_vip = 1, vip_until = ? WHERE user_id = ?", (new_vip_until, user_id))
        await db.commit()
        return user_id, new_vip_until

async def reject_receipt(receipt_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,)) as cursor:
            receipt = await cursor.fetchone()
            if not receipt or receipt["status"] != "pending":
                return None

        user_id = receipt["user_id"]
        await db.execute("UPDATE receipts SET status = 'rejected' WHERE id = ?", (receipt_id,))
        await db.commit()
        return user_id

async def get_stats() -> Dict[str, int]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT COUNT(*) as count FROM users") as c:
            total = (await c.fetchone())["count"]
        async with db.execute("SELECT COUNT(*) as count FROM users WHERE gender = 'male'") as c:
            males = (await c.fetchone())["count"]
        async with db.execute("SELECT COUNT(*) as count FROM users WHERE gender = 'female'") as c:
            females = (await c.fetchone())["count"]
        async with db.execute("SELECT COUNT(*) as count FROM users WHERE is_vip = 1") as c:
            vip_count = (await c.fetchone())["count"]
        async with db.execute("SELECT COUNT(*) as count FROM users WHERE partner_id IS NOT NULL") as c:
            active_chats = (await c.fetchone())["count"] // 2
        async with db.execute("SELECT COUNT(*) as count FROM users WHERE is_searching = 1") as c:
            searching_count = (await c.fetchone())["count"]

        return {
            "total": total,
            "males": males,
            "females": females,
            "vip_count": vip_count,
            "active_chats": active_chats,
            "searching_count": searching_count
        }
