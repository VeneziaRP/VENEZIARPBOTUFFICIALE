import discord
from discord import ui
from utils import annuncio_storage as store

class ConfermaView(ui.View):
    def __init__(self, message_id: int, state: dict | None = None):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.state = state or {"tipo": "conferma", "confermati": []}

    def _save(self):
        store.save(self.message_id, self.state)

    @ui.button(label="✅ Confermo", style=discord.ButtonStyle.success)
    async def b_confermo(self, interaction: discord.Interaction, button: ui.Button):
        uid = str(interaction.user.id)
        if uid in self.state["confermati"]:
            return await interaction.response.send_message("Hai già confermato.", ephemeral=True)

        self.state["confermati"].append(uid)
        self._save()
        await interaction.response.send_message("✅ Conferma registrata!", ephemeral=True)