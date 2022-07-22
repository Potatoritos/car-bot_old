import asyncio
from collections import deque
import random
import time
from typing import Annotated as A, Optional

import discord
import car


class VCLogCooldownTuple:
    def __init__(self, member_id: int, time: float):
        self.member_id = member_id
        self.time = time


class Moderation(car.Cog):
    category = "Moderation"
    # checks = (car.guild_must_be_id(495327409487478785),)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vc_dq: deque[VCLogCooldownTuple] = deque()
        self.vc_count: dict[int, int] = {}

        self.vc_prev_msg = None
        self.vc_prev_msg_uid = None
        self.vc_prev_msg_cnt = 0

    @car.listener
    async def on_message(self, msg):
        if msg.guild is None:
            return

        cfg = self.bot.guild_settings.select(
            'vclog_channel, vclog_enabled', 'WHERE guild_id=?', (msg.guild.id,)
        )
        if not cfg['vclog_enabled']:
            return

        if msg.channel.id == cfg['vclog_channel']:
            self.vc_prev_msg_cnt += 1

    @car.listener
    async def on_voice_state_update(self, member, bef, aft):
        if member.bot or bef.channel == aft.channel:
            return

        cfg = self.bot.guild_settings.select(
            'vclog_channel, vclog_enabled', 'WHERE guild_id=?',
            (member.guild.id,)
        )
        if not cfg['vclog_enabled']:
            return

        log_channel = discord.utils.get(member.guild.channels,
                                    id=cfg['vclog_channel'])
        if log_channel is None:
            return
        
        # update how many VC moves someone has done in the past 15s
        while len(self.vc_dq) and time.monotonic() - self.vc_dq[0].time > 15:
            self.vc_count[self.vc_dq.popleft().member_id] -= 1

        if member.id not in self.vc_count:
            self.vc_count[member.id] = 0

        self.vc_count[member.id] += 1
        self.vc_dq.append(VCLogCooldownTuple(member.id, time.monotonic()))

        if self.vc_count[member.id] > 5:
            return

        if aft.channel is None:
            status = "◀—"
            channel = bef.channel
        else:
            status = "—▶"
            channel = aft.channel

        status_msg = f"`{status}` <#{channel.id}>"

        if self.vc_prev_msg is not None and self.vc_prev_msg_cnt <= 1 \
                and member.id == self.vc_prev_msg_uid:
            prev = self.vc_prev_msg.embeds[0]

            e = discord.Embed(description=f"{prev.description}\n{status_msg}")
            e.set_author(name=prev.author.name, icon_url=prev.author.icon_url)

            self.vc_prev_msg = await self.vc_prev_msg.edit(embed=e)

        else:
            e = discord.Embed(description=status_msg)
            e.set_author(name=member.name, icon_url=member.avatar.url)

            msg = await log_channel.send(embed=e)

            self.vc_prev_msg = msg
            self.vc_prev_msg_uid = member.id
            self.vc_prev_msg_cnt = 0

    @car.listener
    async def on_message_edit(self, bef, aft):
        if bef.author.bot or bef.content == aft.content:
            return

        cfg = self.bot.guild_settings.select(
            'modlog_channel, modlog_enabled', 'WHERE guild_id=?',
            (bef.guild.id,)
        )
        if not cfg['modlog_enabled']:
            return

        channel = discord.utils.get(bef.guild.text_channels,
                                    id=cfg['modlog_channel'])

        e = discord.Embed(description=(
            f"[[Jump]]({bef.jump_url}) {bef.author.mention} in"
            f"{bef.channel.mention}"
        ))
        e.set_author(name="Message Edit",
                     icon_url=bef.author.avatar.url)

        if len(bef.content) > 0:
            e.add_field(name="Before", value=bef.content)

        if len(aft.content) > 0:
            ctn = aft.content
            if len(bef.content) + len(aft.content) > 3900:
                ctn = aft.content[max(0, len(aft.content)-100):] \
                    + "\n*(continued...)*"

            e.add_field(name="After", value=ctn)

        await channel.send(embed=e)

    @car.listener
    async def on_message_delete(self, msg):
        if msg.author.bot:
            return

        cfg = self.bot.guild_settings.select(
            'modlog_channel, modlog_enabled', 'WHERE guild_id=?',
            (msg.guild.id,)
        )
        if not cfg['modlog_enabled']:
            return

        channel = discord.utils.get(msg.guild.text_channels,
                                    id=cfg['modlog_channel'])

        e = discord.Embed(description=(
            f"{msg.author.mention} in {msg.channel.mention}"
        ))
        e.set_author(name="Message Delete",
                     icon_url=msg.author.avatar.url)

        if len(msg.content) > 0:
            e.add_field(name="Content", value=msg.content)

        await channel.send(embed=e)

    @car.slash_command_group(name="give")
    async def _give(self, ctx): pass

    @staticmethod
    async def add_role(member, role):
        if role in member.roles:
            raise car.CommandError(f"{member.mention} already has role "
                                   f"{role.mention}!")

        try:
            await member.add_roles(role)
        except discord.errors.Forbidden:
            raise car.CommandError("I require the manage roles permission!")

    @staticmethod
    async def remove_role(member, role):
        if role not in member.roles:
            raise car.CommandError(f"{member.mention} already doesn't have "
                                   f"role {role.mention}!")

        try:
            await member.remove_roles(role)
        except discord.errors.Forbidden:
            raise car.CommandError("I require the manage roles permission!")

    @car.mixed_command(slash_name="give role", aliases=['addrole', 'role'])
    @car.requires_permissions(manage_roles=True)
    async def giverole(self, ctx, member: discord.Member,
                       role: discord.Role):
        """Gives a role to a user"""

        if ctx.author.top_role <= role:
            raise car.CommandError(f"You aren't allowed to give this role!")

        await self.add_role(member, role)

        e = discord.Embed(
            description=f"Added {role.mention} to {member.mention}")

        await ctx.respond(embed=e)

    @car.slash_command_group(name="revoke")
    async def _revoke(self, ctx): pass

    @car.mixed_command(slash_name="revoke role")
    @car.requires_permissions(manage_roles=True)
    async def revokerole(self, ctx, member: discord.Member,
                         role: discord.Role):
        """Removes a role from a user"""

        if ctx.author.top_role <= role:
            raise car.CommandError(f"You aren't allowed to remove this role!")

        await self.remove_role(member, role)

        e = discord.Embed(
            description=f"Removed {role.mention} from {member.mention}")

        await ctx.respond(embed=e)

    @car.slash_command_group(name="wab")
    async def _wab(self, ctx): pass

    @car.mixed_command(slash_name="wab ban", aliases=["wabban"])
    @car.guild_must_be_id(495327409487478785)
    @car.requires_permissions(manage_roles=True)
    async def ban(
        self, ctx,
        member: discord.Member,
        countdown: A[Optional[int], car.ToInt() | car.InRange(0, 60)] = 0
    ):
        """Adds the banned role to a user"""
        role = discord.utils.get(ctx.guild.roles, id=525044579800711170)

        if role in member.roles:
            raise car.CommandError(f"{member.mention} is already banned!")

        edit = False

        if countdown > 0:
            edit = True
            e = discord.Embed(
                description=(
                    f":rotating_light: {member.mention} will be BANNED "
                    f"in {int(round(countdown))}......."
                )
            )
            await ctx.respond(embed=e)

            while countdown > 0:
                e = discord.Embed(
                    description=(
                        f":rotating_light: {member.mention} will be BANNED "
                        f"in {int(round(countdown))}......."
                    )
                )
                await ctx.edit_response(embed=e)
                await asyncio.sleep(1)
                countdown -= 1

        await self.add_role(member, role)

        emoji = random.choice([':flushed:', ':moyai:', ':monkey:',
                               ':gorilla:', ':orangutan:',
                               '<:blobangery:808087859965853726>',
                               '<:grimace:716692825777111100>'])

        e = discord.Embed(
            description=(
                f":rotating_light: {member.mention} has been BANNED "
                f"from the Wab Server!!!! {emoji}"
            )
        )
        if edit:
            await ctx.edit_response(embed=e)
        else:
            await ctx.respond(embed=e)

    @car.mixed_command(slash_name="wab unban", aliases=["wabunban"])
    @car.guild_must_be_id(495327409487478785)
    @car.requires_permissions(manage_roles=True)
    async def unban(self, ctx, member: discord.Member):
        """Removes the banned role from a user"""
        role = discord.utils.get(ctx.guild.roles, id=525044579800711170)

        if role not in member.roles:
            raise car.CommandError(f"{member.mention} is already unbanned!")

        await self.remove_role(member, role)

        emoji = random.choice(['<:grimace:716692825777111100>',
                               '<:individual:811309916429353010>',
                               '<:nigersaurus2:722278862079131731>'])
        e = discord.Embed(
            description=(
                f":rotating_light: {member.mention} has been unbanned {emoji}"
            )
        )
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="wab mute", aliases=["wabmute"])
    @car.guild_must_be_id(495327409487478785)
    @car.requires_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member):
        """Adds the muted role to a user"""
        role = discord.utils.get(ctx.guild.roles, id=536552924583821313)

        if role in member.roles:
            raise car.CommandError(f"{member.mention} is already muted!")

        await self.add_role(member, role)

        e = discord.Embed(
            description=f":rotating_light: {member.mention} has been muted"
        )
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="wab unmute", aliases=["wabunmute"])
    @car.guild_must_be_id(495327409487478785)
    @car.requires_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Removes the muted role from a user"""
        role = discord.utils.get(ctx.guild.roles, id=536552924583821313)

        if role not in member.roles:
            raise car.CommandError(f"{member.mention} is already unmuted!")

        await self.remove_role(member, role)

        emoji = random.choice(['<:grimace:716692825777111100>',
                               '<:individual:811309916429353010>',
                               '<:nigersaurus2:722278862079131731>'])
        e = discord.Embed(
            description=(
                f":rotating_light: {member.mention} has been unbanned {emoji}"
            )
        )
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="wab verify", aliases=["wabverify"])
    @car.guild_must_be_id(495327409487478785)
    @car.requires_permissions(manage_roles=True)
    async def verify(self, ctx, member: discord.Member):
        """Adds the muted role to a user"""
        role = discord.utils.get(ctx.guild.roles, id=818612299149082634)

        if role in member.roles:
            raise car.CommandError(f"{member.mention} is already verified!")

        await self.add_role(member, role)

        e = discord.Embed(
            description=f":rotating_light: {member.mention} has been verified"
        )
        await ctx.respond(embed=e)

    @car.mixed_command(slash_name="wab unverify", aliases=["wabunverify"])
    @car.guild_must_be_id(495327409487478785)
    @car.requires_permissions(manage_roles=True)
    async def unverify(self, ctx, member: discord.Member):
        """Removes the verified role from a user"""
        role = discord.utils.get(ctx.guild.roles, id=818612299149082634)

        if role not in member.roles:
            raise car.CommandError(f"{member.mention} is already unverified!")

        await self.remove_role(member, role)

        emoji = random.choice([':monkey:', ':orangutan:', ':gorilla:'
                               '<:grimace:716692825777111100>',
                               '<:individual:811309916429353010>',
                               '<:nigersaurus2:722278862079131731>'])
        e = discord.Embed(
            description=(
                f":rotating_light: {member.mention} has been unverified {emoji}"
            )
        )
        await ctx.respond(embed=e)

