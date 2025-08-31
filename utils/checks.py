# utils/checks.py
import discord
from discord import app_commands

STAFF_ROLE_ID = 1408613549168918528  # <— ID ruolo Staff
CITTADINO_ROLE_ID = 1408613574850379959  # <— ID ruolo Cittadino

def is_staff(interaction: discord.Interaction) -> bool:
    """True se l’utente è staff (permessi o ruolo staff)."""
    if interaction.user.guild_permissions.manage_guild:
        return True
    staff_role = interaction.guild.get_role(STAFF_ROLE_ID) if interaction.guild else None
    return staff_role in interaction.user.roles if staff_role else False

def is_cittadino(interaction: discord.Interaction) -> bool:
    """True se l’utente ha il ruolo cittadino."""
    citt_role = interaction.guild.get_role(CITTADINO_ROLE_ID) if interaction.guild else None
    return citt_role in interaction.user.roles if citt_role else False

# Decoratore per staff-only
def staff_only():
    async def predicate(interaction: discord.Interaction):
        if not is_staff(interaction):
            raise app_commands.CheckFailure("Non sei autorizzato ad usare questo comando.")
        return True
    return app_commands.check(predicate)

# Decoratore per cittadini (solo per /profilo)
def cittadini_only():
    async def predicate(interaction: discord.Interaction):
        if not is_cittadino(interaction) and not is_staff(interaction):
            raise app_commands.CheckFailure("Solo i cittadini possono usare questo comando.")
        return True
    return app_commands.check(predicate)