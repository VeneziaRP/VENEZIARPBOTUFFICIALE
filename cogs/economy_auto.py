# cogs/economy_auto.py
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime, timezone

import discord
from discord.ext import commands

from utils.profili import get_profile, set_profile, money_fmt

CONFIG_FILE = Path("data/economy_config.json")
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {
    "salary_per_cycle": {},             # { "ROLE_ID": amount, ... }
    "payroll_log_channel_id": 1409251318153089044,  # canale log
    "delete_logs_after_seconds": 120    # auto-delete dopo 2 minuti
}

def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
    return DEFAULT_CONFIG.copy()

def pick_salary_for_member(member: discord.Member, salary_map: Dict[str, Any]) -> Tuple[int, int | None]:
    """Ritorna (stipendio, role_id) scegliendo la quota PIÙ ALTA tra i ruoli posseduti."""
    best_amount = 0
    best_role_id = None
    member_role_ids = {r.id for r in member.roles}
    for k, v in salary_map.items():
        try:
            rid = int(k)
            amount = int(v)
        except Exception:
            continue
        if rid in member_role_ids and amount > best_amount:
            best_amount = amount
            best_role_id = rid
    return best_amount, best_role_id

class EconomyAuto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._worker_task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._last_run_date: datetime.date | None = None

    async def cog_load(self):
        self._stop.clear()
        self._worker_task = asyncio.create_task(self._worker())

    async def cog_unload(self):
        self._stop.set()
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except Exception:
                pass

    # ------------- Worker loop (mensile) -------------
    async def _worker(self):
        await self.bot.wait_until_ready()
        while not self._stop.is_set():
            now = datetime.now(timezone.utc)
            # se è il primo del mese e non abbiamo ancora pagato oggi
            if now.day == 1 and (self._last_run_date != now.date()):
                try:
                    cfg = load_config()
                    await self._run_payroll(cfg)
                    self._last_run_date = now.date()
                except Exception:
                    pass
            try:
                # ricontrolla tra 1 ora
                await asyncio.wait_for(self._stop.wait(), timeout=3600)
            except asyncio.TimeoutError:
                continue

    # ------------- Core payroll -------------
    async def _run_payroll(self, cfg: Dict[str, Any]):
        if not self.bot.guilds:
            return

        salary_map: Dict[str, Any] = cfg.get("salary_per_cycle") or {}
        if not salary_map:
            return

        log_channel_id = int(cfg.get("payroll_log_channel_id") or 0)
        delete_after = int(cfg.get("delete_logs_after_seconds") or 120)

        for guild in self.bot.guilds:
            log_ch = guild.get_channel(log_channel_id) if log_channel_id else None

            paid_count = 0
            total_paid = 0

            for member in guild.members:
                if member.bot:
                    continue
                amount, role_id = pick_salary_for_member(member, salary_map)
                if amount <= 0 or role_id is None:
                    continue

                # Accredito su BANCA
                prof = get_profile(member.id)
                bank = dict(prof.get("bank") or {})
                try:
                    saldo_attuale = float(bank.get("saldo") or 0)
                except Exception:
                    saldo_attuale = 0.0
                nuovo_saldo = saldo_attuale + float(amount)
                bank["saldo"] = nuovo_saldo
                set_profile(member.id, bank=bank)

                paid_count += 1
                total_paid += int(amount)

            # Log (con auto-delete dopo 2 minuti)
            if isinstance(log_ch, discord.TextChannel):
                try:
                    msg = await log_ch.send(
                        f"💰 **Stipendi mensili eseguiti** in **{guild.name}** — "
                        f"pagati **{paid_count}** utenti • Totale {money_fmt(total_paid)}."
                    )
                    asyncio.create_task(self._autodelete(msg, delete_after))
                except Exception:
                    pass

    async def _autodelete(self, message: discord.Message, delay: int):
        try:
            await asyncio.sleep(max(5, delay))
            await message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

    # ------------- Comando manuale -------------
    @commands.hybrid_command(name="payroll_now", description="Esegui subito il ciclo stipendi (staff).")
    @commands.has_permissions(manage_guild=True)
    async def payroll_now(self, ctx: commands.Context):
        cfg = load_config()
        await self._run_payroll(cfg)
        await ctx.reply("✅ Payroll eseguito ora.", mention_author=False)

async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyAuto(bot))