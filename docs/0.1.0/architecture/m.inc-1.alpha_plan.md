# Blaise Agüera y Arcas BFF experiment using brainfuck

`Mercenaries Inc.`(M|inc) is a version of the cubff experiment that reframes the experiment to include "incentive"(wealth), "currency"(money)
 "perator" traits, also known as "mercenary" traits.

## Traits

### Incentive
- act as a driving motivation for[`mercenary`,`knight`,`king`]
- `mercenary` incentive is to gain `wealth`(traits) over everything else.
- `knight` [defend]: incentive is to gain employment by the `king` over anything else.
- `king` [kingdom]:incentive is to `survive` by `defend` their `wealth`(traits) over anything else.

### wealth
- wealth represents traits
- mercenaries logic: mercenaries `incentive` is to gain `wealth`(traits) over everything else.
    - survival priority is lower than gaining `wealth`(traits)

### currency

> [!NOTE]
> (100:currency) = (5:wealth)

Currency can be converted to wealth by `trading` with other `kings`
- trading ratio is 1:5
- mercenaries cannot trade with anyone.

```
def king + currency as incentive ->
  if:
    bribe == greater than or equal to mercenary `raid`(traits)
  mercenary will not raid king for their traits
    king subtract = [bribe:{amount}] -> currency -= {amount}
    king will lose small percentage of wealth(traits)
    king will +survive
  else:
    mercenary will raid king for their traits
    king will lose 50% of currency
    king will lose 25% of wealth(traits)
    king will lose currency
```

### kings
- `king` start with a large amount of wealth
- `king` can create more wealth by trading with other `kings`
  -`king` cannot trade with mercenaries, only `bribe` them to not raid them for their traits.
- `bribe`: a percentage of `currency` paid to the `mercenary` to nullify `raid` trait.

### mercenaries
- `mercenary`: act as an intelligent predator that 'raid'(consumes)other tapes its paired with for wealth.
- incentive: `mercenary` == `incentive` ++ `wealth`(traits)
    - can only gain `weath` by `raid`
- currency:
  ```
  from: {
    king = [bribe, raid],
    knight: [raid:defend = {outcome}]
  }
  ```
- trait:
  ```
  raid == {kings:[bribe, raid]} + {knights:[raid:defend = (calculate:winner)]} -> [currency + wealth] => incentive
  ```

### knights
- `knights`: act as a guardian of the `kings` `wealth`(traits)
- incentive: `knight` == `incentive` ++ `wealth`(traits)
    - can only gain `weath` by `defend`
- currency:
    ```
    from: {
      king = [defend],
      mercenary: [defend:raid = (calculate:outcome = {loss} or {gain})] => currency -= {loss} or currency += {gain}
    }
    ```
- trait:
  ```
  defend == [kings:wealth] + [mercenaries:currency] => [incentive]
  ```
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
[1]: Plucking two of those tapes at random from the soup
[2]: Sticking them end to end so you make one tape that is now 128 bytes
  - Run it 
  - (This modification of brainfuck is self-modifying, meaning that when you run it, the code can modify values on that specific combined tape)
[4]: Pulling the tapes back apart
[5]: Dropping them back in the soup
[6]: Repeat indefinitely
```

Once the workflow is repeated a few million times, there will not be much going on.
The huge majority of those bytes are not instructions—only an average of two of them or so on each tape—
so the likelihood of them doing anything is almost zero. You might once in a while see one byte somewhere change.
But after a few million iterations, something magical happens: suddenly the entropy of the soup drops dramatically.
So it goes from being incompressible to being very highly compressible, and programs emerge on those tapes.
Those programs are complex; it takes some real effort to reverse engineer, and you can see it's occurring in a lot of copies.
The fact that it's appearing in a lot of copies tells you what the program is doing: it's copying itself.

- The bff experiment shows you HOW life emerges from nothing
- The emergence of life is the emergence of purpose
- In this case, the purpose of one of these programs or bytes is to reproduce
    - If you were to mess with one of those bytes or change it, you would in most cases break the program
    - When you break the program, it no longer functions to reproduce

Summary:

- bff_experiment = life_emerging
    - life_emerging = purpose_emerging
    - byte_purpose = reproduce
        - byte_change = broken_program
        - broken_program = no_reproduce, no_purpose

## OTHER REF

[Conways Game of Life](https://conwaylife.com/wiki/OTCA_metapixel)
[Broderick Westrope's Tetrigo](https://github.com/Broderick-Westrope/tetrigo)
[Wireworld](https://en.wikipedia.org/wiki/Wireworld)
[Hashlife](https://en.wikipedia.org/wiki/Hashlife)
[Hashlife Repository Index](https://johnhw.github.io/hashlife/index.md.html)
[Hashlife Developer Blog](https://www.dev-mind.blog/hashlife/)

    - king pays mercenaries not to raid them for their traits
- logic: `mercenary` == `incentive` ++ `currency`
    - mercenaries incentive 
### kings
`mercenary`: act an intelligent predator that 'raid'(consumes)other tapes its paired with for wealth.
`incentive`: act as 
`king`: act as a guardian of the 'mercenary's resources(wealth, currency, etc.)