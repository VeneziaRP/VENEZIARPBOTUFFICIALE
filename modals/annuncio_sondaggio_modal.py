import discord
from views.tipi.sondaggio_view import SondaggioView
from utils import annuncio_storage as store

class AnnuncioSondaggioModal(discord.ui.Modal, title="Crea Sondaggio Rapido"):
    def __init__(self):
        super().__init__(timeout=None)
        self.domanda = discord.ui.TextInput(label="Domanda", max_length=200)
        self.opzioni = discord.ui.TextInput(label="Opzioni (separate da ,)", max_length=200)
        self.add_item(self.domanda)
        self.add_item(self.opzioni)

    async def on_submit(self, interaction: discord.Interaction):
        ops = [o.strip() for o in self.opzioni.value.split(",") if o.strip()]
        embed = discord.Embed(title="📊 Sondaggio", description=str(self.domanda.value), color=discord.Color.gold())
        view = SondaggioView(interaction.id, ops)
        msg = await interaction.response.send_message(embed=embed, view=view)
        store.save(msg.id, {"tipo": "sondaggio", "domanda": self.domanda.value, "opzioni": ops, "voti": {o: [] for o in ops}})