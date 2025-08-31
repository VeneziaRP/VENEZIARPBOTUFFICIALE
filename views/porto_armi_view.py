# views/porto_armi_view.py
import discord
from discord.ext import commands
from .porto_armi_review_view import PortoArmiReviewView
from .porto_armi_db import is_pending, is_already_approved, mark_pending

STAFF_PORTO_ARMI_CHANNEL_ID = 1408591152323625100  # <- canale logs staff

# --- Modale ---
class PortoArmiModal(discord.ui.Modal, title="🔫 Richiesta Porto d’Armi"):
    def __init__(self, author: discord.Member, tipologia: str):
        super().__init__(timeout=None)
        self.author = author
        self.tipologia = tipologia

        self.motivazione = discord.ui.TextInput(
            label="🧠 Motivazione RP (obbligatoria)",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000,
            placeholder="Es. Sicurezza personale, lavoro di guardia giurata..."
        )
        self.arma = discord.ui.TextInput(
            label="🔫 Arma principale (facoltativa)",
            required=False,
            max_length=60,
            placeholder="Es. Pistola 9mm, Fucile da caccia..."
        )
        self.esperienza = discord.ui.TextInput(
            label="🎯 Esperienza/Addestramento (facoltativo)",
            required=False,
            max_length=120,
            placeholder="Es. Tiro a segno sportivo, corso di addestramento..."
        )

        self.add_item(self.motivazione)
        self.add_item(self.arma)
        self.add_item(self.esperienza)

    async def on_submit(self, interaction: discord.Interaction):
        uid = self.author.id
        if is_already_approved(uid):
            return await interaction.response.send_message(
                "ℹ️ Hai già un **porto d’armi approvato**.",
                ephemeral=True
            )

        # Embed per lo staff
        e = discord.Embed(
            title="📝 Nuova Richiesta Porto d’Armi",
            color=discord.Color.orange()
        )
        e.add_field(name="👤 Utente", value=f"{self.author.mention} (`{self.author.id}`)", inline=False)
        e.add_field(name="📜 Tipologia", value=f"**{self.tipologia}**", inline=True)
        e.add_field(name="🧠 Motivazione", value=self.motivazione.value, inline=False)
        if self.arma.value:
            e.add_field(name="🔫 Arma principale", value=self.arma.value, inline=True)
        if self.esperienza.value:
            e.add_field(name="🎯 Esperienza", value=self.esperienza.value, inline=True)

        if self.author.avatar:
            e.set_thumbnail(url=self.author.avatar.url)
        if interaction.guild and interaction.guild.icon:
            e.set_footer(text="VeneziaRP | Porto d’Armi", icon_url=interaction.guild.icon.url)
        else:
            e.set_footer(text="VeneziaRP | Porto d’Armi")

        ch = interaction.client.get_channel(STAFF_PORTO_ARMI_CHANNEL_ID)
        if ch is None:
            return await interaction.response.send_message(
                "❌ Canale staff non configurato.",
                ephemeral=True
            )

        # Salva in PENDING con tutti i dati utili alla review
        mark_pending(uid, {
            "tipo": self.tipologia,
            "motivazione": self.motivazione.value.strip(),
            "arma_principale": (self.arma.value or "").strip(),
            "esperienza": (self.esperienza.value or "").strip(),
        })

        view = PortoArmiReviewView(interaction.client, applicant_id=uid, tipo=self.tipologia)
        await ch.send(embed=e, view=view)

        await interaction.response.send_message(
            "✅ **Richiesta inviata!** Lo staff la valuterà entro 24–48 ore.",
            ephemeral=True
        )

# --- Select tipologia ---
class _SelectTipo(discord.ui.Select):
    def __init__(self, author: discord.Member):
        self.author = author
        super().__init__(
            placeholder="📜 Scegli la tipologia di porto d’armi",
            options=[
                discord.SelectOption(label="P1 — 🏅 Sportivo", value="P1", description="Uso sportivo / poligono"),
                discord.SelectOption(label="P2 — 🦌 Caccia", value="P2", description="Attività venatoria"),
                discord.SelectOption(label="P3 — 🛡️ Difesa Personale", value="P3", description="Tutela della persona"),
                discord.SelectOption(label="P4 — 💼 Lavoro", value="P4", description="Guardia giurata, sicurezza…"),
            ],
            min_values=1,
            max_values=1,
            custom_id="porto_armi_tipo"
        )

    async def callback(self, interaction: discord.Interaction):
        uid = self.author.id
        if is_already_approved(uid):
            return await interaction.response.send_message(
                "ℹ️ Hai già un **porto d’armi approvato**.",
                ephemeral=True
            )
        if is_pending(uid):
            return await interaction.response.send_message(
                "⏳ Hai già una **richiesta in valutazione**.",
                ephemeral=True
            )
        await interaction.response.send_modal(PortoArmiModal(self.author, self.values[0]))

class _SelectTipoView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=180)
        self.add_item(_SelectTipo(author))

# --- View pubblica ---
class PortoArmiView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="🔫 Richiedi Porto d’Armi",
        style=discord.ButtonStyle.success,
        emoji="📜",
        custom_id="porto_armi_start"
    )
    async def start(self, interaction: discord.Interaction, _: discord.ui.Button):
        uid = interaction.user.id
        if is_already_approved(uid):
            return await interaction.response.send_message(
                "ℹ️ Hai già un **porto d’armi approvato**.",
                ephemeral=True
            )
        if is_pending(uid):
            return await interaction.response.send_message(
                "⏳ Hai già una **richiesta in valutazione**.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "📌 **Seleziona la tipologia** di porto d’armi che vuoi richiedere:",
            view=_SelectTipoView(interaction.user),
            ephemeral=True
        )