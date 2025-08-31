import discord
from utils import annuncio_storage as store

class AnnuncioStandardModal(discord.ui.Modal, title="Crea Annuncio Standard"):
    def __init__(self):
        super().__init__(timeout=None)
        self.titolo = discord.ui.TextInput(label="Titolo", placeholder="ANNUNCIO IMPORTANTE!!", max_length=128)
        self.descrizione = discord.ui.TextInput(label="Descrizione", style=discord.TextStyle.paragraph, placeholder="Scrivi il contenuto...", max_length=2000)
        self.add_item(self.titolo)
        self.add_item(self.descrizione)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title=str(self.titolo.value), description=str(self.descrizione.value), color=discord.Color.gold())
        embed.set_footer(text="VeneziaRP | Annunci")
        msg = await interaction.response.send_message(embed=embed)
        store.save(msg.id, {"tipo": "standard", "titolo": self.titolo.value, "descrizione": self.descrizione.value})