# views/colloqui_view.py
from __future__ import annotations
import discord
from discord import ui
from modals.prenotazione_modale import PrenotazioneModal

class ColloquiView(discord.ui.View):
    """Pannello prenotazioni colloqui. View persistente (timeout=None)."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🗣️ Prenota ORALE",
        style=discord.ButtonStyle.primary,
        custom_id="colloquio:orale",
    )
    async def prenota_orale(self, interaction: discord.Interaction, _: ui.Button):
        # apre la modale passando il tipo
        await interaction.response.send_modal(PrenotazioneModal(tipo="orale"))

    @discord.ui.button(
        label="🛠️ Prenota PRATICO",
        style=discord.ButtonStyle.success,
        custom_id="colloquio:pratico",
    )
    async def prenota_pratico(self, interaction: discord.Interaction, _: ui.Button):
        await interaction.response.send_modal(PrenotazioneModal(tipo="pratico"))