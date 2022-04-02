from typing import Annotated as A, Optional
import discord
import car
import carpp


class Simulation(car.Cog):
    category = "Simulation"
    @car.mixed_command()
    async def akpull(
        self,
        ctx: car.Context,
        banner_type: A[int, car.FromChoices({'Standard': 50, 'Limited': 70})],
        pulls: A[Optional[int], car.InRange(lower=0)] = 0,
        orundums: A[Optional[int], car.InRange(lower=0)] = 0,
        originite_prime: A[Optional[int], car.InRange(lower=0)] = 0
    ):
        assert pulls is not None and orundums is not None \
            and originite_prime is not None
        amt_pulls = int(pulls + orundums/600 + originite_prime*180/600)
        if amt_pulls > 600:
            raise car.CheckError("The total amount of pulls must be <=600")
        if amt_pulls <= 0:
            raise car.CheckError("You must specify an amount of pulls!")
        trials = int(min(1e6, int(2e7/amt_pulls)))
        await ctx.defer()

        expected, no_rateup, any_rateup, specific_rateup, both_rateup \
            = carpp.akpull(trials, amt_pulls, banner_type)

        desc = (
            "```css\n[6* results]\n"
            f"Expected amount    = {expected:.2f}\n"
            f"P(No rateups)       = {no_rateup*100:.2f}%\n"
            f"P(Any rateup)      = {any_rateup*100:.2f}%\n"
            f"P(Specific rateup) = {specific_rateup*100:.2f}%\n"
            f"P(Both rateups)    = {both_rateup*100:.2f}%\n"
            "```"
        )
        e = discord.Embed(title="Simulation results", description=desc)
        e.set_footer(text=f"Pulls: {amt_pulls}, trials: {trials:,}")
        await ctx.edit_response(embed=e)

