# Ice Cream Machine

Base, churn, cream, repeat. 

Provided input is almost never the same as the required input. That is in either content or format. 

The standard "translation layer" is glue code. Glue code is typically:
1. Platform specific.
2. Machine-code oriented.
3. Tiring to maintain.

Nobody likes glue code. 

Good news: this isn't glue code.

Being able to handle rapid native language translations has forever been a second class citizen. Pushing one step further to enable same language translations, for example `english -> english`, is typically not even considered necessary. 

The Ice Cream Machine provides infrastructure enabling any number of non-standard translations. 

## What's the goal?

The goal is to reuse the same computing power while maximizing output potential.

The immediate use case is: using a single Gen AI model to carry out several queries under the guise and input of a single query.

In fields where the terminology has been appropriately stacked, the same base level understanding can be applied broadly and any gaps can be filled in after expanding the translation.

## Existing real world use cases?

This Ice Cream Machine facilitates digital equivalents of [rotor machines](https://en.wikipedia.org/wiki/Rotor_machine) (which are used in the [TypeX](https://en.wikipedia.org/wiki/Typex) and [Enigma machine](https://en.wikipedia.org/wiki/Enigma_machine)).

As well, this enables an explosion of every day technical work into a number of different real world applications (akin to the performance of the [Bomba](https://en.wikipedia.org/wiki/Bomba_(cryptography))). 

## Current implementation status

The repository now includes a first-pass cogs runtime focused on data structures and iteration:

1. UML archive: `docs/cogs-uml.md`
2. Phase-1 implementation notes: `docs/cogs-system.md`
3. Python package: `src/icm/` with grouped modules in:
   - `src/icm/core/`
   - `src/icm/scoring/`
   - `src/icm/interfaces/`
4. Runnable sample: `src/icm/example.py`
5. MCP interface and isolation notes: `docs/icm-mcp.md`
