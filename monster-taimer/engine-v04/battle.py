"""Monster Taimer battle core V0.4 — isolated development implementation.

This module does not replace the approved MT-DAMAGE/STATUS/TURN canon.
Its Gen-V-oriented rules are intentionally partial and explicitly tested.
"""
from dataclasses import dataclass, field
from random import Random

TYPES = frozenset(("Normal","Feuer","Wasser","Elektro","Pflanze","Eis","Kampf","Gift","Boden","Flug","Psycho","Käfer","Gestein","Geist","Drache","Unlicht","Stahl","Fee"))
# Explicit subset for smoke tests; full canonical chart must be imported before release.
TYPE_OVERRIDES = {("Feuer","Pflanze"):2,("Feuer","Wasser"):0.5,("Wasser","Feuer"):2,("Wasser","Pflanze"):0.5,("Elektro","Wasser"):2,("Elektro","Boden"):0,("Normal","Geist"):0,("Kampf","Geist"):0,("Drache","Fee"):0,("Gift","Fee"):2,("Stahl","Fee"):2,("Geist","Stahl"):0.5,("Unlicht","Stahl"):0.5}

@dataclass(frozen=True)
class Move:
    id: str
    name: str
    type: str
    category: str
    power: int
    accuracy: int | None
    max_pp: int
    priority: int = 0
    effect: str = "damage"
    chance: int = 0

    def __post_init__(self):
        if not self.id or self.type not in TYPES or self.category not in ("physical","special","status"):
            raise ValueError("Invalid move metadata")
        if self.power < 0 or not 1 <= self.max_pp <= 64 or not -7 <= self.priority <= 7:
            raise ValueError("Invalid move power/PP/priority")
        if self.accuracy is not None and not 1 <= self.accuracy <= 100:
            raise ValueError("Invalid accuracy")
        if not 0 <= self.chance <= 100 or self.effect not in ("damage","burn","poison","heal"):
            raise ValueError("Unsupported effect or chance")
        if self.category == "status" and self.effect == "damage":
            raise ValueError("Status move cannot use damage effect")

@dataclass
class Slot:
    move: Move
    pp: int

    def __post_init__(self):
        if not 0 <= self.pp <= self.move.max_pp:
            raise ValueError("Invalid PP")

@dataclass
class Monster:
    name: str
    types: tuple[str, ...]
    level: int
    max_hp: int
    hp: int
    attack: int
    defense: int
    sp_attack: int
    sp_defense: int
    speed: int
    moves: dict[str, Slot]
    status: str = "none"

    def __post_init__(self):
        if not 1 <= self.level <= 100 or not 1 <= len(self.types) <= 2 or len(set(self.types)) != len(self.types) or not set(self.types) <= TYPES:
            raise ValueError("Invalid level/types")
        if self.max_hp < 1 or not 0 <= self.hp <= self.max_hp:
            raise ValueError("Invalid HP")
        if min(self.attack,self.defense,self.sp_attack,self.sp_defense,self.speed) < 1:
            raise ValueError("Stats must be positive")
        if len(self.moves) > 4 or any(k != v.move.id for k,v in self.moves.items()):
            raise ValueError("Invalid move slots")

@dataclass
class Battle:
    a: Monster
    b: Monster
    seed: int = 0
    turn: int = 0
    log: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if self.a is self.b:
            raise ValueError("Distinct combatants required")
        self.rng = Random(self.seed)

    def emit(self, kind, **fields):
        self.log.append({"turn":self.turn,"kind":kind,**fields})

    def target(self, actor):
        return self.b if actor is self.a else self.a

    def damage(self, actor, target, move):
        atk = actor.attack if move.category == "physical" else actor.sp_attack
        defense = target.defense if move.category == "physical" else target.sp_defense
        base = ((2 * actor.level // 5 + 2) * move.power * atk // defense) // 50 + 2
        effectiveness = 1.0
        for t in target.types:
            effectiveness *= TYPE_OVERRIDES.get((move.type,t),1.0)
        if effectiveness == 0:
            return 0
        stab = 1.5 if move.type in actor.types else 1.0
        return max(1,int(base * stab * effectiveness * self.rng.randint(85,100)/100))

    def action(self, actor, move_id):
        target = self.target(actor)
        slot = actor.moves[move_id]
        move = slot.move
        if actor.hp == 0 or target.hp == 0:
            return
        if slot.pp == 0:
            self.emit("no_pp",actor=actor.name,move=move_id)
            return
        slot.pp -= 1
        self.emit("used",actor=actor.name,move=move_id,pp=slot.pp)
        if move.accuracy is not None and self.rng.randint(1,100) > move.accuracy:
            self.emit("miss",actor=actor.name,move=move_id)
            return
        if move.effect == "heal":
            amount = min(actor.max_hp-actor.hp,max(1,actor.max_hp//2))
            actor.hp += amount
            self.emit("heal",actor=actor.name,amount=amount)
            return
        if move.category == "status":
            if target.status == "none":
                target.status = move.effect
                self.emit("status",target=target.name,status=move.effect)
            return
        amount = min(target.hp,self.damage(actor,target,move))
        target.hp -= amount
        self.emit("damage",actor=actor.name,target=target.name,amount=amount)
        if target.hp == 0:
            self.emit("faint",target=target.name)
            return
        if move.effect in ("burn","poison") and target.status == "none" and self.rng.randrange(100) < move.chance:
            target.status = move.effect
            self.emit("status",target=target.name,status=move.effect)

    def play_turn(self, move_a, move_b):
        if self.a.hp == 0 or self.b.hp == 0:
            raise RuntimeError("Battle finished")
        commands = [(self.a,move_a),(self.b,move_b)]
        # Validate both commands before mutating the turn counter or PP.
        for actor,mid in commands:
            if mid not in actor.moves:
                raise ValueError(f"Unknown move: {mid}")
        self.turn += 1
        # Tie randomness is consumed only for actual priority/speed ties.
        first,second = commands
        def key(cmd):
            actor,mid=cmd
            return (actor.moves[mid].move.priority,actor.speed//4 if actor.status=="paralysis" else actor.speed)
        if key(second)>key(first) or (key(second)==key(first) and self.rng.randrange(2)==1):
            first,second=second,first
        for actor,mid in (first,second):
            if actor.hp and self.target(actor).hp:
                self.action(actor,mid)
        for actor in (self.a,self.b):
            if actor.hp and actor.status in ("burn","poison"):
                amount=min(actor.hp,max(1,actor.max_hp//8))
                actor.hp-=amount
                self.emit("residual",target=actor.name,amount=amount)
                if actor.hp==0:
                    self.emit("faint",target=actor.name)
        if not self.a.hp and not self.b.hp:
            return "draw"
        if not self.a.hp:
            return self.b.name
        if not self.b.hp:
            return self.a.name
        return None
