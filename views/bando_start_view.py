import re
import discord
from discord.ext import commands
from .bando_flow import CandidaturaIntroModal

# (opzionale) categoria dove creare i canali candidatura
CANDIDATURE_CATEGORY_ID: int | None = 1408583038149066752

def _slugify(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return base or "utente"

class ChannelFormView(discord.ui.View):
    """Dentro al canale candidatura: bottone che apre la modale iniziale."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✍️ Compila il modulo", style=discord.ButtonStyle.primary, custom_id="bando:open_form")
    async def open_form(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(CandidaturaIntroModal(interaction.user))

class BandoStartView(discord.ui.View):
    """Nel pannello pubblico: crea il canale candidatura + messaggio guida."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Invia candidatura", emoji="📨", style=discord.ButtonStyle.success, custom_id="bando:start")
    async def start_bando(self, interaction: discord.Interaction, _: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user
        if guild is None:
            return await interaction.response.send_message("Errore: guild non trovata.", ephemeral=True)

        parent = None
        if CANDIDATURE_CATEGORY_ID:
            parent = guild.get_channel(CANDIDATURE_CATEGORY_ID)
        if parent is None:
            parent = interaction.channel.category

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }

        safe = _slugify(user.display_name)
        name = f"candidatura-{safe}"
        channel = await guild.create_text_channel(name=name[:90], category=parent, overwrites=overwrites)

        emb = discord.Embed(
            title="📋 Candidatura Staff",
            description=(
                "Benvenuto nel **tuo canale candidatura**!\n\n"
                "🔹 Qui potrai completare la tua **domanda per entrare nello Staff di VeneziaRP**.\n"
                "🔒 Il canale è **privato**: visibile solo a te e allo staff.\n\n"
                "➡️ Quando sei pronto, clicca **Compila il modulo** qui sotto per iniziare.\n"
                "⏳ Puoi prenderti il tempo necessario; se chiudi, potrai riprendere da qui."
            ),
            color=discord.Color.gold(),
        )
        if user.display_avatar:
            emb.set_thumbnail(url=user.display_avatar.url)
        emb.set_footer(text="VeneziaRP | Sistema candidature")

        await channel.send(embed=emb, view=ChannelFormView())
        await interaction.response.send_message(
            f"✅ Canale creato: {channel.mention}\nAprilo e clicca **Compila il modulo**.", ephemeral=True
        )

def register_start_views(bot: commands.Bot | discord.Client):
    bot.add_view(BandoStartView())
    bot.add_view(ChannelFormView())