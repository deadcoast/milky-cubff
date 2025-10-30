# Blaise Agüera y Arcas BFF experiment using brainfuck

`Mercenaries Inc.` (M|inc) is a version of the cuBFF experiment that reframes the experiment to include "incentive" (wealth), "currency" (money), and "operator" traits, also known as "mercenary" traits.

## Traits

### Incentive
- Acts as a driving motivation for [`mercenary`, `knight`, `king`].
- `mercenary` incentive is to gain `wealth` (traits) over everything else, then currency, then raid frequency, then survival.
- `knight` [defend]: incentive is to gain employment by the `king`, maximize successful defends, then currency, then defend/sense/adapt growth, then survival.
- `king` [kingdom]: incentive is to `survive` by `defend`ing their `wealth` (traits), maintain a currency buffer, then grow wealth via king↔king trade.

### wealth
- Wealth represents traits.
- Mercenaries logic: `mercenary` incentive is to gain `wealth` (traits) over everything else.
    - Survival priority is lower than gaining `wealth` (traits).

### currency

> [!NOTE]
> (100 : currency) = (5 : wealth)

Currency can be converted to wealth by `trading` with other `kings`.
- Trading ratio is 100:5 (i.e., each 100 currency invested by a king creates +5 wealth units).
- Distribution of created wealth per 100 currency (current model): `defend:+3`, `trade:+2` (any remainder to `defend`).
- Mercenaries cannot trade with anyone.

```

king + currency as incentive ->
constants:
BRIBE_LEAKAGE = 0.05            # 5% wealth leakage on successful bribe
ON_FAILED_BRIBE:
king_currency_loss = 0.50     # 50% of king's currency
king_wealth_loss   = 0.25     # 25% of each wealth trait goes to merc
if:
bribe_threshold (posted by king) >= raid_value(merc, king, assigned_knights)
and king.currency >= bribe_threshold
then:
mercenary will not raid king for their traits
king subtract = [bribe:{amount}] -> currency -= {amount}
mercenary currency += {amount}
king will lose small percentage of wealth(traits): scale all traits by (1 - 0.05)
king will +survive (no raid this tick)
else:
mercenary will raid king for their traits (contest or unopposed):
if no knight assigned:
king will lose 50% of currency (transfer to mercenary)
king will lose 25% of wealth(traits) (each trait slice transfers to mercenary)
if a knight is assigned and loses:
same mirrored losses apply as above

```

### kings
- `king` starts with a large amount of wealth.
- `king` can create more wealth by trading with other `kings` only (100 currency → +5 wealth).
    - `king` cannot trade with mercenaries; they can only `bribe` them to avoid a raid.
- `bribe`: a threshold amount of `currency` paid to the `mercenary` to nullify `raid`.
    - On successful bribe: wealth leakage = 5% across all traits.
    - On failed bribe or contested loss: king loses 50% currency and 25% of each wealth trait (mirrored to the mercenary).

### mercenaries
- `mercenary`: acts as an intelligent predator that `raid`s (consumes) other tapes it’s paired with for wealth.
- incentive: `mercenary` == prioritize `wealth` gain → `currency` gain → `raid` frequency → `survival`.
    - can only gain `wealth` by `raid` (or mirrored transfers on king loss) and small bounty losses they inflict on knights (inverse of knight bounty).
- currency:
```

from: {
king = [bribe, raid (mirrored king losses)],
knight: [defend vs raid = {stake transfer if knight wins (loss to merc), else no stake gain}]
}

```
- trait:
```

raid == {kings:[bribe accepted → none | failed bribe/defend loss → mirrored wealth]}
+ {knights:[raid:defend = (deterministic outcome; if knight wins, merc loses small bounty % from (raid, adapt))]}
-> [currency + wealth] => incentive

```
- Targeting rule (current model): select the king with highest `wealth_exposed = wealth_total * exposure_factor(king=1.0)`; tie-break by king id.

### knights
- `knights`: act as a guardian of the `kings` `wealth` (traits).
- incentive: `knight` == maximize successful `defend`s → `currency` (retainers, stakes) → `defend/sense/adapt` growth → survival.
- can only gain `wealth` by `defend` (bounty transfers from mercenary on defend win).
- currency:
```

from: {
king = [defend (retainer fee each tick if employed)],
mercenary: [defend:raid = (deterministic outcome) =>
if win: currency += stake, merc.currency -= stake
if loss: currency -= stake (min 0)]
}

```
- trait:
```

defend == [kings:wealth protected] + [mercenaries: (bounty from merc 'raid' and 'adapt' on defend win)] => [incentive]

````
1. Variations to research @m.inc-2.variations.md you will find their repositories linked for you to review
2. Review the repositories
3. Formulate the `m.inc` version in @0.1.1.md

---

1. He began with a bunch of tapes 64 bytes long.
2. Bytes start off filled with random bytes with 7 instructions; the great majority of those random bytes—about 31/32 of them—are no-ops,
 meaning they don't code for any instruction at all, so they start off random and very much purposeless.
3. There are millions of them in the byte soup.
4. The procedure is very simple:

workflow:

```text
[1]: Pluck two tapes at random from the soup
[2]: Stick them end-to-end so you make one tape that is now 128 bytes
   - Run it
   - (This modification of brainfuck is self-modifying, meaning that when you run it, the code can modify values on that specific combined tape)
[4]: Pull the tapes back apart
[5]: Drop them back in the soup
[6]: Repeat indefinitely
````

Once the workflow is repeated a few million times, there will not be much going on.
The huge majority of those bytes are not instructions—only an average of two of them or so on each tape—
so the likelihood of them doing anything is almost zero. You might once in a while see one byte somewhere change.
But after a few million iterations, something magical happens: suddenly the entropy of the soup drops dramatically.
So it goes from being incompressible to being very highly compressible, and programs emerge on those tapes.
Those programs are complex; it takes some real effort to reverse engineer, and you can see it's occurring in a lot of copies.
The fact that it's appearing in a lot of copies tells you what the program is doing: it's copying itself.

- The BFF experiment shows you HOW life emerges from nothing.
- The emergence of life is the emergence of purpose.
- In this case, the purpose of one of these programs or bytes is to reproduce:

    - If you were to mess with one of those bytes or change it, you would in most cases break the program.
    - When you break the program, it no longer functions to reproduce.

Summary:

- bff_experiment = life_emerging

    - life_emerging = purpose_emerging
    - byte_purpose = reproduce

        - byte_change = broken_program
        - broken_program = no_reproduce, no_purpose

---
