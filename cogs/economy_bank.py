# cogs/economy_bank.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

import discord
from discord.ext import commands
from discord import app_commands

from utils.profili import get_profile, set_profile, money_fmt

CONFIG_FILE = Path("data/economy_config.json")
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_CFG = {
    # canale dove loggare le operazioni utente (facoltativo)
    "bank_log_channel_id": 0,

    # limiti/parametri
    "min_operation_amount": 10,       # minimo 10€
    "max_operation_amount": 1_000_000,  # tetto massimo
}

def _load_cfg() -> Dict[str, Any]:
    cfg = DEFAULT_CFG.copy()
    if CONFIG_FILE.exists():
        try:
            user_cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            # importa solo chiavi conosciute, senza distruggere altre configurazioni già presenti
            for k in DEFAULT_CFG.keys():
                if k in user_cfg:
                    cfg[k] = user_cfg[k]
            # lascia intatti eventuali altre chiavi dell'economia (stipendi, ecc.)
        except Exception:
            pass
    else:
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg

def _round2(x: float) -> float:
    return float(f"{x:.2f}")

class EconomyBank(commands.Cog):
    """Deposita e preleva dal conto bancario personale."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ========= Slash: /deposita =========
    @app_commands.command(name="deposita", description="Deposita una somma dal portafoglio al conto bancario.")
    @app_commands.describe(importo="Importo da depositare in banca (es. 250.50).")
    async def deposita(self, itx: discord.Interaction, importo: float):
        await itx.response.defer(ephemeral=True)

        cfg = _load_cfg()
        min_amt = float(cfg.get("min_operation_amount") or 1)
        max_amt = float(cfg.get("max_operation_amount") or 1_000_000)

        # validazione importo
        if importo is None or importo <= 0:
            return await itx.followup.send("❌ Inserisci un importo positivo.", ephemeral=True)
        if importo < min_amt:
            return await itx.followup.send(f"❌ L'importo minimo è {money_fmt(min_amt)}.", ephemeral=True)
        if importo > max_amt:
            return await itx.followup.send(f"❌ L'importo massimo per operazione è {money_fmt(max_amt)}.", ephemeral=True)

        prof = get_profile(itx.user.id)
        wallet = float(prof.get("wallet") or 0)
        bank   = dict(prof.get("bank") or {})
        saldo  = float(bank.get("saldo") or 0)

        if wallet < importo:
            return await itx.followup.send(
                f"❌ Fondi insufficienti nel portafoglio. Disponibile: {money_fmt(wallet)}",
                ephemeral=True
            )

        # esegui movimento
        wallet -= importo
        saldo  += importo

        set_profile(itx.user.id, wallet=_round2(wallet), bank={"saldo": _round2(saldo)})

        # feedback all'utente
        msg = (
            f"✅ Deposito effettuato: **{money_fmt(importo)}**\n"
            f"💳 Portafoglio: {money_fmt(wallet)}\n"
            f"🏦 Conto: {money_fmt(saldo)}"
        )
        await itx.followup.send(msg, ephemeral=True)

        # log opzionale
        log_ch_id = int(cfg.get("bank_log_channel_id") or 0)
        if log_ch_id and itx.guild:
            ch = itx.guild.get_channel(log_ch_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    await ch.send(
                        f"📥 **Deposito** — {itx.user.mention} ha depositato {money_fmt(importo)}.\n"
                        f"Saldo conto: {money_fmt(saldo)}"
                    )
                except Exception:
                    pass

    # ========= Slash: /preleva =========
    @app_commands.command(name="preleva", description="Preleva una somma dal conto bancario al portafoglio.")
    @app_commands.describe(importo="Importo da prelevare dal conto (es. 150).")
    async def preleva(self, itx: discord.Interaction, importo: float):
        await itx.response.defer(ephemeral=True)

        cfg = _load_cfg()
        min_amt = float(cfg.get("min_operation_amount") or 1)
        max_amt = float(cfg.get("max_operation_amount") or 1_000_000)

        if importo is None or importo <= 0:
            return await itx.followup.send("❌ Inserisci un importo positivo.", ephemeral=True)
        if importo < min_amt:
            return await itx.followup.send(f"❌ L'importo minimo è {money_fmt(min_amt)}.", ephemeral=True)
        if importo > max_amt:
            return await itx.followup.send(f"❌ L'importo massimo per operazione è {money_fmt(max_amt)}.", ephemeral=True)

        prof = get_profile(itx.user.id)
        wallet = float(prof.get("wallet") or 0)
        bank   = dict(prof.get("bank") or {})
        saldo  = float(bank.get("saldo") or 0)

        if saldo < importo:
            return await itx.followup.send(
                f"❌ Fondi insufficienti sul conto. Disponibile: {money_fmt(saldo)}",
                ephemeral=True
            )

        # esegui movimento
        saldo  -= importo
        wallet += importo

        set_profile(itx.user.id, wallet=_round2(wallet), bank={"saldo": _round2(saldo)})

        msg = (
            f"✅ Prelievo effettuato: **{money_fmt(importo)}**\n"
            f"💳 Portafoglio: {money_fmt(wallet)}\n"
            f"🏦 Conto: {money_fmt(saldo)}"
        )
        await itx.followup.send(msg, ephemeral=True)

        # log opzionale
        log_ch_id = int(cfg.get("bank_log_channel_id") or 0)
        if log_ch_id and itx.guild:
            ch = itx.guild.get_channel(log_ch_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    await ch.send(
                        f"📤 **Prelievo** — {itx.user.mention} ha prelevato {money_fmt(importo)}.\n"
                        f"Saldo conto: {money_fmt(saldo)}"
                    )
                except Exception:
                    pass

async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyBank(bot))