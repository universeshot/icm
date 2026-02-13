# Data Cogs
Data cogs are infinitely nestable units of data. Interleaving cogs can be used to divide and combine any set data. 


## Base cog
The base cog is a single unit of data. The assumption is that base cogs can grow, and split or combine as needed. 


## Additional cogs / combining cogs
Subsequent layers can begin as additional single units of data. 

Combining any two cogs should create a third and optional fourth component. If only creating a tertiary component, it should be composable by combination with one of the first two cogs' components. 

Additional components are first added as additional cogs. If multiple components can be grouped by the same topic, they may combine to form a single cog unit.

Layered cogs are reordered based on similarity scores with relation to the base cog. In the same manner, adjacent cogs align so that most the similar are closest to the base. 

Two cogs are perfectly similar when they share the same scope and breadth over a shared theme or thesis. 


## Distributing content
Adjacent cogs can be swapped with layered cogs at any time - all adjacent cogs become layered cogs, and all layered cogs become adjacent cogs. Ordering should remain the same. 

Swapping adjacent cogs with layered cogs maintains similarity ordering. 

Similarity for `Cog A -> Cog B = 0.1` and `Cog A -> Cog C = 0.2` does not imply similarity `Cog B -> Cog C = 0.1`. As a result, swapping the base cog forces a complete reordering based on the new similarity scores. 

Reordering also means visiting every layer again to check for any new combinations that should be found. This includes combinations from both multiplying and dividing existing data. 

Multiplying implies adding more data based on inclusive interactions between `Cog A` and `Cog N`. This means combining `Cog A x Cog B`, then `Cog A x Cog B x Cog C`, then `Cog A x Cog B x Cog C x Cog D`, and so on. 

Dividing implies adding more cogs based on how `Cog N` splits into data pieces with known combination paths. Data created through division contains data on `Cog N-1` at most. There is no lower limit to the division layer during division. 

Two data are created during themed splits and one piece is created during a combinatory split, e.g.:
1. `theme @ Cog N-1 x two new data @ Cog N-1`; or
2. `theme, new data @ Cog N-1 x theme, new data @ Cog N-2`; or
3. `theme, new data @ Cog N-1 x theme, existing data @ Cog N-2`; or
4. `theme, new data @ Cog N-1 x theme, existing data @ Cog C`; or
5. `theme, new data @ Cog B x theme, new data @ Cog A`.

After dividing to create data recursive traversal can check for further multiplication and division opportunities. 


## Additional content
Layers can be selectively hidden to check for any skip-level interactions. This is most important for multiplication, since hiding layers changes the input vector and not the available output surface.

As well, similarity score calculations can be made more complex by including other granular features.

Similarity based on a fixed set of predetermined calculations enables a linearly growing number of variations. Similarity based on granular features extends the available similarity scope to an exponential number of variations.

New feature values can also be calculated for each cog. These feature values can be based on a cog's position, contents, or any neighbouring cog's contents.

### Example feature and score updates

#### Pseudo base
Pseudo base cogs can be assumed every `X` distance from the base cog, and similarity scores can be calculated using the immediately preceding base cog or pseudo base cog.

Rules enabling pseudo bases every `X` would be:
```
Similarity score priority order is: 
1. Distance to preceding base or pseudo base
2. With comparison to preceding base:
    1. Theme breadth
    2. Scope covered

New feature: pseudo base (true or false)
- If distance from previous base or pseudo base > `X`, this is pseudo base
```

#### Linearly progressive base
The base cog is determined as a moving value, where the base is an aggregate of every cog up to the current cog. Similarity scores are based on that progressive base value instead of any fixed base value.

Rules:
```
Similarity score priority order is:
1. With comparison to aggregate base score:
    1. Theme breadth
    2. Scope covered

New feature: aggregate base score (theme breadth value, scope covered value)
- For all cogs preceding this, calculate the average (theme breadth value, scope covered value)
    - Note: using the previous cog's already calculated aggregate value helps prevent wasted computation
```


## Impact across distance
Assuming use of a truly reliable similarity score, the impact resulting from combining two components will be greater the further apart the owning cogs begin. 

When dividing one component out, the resulting cogs will be increasingly distant according to how far the nearest created reagent is. Nearer closest reagents imply likelihood of further counterpart reagents. 