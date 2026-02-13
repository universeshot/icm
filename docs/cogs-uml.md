# Data Cogs UML

This file stores the latest UML sketches discussed for the cogs data system.

## Core Class Diagram

```text
+--------------------+        publishes        +----------------------+
| CogAtom            |------------------------>| EventBus             |
+--------------------+                         +----------------------+
| id: AtomId         |                         | subscribe(topic,h)   |
| payload: dict      |                         | publish(event)       |
| features: dict     |                         +----------------------+
| version: int       |
| update(...)        |
+--------------------+

+----------------------+      1      *      +----------------------+
| CogGraph             |---------------------| GraphNode            |
+----------------------+ contains            +----------------------+
| id: GraphId          |                     | atom_id: AtomId      |
| node_order: [AtomId] |                     | layer: int           |
| hidden_layers: set   |                     | role: base|adj|lay   |
| context_hash: str    |                     +----------------------+
| apply_policy(...)    |
| rebuild_order(...)   |
+----------------------+

+----------------------+       1     *       +----------------------+
| ScoreSet             |---------------------| ScoreEntry            |
+----------------------+ has directed edges  +----------------------+
| id: ScoreSetId       |                     | from_id: AtomId       |
| strategy_id: str     |                     | to_id: AtomId         |
| context_hash: str    |                     | score: float          |
| version: int         |                     | variance: float       |
| get(a,b)->Score      |                     | feature_vec: dict     |
+----------------------+                     +----------------------+

+----------------------+       indexes       +----------------------+
| NeighborIndex        |-------------------->| ScoreSet              |
+----------------------+                     +----------------------+
| by_from: from->[to*] |
| top_unseen(from,...) |
| range_group(from,y)  |
+----------------------+

+----------------------+        used by       +----------------------+
| PathPolicy           |<---------------------| TraversalEngine       |
+----------------------+                      +----------------------+
| strategy_id          |                      | next_chain(...)       |
| direction_mode       |                      | expand_multiply(...)  |
| candidate_filter     |                      | expand_divide(...)    |
| selection_key[]      |                      +----------------------+
| equivalence_rule     |
| stop_rule            |
+----------------------+

+----------------------+       view-scoped    +----------------------+
| EquivalenceCluster   |--------------------->| CogGraph             |
+----------------------+                      +----------------------+
| strategy_id          | groups nodes by      | (no physical merge)  |
| context_hash         | epsilon/rules        +----------------------+
| cluster_id->[atom*]  |
+----------------------+

+----------------------+     subscribes       +----------------------+
| RecomputeService     |<---------------------| EventBus             |
+----------------------+                      +----------------------+
| on_atom_updated(...) |
| update_row_col O(N)  |
| refresh_index(...)   |
| bump_versions(...)   |
+----------------------+
```

## Automation Sequence

```text
CogAtom.update()
  -> EventBus.publish(AtomUpdated(atom_id, new_version))

RecomputeService.on_atom_updated
  -> ScoreSet.recompute_row_col(atom_id)      # per strategy/context
  -> NeighborIndex.refresh(atom_id)
  -> EventBus.publish(ScoresUpdated(...))

CogGraph subscriber
  -> rebuild_order(PathPolicy, NeighborIndex, seen-overlay)
  -> EquivalenceCluster.recompute(policy.equivalence_rule)
  -> persist snapshot/version
```

## Concrete Example: 3 Cogs and Directed Scores

```text
UML Object Diagram (Concrete Example)

+-----------------------------+          +----------------------------------+
| p1: PathPolicy              | uses     | ssX: ScoreSet                    |
+-----------------------------+--------->+----------------------------------+
| strategy_id = "X"           |          | strategy_id = "X"                |
| direction_mode = directed   |          | context_hash = "base:A|v1"       |
| selection_key = [score desc,|          +----------------------------------+
|                  atom_id asc]|                  | 1..*
+-----------------------------+                   v
                                        +-------------------------------+
                                        | e1..e6: ScoreEntry            |
                                        +-------------------------------+
                                        | e1 A->B=0.10  e2 B->A=0.14    |
                                        | e3 A->C=0.20  e4 C->A=0.19    |
                                        | e5 B->C=0.65  e6 C->B=0.61    |
                                        +-------------------------------+

+-----------------------------+ owns 3 +-----------------------------+
| g1: CogGraph                |------->| nA/nB/nC: GraphNode         |
+-----------------------------+        +-----------------------------+
| base = A                    |        | nA.atom_id=A, layer=0       |
| node_order = [A, C, B]      |        | nC.atom_id=C, layer=1       |
| hidden_layers = {}          |        | nB.atom_id=B, layer=1       |
+-----------------------------+        +-----------------------------+
          ^  references atom_id                    | references
          |                                        v
+----------------------+   +----------------------+   +----------------------+
| a: CogAtom           |   | b: CogAtom           |   | c: CogAtom           |
+----------------------+   +----------------------+   +----------------------+
| id="A"               |   | id="B"               |   | id="C"               |
| theme="Payments"     |   | theme="Invoicing"    |   | theme="Settlement"   |
| breadth=17           |   | breadth=14           |   | breadth=16           |
| depth=2              |   | depth=3              |   | depth=2              |
| volume=8             |   | volume=9             |   | volume=10            |
+----------------------+   +----------------------+   +----------------------+

+----------------------------------------------+
| niX: NeighborIndex (for ScoreSet X)          |
+----------------------------------------------+
| from A -> [C(0.20), B(0.10)]                 |
| from B -> [C(0.65), A(0.14)]                 |
| from C -> [B(0.61), A(0.19)]                 |
+----------------------------------------------+
```

## Concrete Example: 2 Layers and Components

```text
UML Object Diagram (2 Layers, 3 Components Total)

+----------------------------------+
| g1: CogGraph                     |
+----------------------------------+
| id = "G-1"                       |
| base_cog_id = "Cog-A"            |
| node_order = [Cog-A, Cog-B]      |
+----------------+-----------------+
                 |
                 | contains
                 v
     +-----------------------+      +-----------------------+
     | n0: GraphNode         |      | n1: GraphNode         |
     +-----------------------+      +-----------------------+
     | cog_id = "Cog-A"      |      | cog_id = "Cog-B"      |
     | layer = 0             |      | layer = 1             |
     +-----------+-----------+      +-----------+-----------+
                 |                              |
                 v                              v
        +--------------------+         +--------------------+
        | Cog-A              |         | Cog-B              |
        +--------------------+         +--------------------+
        | theme = "Payments" |         | theme = "Settlement"|
        +---------+----------+         +---------+----------+
                  | owns 2                      | owns 1
          +-------+-------+                     |
          v               v                     v
+----------------+ +----------------+   +----------------+
| cA1: Component | | cA2: Component |   | cB1: Component |
+----------------+ +----------------+   +----------------+
| kind = "rule"  | | kind = "data"  |   | kind = "model" |
+----------------+ +----------------+   +----------------+

+----------------------------------+
| ssX: ScoreSet (strategy = "X")   |
+----------------------------------+
| Cog-A -> Cog-B = 0.72            |
| Cog-B -> Cog-A = 0.64            |
+----------------------------------+
```
