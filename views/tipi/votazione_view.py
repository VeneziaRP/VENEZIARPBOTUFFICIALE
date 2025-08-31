import discord
from discord import ui
from utils import annuncio_storage as store

class VotazioneView(ui.View):
    def __init__(self, message_id: int, state: dict | None = None):
        super().__init__(timeout=None)
        self.message_id = message_id
        self.state = state or {"tipo": "votazione", "yes": [], "no": [], "maybe": []}
        self._sync_labels()

    def _sync_labels(self):
        self.b_si.label = f"✅ Sì ({len(self.state['yes'])})"
        self.b_no.label = f"❌ No ({len(self.state['no'])})"
        self.b_forse.label = f"🤔 Forse ({len(self.state['maybe'])})"

    def _save(self):
        store.save(self.message_id, self.state)

    async def _vote(self, interaction: discord.Interaction, choice: str):
        uid = str(interaction.user.id)
        for k in ("yes", "no", "maybe"):
            if uid in self.state[k]:
                self.state[k].remove(uid)
        self.state[choice].append(uid)
        self._save()
        self._sync_labels()

        # aggiorna messaggio → prima risposta
        await interaction.response.edit_message(view=self)

        # opzionale: feedback all'utente
        await interaction.followup.send("✅ Voto registrato!", ephemeral=True)

    @ui.button(label="✅ Sì (0)", style=discord.ButtonStyle.success)
    async def b_si(self, interaction: discord.Interaction, button: ui.Button):
        await self._vote(interaction, "yes")

    @ui.button(label="❌ No (0)", style=discord.ButtonStyle.danger)
    async def b_no(self, interaction: discord.Interaction, button: ui.Button):
        await self._vote(interaction, "no")

    @ui.button(label="🤔 Forse (0)", style=discord.ButtonStyle.secondary)
    async def b_forse(self, interaction: discord.Interaction, button: ui.Button):
        await self._vote(interaction, "maybe")