# modals/prenotazione_modale.py
from __future__ import annotations
import discord
from discord import ui

# 🔧 CONFIG: dove inviare le richieste in base al tipo
ORALE_CHANNEL_ID   = 1408599684041412720   # <-- canale richieste ORALE
PRATICO_CHANNEL_ID = 1408599634993221782   # <-- canale richieste PRATICO
PING_ROLE_ID: int | None = None            # opzionale: ruolo da pingare (es. @Staff Colloqui)

def _target_channel_id(tipo: str) -> int:
    return ORALE_CHANNEL_ID if tipo.lower() == "orale" else PRATICO_CHANNEL_ID

class PrenotazioneModal(discord.ui.Modal, title="Prenota colloquio"):
    def __init__(self, *, tipo: str):
        super().__init__(timeout=None)
        self.tipo = "orale" if tipo.lower() == "orale" else "pratico"

        self.preferenza = ui.TextInput(
            label="Giorno e orario preferiti",
            placeholder="Es. Martedì 21:30 oppure 21-22",
            max_length=100,
            required=True,
        )
        self.alternative = ui.TextInput(
            label="Alternative (opzionale)",
            placeholder="Altri giorni/orari possibili",
            max_length=100,
            required=False,
        )
        self.note = ui.TextInput(
            label="Note per lo staff (opz.)",
            style=discord.TextStyle.paragraph,
            placeholder="Es. fuso orario, vincoli, altre info utili",
            max_length=400,
            required=False,
        )

        self.add_item(self.preferenza)
        self.add_item(self.alternative)
        self.add_item(self.note)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("⚠️ Guild non trovata.", ephemeral=True)

        target_id = _target_channel_id(self.tipo)
        target = guild.get_channel(target_id)

        # Embed riassunto
        e = discord.Embed(
            title=f"🗓️ Nuova prenotazione {self.tipo.upper()}",
            description=(
                f"Richiedente: {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"Tipo: **{self.tipo.upper()}**"
            ),
            color=discord.Color.blurple() if self.tipo == "orale" else discord.Color.green(),
        )
        e.add_field(name="Preferenza",  value=self.preferenza.value.strip(), inline=False)
        if self.alternative.value:
            e.add_field(name="Alternative", value=self.alternative.value.strip(), inline=False)
        if self.note.value:
            e.add_field(name="Note", value=self.note.value.strip(), inline=False)

        if interaction.user.display_avatar:
            e.set_thumbnail(url=interaction.user.display_avatar.url)
        e.set_footer(text="VeneziaRP • Prenotazioni colloqui")

        content = None
        if PING_ROLE_ID:
            role = guild.get_role(PING_ROLE_ID)
            if role:
                content = role.mention

        if isinstance(target, discord.TextChannel):
            await target.send(content=content, embed=e)
            await interaction.response.send_message(
                f"✅ Richiesta **{self.tipo}** inviata! Lo staff ti risponderà nel canale dedicato.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "❌ Non trovo il canale destinazione per questo tipo di colloquio. Avvisa lo staff.",
                ephemeral=True,
            )