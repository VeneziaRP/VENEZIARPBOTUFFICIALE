import discord
from discord import ui

from modals.annuncio_standard_modal import AnnuncioStandardModal
from modals.annuncio_votazione_modal import AnnuncioVotazioneModal
from modals.annuncio_sondaggio_modal import AnnuncioSondaggioModal
from modals.annuncio_evento_modal import AnnuncioEventoModal
from views.tipi.conferma_view import ConfermaView
from utils import annuncio_storage as store

class AnnuncioSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="📢 Standard", value="standard"),
            discord.SelectOption(label="✅ Votazione", value="votazione"),
            discord.SelectOption(label="📄 Conferma", value="conferma"),
            discord.SelectOption(label="📊 Sondaggio", value="sondaggio"),
            discord.SelectOption(label="🎉 Evento", value="evento"),
            discord.SelectOption(label="🔒 Staff Only", value="staff"),
        ]
        super().__init__(placeholder="Seleziona tipo annuncio...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        tipo = self.values[0]
        if tipo == "standard":
            return await interaction.response.send_modal(AnnuncioStandardModal())
        elif tipo == "votazione":
            return await interaction.response.send_modal(AnnuncioVotazioneModal())
        elif tipo == "conferma":
            view = ConfermaView(interaction.message.id)
            state = {"tipo": "conferma", "confermati": []}
            store.save(interaction.message.id, state)
            embed = discord.Embed(title="📄 Conferma Richiesta", description="Premi **✅ Confermo** per confermare.", color=discord.Color.gold())
            return await interaction.response.send_message(embed=embed, view=view)
        elif tipo == "sondaggio":
            return await interaction.response.send_modal(AnnuncioSondaggioModal())
        elif tipo == "evento":
            return await interaction.response.send_modal(AnnuncioEventoModal())
        elif tipo == "staff":
            embed = discord.Embed(title="🔒 Annuncio Staff", description="Messaggio interno allo staff.", color=discord.Color.red())
            return await interaction.response.send_message(embed=embed)

class AnnuncioSelectView(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(AnnuncioSelect())
    