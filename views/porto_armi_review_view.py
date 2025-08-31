# views/porto_armi_review_view.py
import discord
from discord.ext import commands
from datetime import datetime, timezone

from .porto_armi_db import unmark_pending, mark_approved, get_pending_data

# aggiorniamo anche il profilo utente con il documento
try:
    from utils.profile_store import upsert_profile  # se non c'è ancora, nessun problema
except Exception:
    upsert_profile = None

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def _gen_doc_number(user_id: int, tipo: str) -> str:
    # es. PA-P3-8247-2508
    tail = str(user_id)[-4:]
    ym = datetime.now(timezone.utc).strftime("%y%m")
    return f"PA-{tipo}-{tail}-{ym}"

class PortoArmiRejectModal(discord.ui.Modal, title="🛑 Rifiuta Porto d’Armi — Motivazione"):
    def __init__(self, view_ref: "PortoArmiReviewView"):
        super().__init__(timeout=None)
        self.view_ref = view_ref
        self.reason = discord.ui.TextInput(
            label="Motivazione (visibile all’utente)",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await self.view_ref._finalize(interaction, approved=False, reason=self.reason.value.strip())

class PortoArmiReviewView(discord.ui.View):
    """Bottoni persistenti per approvare/rifiutare una richiesta di Porto d’Armi."""
    def __init__(self, bot: commands.Bot, applicant_id: int | None = None, tipo: str | None = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.applicant_id = applicant_id
        self.tipo = (tipo or "").upper()  # P1/P2/P3/P4

    @discord.ui.button(label="Approva ✅", style=discord.ButtonStyle.success, emoji="🟢",
                       custom_id="porto_armi_review_approve")
    async def approve(self, interaction: discord.Interaction, _: discord.ui.Button):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        await self._finalize(interaction, approved=True, reason=None)

    @discord.ui.button(label="Rifiuta ❌", style=discord.ButtonStyle.danger, emoji="🔴",
                       custom_id="porto_armi_review_reject")
    async def reject(self, interaction: discord.Interaction, _: discord.ui.Button):
        try:
            await interaction.response.send_modal(PortoArmiRejectModal(self))
        except discord.InteractionResponded:
            await interaction.followup.send("Riapri il rifiuto cliccando di nuovo.", ephemeral=True)

    async def _finalize(self, interaction: discord.Interaction, approved: bool, reason: str | None):
        uid = self.applicant_id
        guild = interaction.guild
        member = guild.get_member(uid) if guild else None

        # prendo i dati PRIMA di toccare il DB
        pending = {}
        try:
            pending = get_pending_data(uid) or {}
        except Exception:
            pending = {}

        # stato DB
        if uid:
            unmark_pending(uid)
            if approved:
                mark_approved(uid, self.tipo)

        # disabilita bottoni
        for c in self.children:
            if isinstance(c, discord.ui.Button):
                c.disabled = True

        # aggiorna embed staff
        try:
            msg = interaction.message
            if msg and msg.embeds:
                emb = msg.embeds[0]
                staff = interaction.user.mention
                if approved:
                    emb.color = discord.Color.green()
                    emb.add_field(name="📜 Esito", value=f"✅ Approvata ({self.tipo})", inline=True)
                    emb.add_field(name="👮‍♂️ Approvata da", value=staff, inline=True)
                else:
                    emb.color = discord.Color.red()
                    emb.add_field(name="📜 Esito", value=f"❌ Rifiutata ({self.tipo})", inline=True)
                    emb.add_field(name="🛡️ Rifiutata da", value=staff, inline=True)
                    if reason:
                        emb.add_field(name="📝 Motivazione", value=f"```{reason[:1024]}```", inline=False)
                await msg.edit(embed=emb, view=self)
        except Exception:
            pass

        # aggiorna profilo (se approvata)
        if approved and member and upsert_profile:
            try:
                numero = _gen_doc_number(member.id, self.tipo or "P?")
                doc = {
                    "porto_armi": {
                        "stato": True,
                        "tipologia": self.tipo,
                        "numero": numero,
                        "rilasciata_il": _now_iso(),
                        "note": "",
                        "motivazione": pending.get("motivazione", ""),
                        "arma_principale": pending.get("arma_principale", ""),
                        "esperienza": pending.get("esperienza", ""),
                    }
                }
                upsert_profile(member.id, {"docs": doc})
            except Exception:
                pass

        # DM utente
        if member:
            try:
                if approved:
                    await member.send(
                        f"🔫 **PORTO D’ARMI APPROVATO!**\n"
                        f"🎯 Tipologia: **{self.tipo}**\n"
                        f"🧠 Motivazione: {pending.get('motivazione','—')}\n"
                        f"👮‍♂️ Approvato da: **{interaction.user.display_name}**\n\n"
                        "✅ Ora puoi detenere/portare armi come da regole di **VeneziaRP**.\n"
                        "⚠️ Uso scorretto ⇒ ritiro immediato."
                    )
                else:
                    await member.send(
                        f"🚫 **PORTO D’ARMI RIFIUTATO**\n"
                        f"🎯 Tipologia: **{self.tipo}**\n"
                        f"🛡️ Rifiutato da: **{interaction.user.display_name}**\n"
                        f"📝 Motivazione: {reason or 'Non specificata'}\n\n"
                        "Potrai ripresentare la domanda quando rispetterai i requisiti."
                    )
            except discord.Forbidden:
                pass

        # Ack staff
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("✅ Operazione registrata.", ephemeral=True)
            else:
                await interaction.followup.send("✅ Operazione registrata.", ephemeral=True)
        except Exception:
            pass