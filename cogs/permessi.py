import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands

ROLES_FILE = Path("data/roles.json")
CHANS_FILE = Path("data/channels.json")
for p in (ROLES_FILE, CHANS_FILE):
    p.parent.mkdir(parents=True, exist_ok=True)

# ---------------- utils ----------------
def load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except:
            return {}
    return {}

def get_role(g: discord.Guild, rid): 
    return g.get_role(rid) if rid else None

def resolve_category(g: discord.Guild, key: str) -> discord.CategoryChannel | None:
    data = load_json(CHANS_FILE)
    # prova nome esatto
    name = (data.get("names", {}).get("categories", {}) or {}).get(key)
    if name:
        for cat in g.categories:
            if cat.name == name:
                return cat
    # fallback ID
    cid = (data.get("categories") or {}).get(key)
    if cid:
        ch = g.get_channel(cid)
        if isinstance(ch, discord.CategoryChannel):
            return ch
    return None

def resolve_channel(g: discord.Guild, key: str) -> discord.TextChannel | None:
    data = load_json(CHANS_FILE)
    # prova nome esatto
    name = (data.get("names", {}).get("channels", {}) or {}).get(key)
    if name:
        for ch in g.text_channels:
            if ch.name == name:
                return ch
    # fallback ID
    cid = (data.get("channels") or {}).get(key)
    if cid:
        ch = g.get_channel(cid)
        if isinstance(ch, discord.TextChannel):
            return ch
    return None

# ---------------- Cog ----------------
class Permessi(commands.Cog):
    def __init__(self, bot): self.bot = bot

    async def _edit_category_and_children(self, cat: discord.CategoryChannel, overwrites: dict, reason: str):
        if not cat: return
        try:
            await cat.edit(overwrites=overwrites, reason=reason)
        except Exception:
            pass
        for ch in cat.channels:
            try:
                await ch.edit(overwrites=overwrites, reason=f"{reason} (sync)")
            except Exception:
                pass

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="perm_check", description="Mostra categorie/canali risolti.")
    async def perm_check(self, itx: discord.Interaction):
        g = itx.guild
        cat_ver = resolve_category(g, "verifica")
        cat_reg = resolve_category(g, "registro")
        cat_ana = resolve_category(g, "anagrafe")
        ch_ver  = resolve_channel(g, "verifica")
        ch_citt = resolve_channel(g, "cittadinanza")

        lines = [
            f"Categoria verifica: {cat_ver.name if cat_ver else '❌'}",
            f"Categoria registro: {cat_reg.name if cat_reg else '❌'}",
            f"Categoria anagrafe: {cat_ana.name if cat_ana else '❌'}",
            f"Canale verifica: {ch_ver.name if ch_ver else '❌'}",
            f"Canale cittadinanza: {ch_citt.name if ch_citt else '❌'}",
        ]
        await itx.response.send_message("```\n" + "\n".join(lines) + "\n```", ephemeral=True)

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="apply_permessi", description="Applica i permessi logici ai ruoli principali.")
    async def apply_permessi(self, itx: discord.Interaction):
        await itx.response.defer(ephemeral=True, thinking=True)
        g = itx.guild
        roles_map = load_json(ROLES_FILE)

        r_nonver = get_role(g, roles_map.get("non_verificato"))
        r_turista = get_role(g, roles_map.get("turista"))
        r_citt = get_role(g, roles_map.get("cittadino"))
        staff_ids = (roles_map.get("groups") or {}).get("staff", [])
        staff_roles = [get_role(g, i) for i in staff_ids if get_role(g, i)]

        if not r_nonver or not r_turista or not r_citt:
            return await itx.followup.send("❌ Config ruoli incompleta.", ephemeral=True)

        # categorie/canali
        cat_ver = resolve_category(g, "verifica")
        cat_reg = resolve_category(g, "registro")
        cat_ana = resolve_category(g, "anagrafe")
        ch_citt = resolve_channel(g, "cittadinanza")

        # --- VERIFICA ---
        if cat_ver:
            ow = {
                g.default_role: discord.PermissionOverwrite(view_channel=False),
                r_nonver: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                r_turista: discord.PermissionOverwrite(view_channel=False),
                r_citt:    discord.PermissionOverwrite(view_channel=False)
            }
            for s in staff_roles:
                ow[s] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)
            await self._edit_category_and_children(cat_ver, ow, "Permessi: Verifica")

        # --- REGISTRO (turista vede) ---
        if cat_reg:
            ow = {
                g.default_role: discord.PermissionOverwrite(view_channel=False),
                r_nonver: discord.PermissionOverwrite(view_channel=False),
                r_turista: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                r_citt:    discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            }
            for s in staff_roles:
                ow[s] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)
            await self._edit_category_and_children(cat_reg, ow, "Permessi: Registro")

        # --- ANAGRAFE (turista no, citt sì; eccezione cittadinanza) ---
        if cat_ana:
            ow = {
                g.default_role: discord.PermissionOverwrite(view_channel=False),
                r_nonver: discord.PermissionOverwrite(view_channel=False),
                r_turista: discord.PermissionOverwrite(view_channel=False),
                r_citt:    discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            }
            for s in staff_roles:
                ow[s] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)
            await self._edit_category_and_children(cat_ana, ow, "Permessi: Anagrafe")

            if ch_citt:
                ow_citt = dict(ow)
                ow_citt[r_turista] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
                try:
                    await ch_citt.edit(overwrites=ow_citt, reason="Eccezione: cittadinanza visibile a Turista")
                except Exception:
                    pass

        # --- ALTRE CATEGORIE ---
        handled = {c.id for c in [cat_ver, cat_reg, cat_ana] if c}
        for cat in g.categories:
            if cat.id in handled: continue
            ow = {
                g.default_role: discord.PermissionOverwrite(view_channel=False),
                r_nonver: discord.PermissionOverwrite(view_channel=False),
                r_turista: discord.PermissionOverwrite(view_channel=False),
                r_citt:    discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, connect=True, speak=True),
            }
            for s in staff_roles:
                ow[s] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True, connect=True, speak=True)
            await self._edit_category_and_children(cat, ow, f"Permessi: {cat.name}")

        await itx.followup.send("✅ Permessi applicati con successo.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Permessi(bot))