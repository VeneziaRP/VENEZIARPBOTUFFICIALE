# views/cittadinanza_review_view.py
from __future__ import annotations
import discord
from discord.ext import commands
from datetime import datetime, date, timezone
from typing import Optional

from utils.iban import generate_iban  # ✅ genera IBAN

# DB unico cittadinanza
from views.cittadinanza_db import (
    is_pending,
    is_already_approved,
    mark_pending,
    unmark_pending,
    mark_approved,
    get_pending_data,
)

# Profili (merge "shallow" a livello top)
from utils.profili import set_profile

# === CONFIG ===
CITTADINO_ROLE_ID = 1408613574850379959
TURISTA_ROLE_ID   = 1408613574150197258


class CittadinanzaRejectModal(discord.ui.Modal, title="Rifiuta cittadinanza — motivazione"):
    def __init__(self, view_ref: "CittadinanzaReviewView"):
        super().__init__(timeout=None)
        self.view_ref = view_ref
        self.reason = discord.ui.TextInput(
            label="Motivazione (visibile al richiedente)",
            placeholder="Es. dati incompleti / regolamento non rispettato…",
            style=discord.TextStyle.paragraph,
            max_length=1000,
            required=True,
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await self.view_ref._finalize_decision(interaction, approved=False, reason=self.reason.value.strip())


class CittadinanzaReviewView(discord.ui.View):
    def __init__(self, bot: commands.Bot, applicant_id: int | None = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.applicant_id = applicant_id

    @discord.ui.button(label="Approva", style=discord.ButtonStyle.success, emoji="✅", custom_id="cittadinanza_review_approve")
    async def approve_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._finalize_decision(interaction, approved=True, reason=None)

    @discord.ui.button(label="Rifiuta", style=discord.ButtonStyle.danger, emoji="🛑", custom_id="cittadinanza_review_reject")
    async def reject_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        try:
            await interaction.response.send_modal(CittadinanzaRejectModal(self))
        except discord.InteractionResponded:
            pass

    # ---- helper ----
    def _safe_split_nome(self, dati: dict) -> tuple[str, str]:
        nome = (dati.get("nome_rp") or "").strip()
        cognome = (dati.get("cognome_rp") or "").strip()
        if not nome and not cognome:
            full = (dati.get("nome_pg") or "").strip()
            if full:
                parts = full.split()
                nome = parts[0]
                cognome = " ".join(parts[1:]) if len(parts) > 1 else ""
        return nome, cognome

    def _pick_birthdate(self, dati: dict) -> str:
        return (dati.get("data_nascita") or dati.get("data_pg") or "").strip().replace("/", "-")

    def _calc_eta(self, dp: str) -> str:
        try:
            dd, mm, yy = dp.split("-")
            born = date(int(yy), int(mm), int(dd))
            today = date.today()
            return str(today.year - born.year - ((today.month, today.day) < (born.month, born.day)))
        except Exception:
            return ""

    async def _finalize_decision(self, interaction: discord.Interaction, approved: bool, reason: Optional[str]):
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.InteractionResponded:
            pass

        if not isinstance(self.applicant_id, int) or self.applicant_id <= 0:
            return await interaction.followup.send("⚠️ View non inizializzata correttamente (manca applicant_id).", ephemeral=True)

        uid = self.applicant_id
        guild = interaction.guild
        member = guild.get_member(uid) if guild else None

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        dati_req = get_pending_data(uid)

        unmark_pending(uid)
        if approved:
            mark_approved(uid)

        try:
            if member:
                if approved:
                    # Ruoli
                    turista = guild.get_role(TURISTA_ROLE_ID)
                    if turista and turista in member.roles:
                        try: await member.remove_roles(turista, reason="Cittadinanza approvata")
                        except discord.Forbidden: pass
                    cittadino = guild.get_role(CITTADINO_ROLE_ID)
                    if cittadino and cittadino not in member.roles:
                        try: await member.add_roles(cittadino, reason="Cittadinanza approvata")
                        except discord.Forbidden: pass

                    # Profilo (costruisci payload + IBAN)
                    nome_rp, cognome_rp = self._safe_split_nome(dati_req)
                    dp = self._pick_birthdate(dati_req)
                    eta_rp = self._calc_eta(dp)

                    payload = {
                        "nome_rp": nome_rp,
                        "cognome_rp": cognome_rp,
                        "data_nascita": dp,
                        "eta_rp": eta_rp,
                        "genere": (dati_req.get("genere") or "").strip(),
                        "nazionalita": (dati_req.get("nazionalita") or "").strip(),
                        "citta_rp": "",
                        "lavoro_rp": (dati_req.get("lavoro_rp") or "").strip(),
                        "interessi": (dati_req.get("interessi") or "").strip(),
                        "competenze": (dati_req.get("competenze") or "").strip(),
                        "orari": (dati_req.get("orari") or "").strip(),
                        "licenze": "",
                        "bio": (dati_req.get("bio") or "").strip(),
                        "roblox": (dati_req.get("roblox") or "").strip(),
                        "social": (dati_req.get("roblox") or "").strip(),
                        "reputazione": 50,
                        "privacy_contatti": True,
                        "docs": {
                            "cittadinanza": {
                                "stato": True,
                                "numero": f"CIT-{uid % 10000:04d}",
                                "rilasciata_il": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                                "rilasciata_da": "Comune di Venezia",
                                "note": ""
                            },
                            "patenti": {
                                "A": {"stato": False, "numero": "", "rilasciata_il": "", "scadenza": ""},
                                "B": {"stato": False, "numero": "", "rilasciata_il": "", "scadenza": ""},
                                "C": {"stato": False, "numero": "", "rilasciata_il": "", "scadenza": ""},
                                "NAUTICA": {"stato": False, "numero": "", "rilasciata_il": "", "scadenza": ""}
                            }
                        },
                        # ✅ IBAN creato subito alla cittadinanza
                        "bank": {
                            "iban": generate_iban(member.id)
                        }
                    }

                    # Salva/merge su data/profili.json
                    set_profile(member.id, **payload)

                    dm = ("🏛️ **Cittadinanza approvata!**\n"
                          "Benvenuto a VeneziaRP, ora sei un **Cittadino ufficiale** 🎉")
                else:
                    dm = ("🏛️ **Cittadinanza rifiutata.**\n"
                          f"Motivazione: {reason or 'Non specificata.'}\n"
                          "Potrai riprovare in futuro.")

                try:
                    await member.send(dm)
                except discord.Forbidden:
                    pass
        except Exception:
            pass

        # Aggiorna l'embed staff
        try:
            msg = interaction.message
            if msg and msg.embeds:
                embed = msg.embeds[0]
                reviewer = interaction.user.mention
                if approved:
                    embed.color = discord.Color.green()
                    embed.add_field(name="Esito", value="✅ Approvato", inline=True)
                    embed.add_field(name="Approvato da", value=reviewer, inline=True)
                else:
                    embed.color = discord.Color.red()
                    embed.add_field(name="Esito", value="🛑 Rifiutato", inline=True)
                    embed.add_field(name="Rifiutato da", value=reviewer, inline=True)
                    if reason:
                        embed.add_field(name="Motivazione", value=reason[:1024], inline=False)
                await msg.edit(embed=embed, view=self)
        except Exception:
            pass

        # Feedback
        try:
            await interaction.followup.send(
                "Operazione registrata ✅" if approved else "Rifiuto registrato 🛑",
                ephemeral=True
            )
        except Exception:
            pass