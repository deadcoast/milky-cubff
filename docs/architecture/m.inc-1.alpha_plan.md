# Blaise Agüera y Arcas BFF experiment using brainfuck

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
