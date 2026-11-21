"""Integrated battle V0.4 draft, using approved damage and status adapters.

Keeps battle.py untouched for backward compatibility. The canonical models
remain partial; move legality, status immunities and full turn sequencing are
not yet Gen-V complete.
"""
from battle import Battle
from damage_adapter import calculate_move_damage, BattleConditions
from status_adapter import Status, state_from_string, paralysis_speed

class IntegratedBattle(Battle):
    def __post_init__(self):
        super().__post_init__()
        self.status_states = {
            id(actor): state_from_string(actor.status)
            for actor in (self.a, self.b)
        }
        self.conditions = BattleConditions()

    def state(self, actor):
        return self.status_states[id(actor)]

    def damage(self, actor, target, move):
        result = calculate_move_damage(
            actor=actor, target=target, move=move,
            random_percent=self.rng.randint(85,100),
            conditions=self.conditions,
        )
        return result.damage

    def action(self, actor, move_id):
        if actor.hp <= 0 or self.target(actor).hp <= 0:
            return
        allowed, reason = self.state(actor).can_act(self.rng)
        actor.status = self.state(actor).status.value
        if not allowed:
            self.emit("blocked",actor=actor.name,reason=reason)
            return
        if reason in ("woke_up","thawed"):
            self.emit("recovered",actor=actor.name,reason=reason)
        previous_target_status = self.target(actor).status
        super().action(actor, move_id)
        target = self.target(actor)
        if target.status != previous_target_status:
            applied = self.state(target).inflict(Status(target.status))
            if not applied:
                target.status = self.state(target).status.value

    def play_turn(self, move_a, move_b):
        if self.a.hp == 0 or self.b.hp == 0:
            raise RuntimeError("Battle finished")
        commands = [(self.a,move_a),(self.b,move_b)]
        for actor,mid in commands:
            if mid not in actor.moves:
                raise ValueError(f"Unknown move: {mid}")
        self.turn += 1
        first,second = commands
        def key(cmd):
            actor,mid=cmd
            return (actor.moves[mid].move.priority,paralysis_speed(actor.speed,self.state(actor)))
        if key(second)>key(first) or (key(second)==key(first) and self.rng.randrange(2)==1):
            first,second=second,first
        for actor,mid in (first,second):
            if actor.hp and self.target(actor).hp:
                self.action(actor,mid)
        for actor in (self.a,self.b):
            if actor.hp:
                amount=min(actor.hp,self.state(actor).end_turn_damage(actor.max_hp))
                if amount:
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
