import discord
from discord import ui
from utils import annuncio_storage as store

class SondaggioView(ui.View):
    def __init__(self, message_id: int, opzioni: list[str], state: dict | None = None):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.state = state or {"tipo": "sondaggio", "opzioni": opzioni, "voti": {o: [] for o in opzioni}}

        for op in self.state["opzioni"]:
            self.add_item(SondaggioButton(op, self))

class SondaggioButton(ui.Button):
    def __init__(self, opzione: str, view: SondaggioView):
        super().__init__(label=opzione, style=discord.ButtonStyle.primary)
        self.opzione = opzione
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        for v in self.view_ref.state["voti"].values():
            if uid in v:
                v.remove(uid)
        self.view_ref.state["voti"][self.opzione].append(uid)
        store.save(self.view_ref.message_id, self.view_ref.state)

        self.label = f"{self.opzione} ({len(self.view_ref.state['voti'][self.opzione])})"

        await interaction.response.edit_message(view=self.view_ref)
        await interaction.followup.send(f"✅ Hai votato: {self.opzione}", ephemeral=True)