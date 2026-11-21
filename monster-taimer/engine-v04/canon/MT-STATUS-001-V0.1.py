"""Monster Taimer MT-STATUS-001 V0.1 – unapproved Gen-V-oriented status core.

Deterministic core with injected RNG; not a full battle-turn scheduler.
Existing canon modules are not modified.
"""
from dataclasses import dataclass
from enum import Enum
from random import Random

class Status(str, Enum):
    NONE = 'none'
    PARALYSIS = 'paralysis'
    BURN = 'burn'
    POISON = 'poison'
    TOXIC = 'toxic'
    SLEEP = 'sleep'
    FREEZE = 'freeze'

@dataclass
class StatusState:
    status: Status = Status.NONE
    toxic_counter: int = 0
    sleep_turns_remaining: int = 0

    def inflict(self, status: Status, *, sleep_turns: int | None = None) -> bool:
        """Applies status if empty; immunity is checked by an external rules layer.

        Sleep duration is supplied by the caller, not generated here.
        """
        if not isinstance(status, Status):
            raise ValueError('Unknown status')
        if self.status != Status.NONE or status == Status.NONE:
            return False
        if status == Status.SLEEP:
            if type(sleep_turns) is not int or sleep_turns < 1:
                raise ValueError('Sleep requires positive duration')
        elif sleep_turns is not None:
            raise ValueError('Sleep duration only valid for sleep')
        self.status = status
        self.toxic_counter = 0
        self.sleep_turns_remaining = sleep_turns if status == Status.SLEEP else 0
        return True

    def cure(self) -> None:
        self.status = Status.NONE
        self.toxic_counter = 0
        self.sleep_turns_remaining = 0

    def switch_out(self) -> None:
        """Gen-V-oriented: toxic counter resets on switch; status remains."""
        self.toxic_counter = 0

    def can_act(self, rng: Random, *, thawing_move: bool = False) -> tuple[bool, str]:
        """Checks major status only; move legality and other effects are external."""
        if self.status == Status.SLEEP:
            self.sleep_turns_remaining = max(0, self.sleep_turns_remaining - 1)
            if self.sleep_turns_remaining == 0:
                self.cure()
                return True, 'woke_up'
            return False, 'asleep'
        if self.status == Status.FREEZE:
            if thawing_move or rng.randrange(100) < 20:
                self.cure()
                return True, 'thawed'
            return False, 'frozen'
        if self.status == Status.PARALYSIS and rng.randrange(100) < 25:
            return False, 'fully_paralyzed'
        return True, 'ok'

    def end_turn_damage(self, max_hp: int) -> int:
        """Status-only damage; immunities, Magic Guard, weather, fainting external."""
        if type(max_hp) is not int or max_hp < 1:
            raise ValueError('max_hp must be positive')
        if self.status in (Status.BURN, Status.POISON):
            return max(1, max_hp // 8)
        if self.status == Status.TOXIC:
            self.toxic_counter = min(15, self.toxic_counter + 1)
            return max(1, max_hp * self.toxic_counter // 16)
        return 0


def paralysis_speed(speed: int, state: StatusState, *, exempt: bool = False) -> int:
    if type(speed) is not int or speed < 1:
        raise ValueError('speed must be positive')
    return max(1, speed // 4) if state.status == Status.PARALYSIS and not exempt else speed


def self_test() -> None:
    s = StatusState()
    assert s.inflict(Status.TOXIC)
    assert not s.inflict(Status.BURN)
    assert [s.end_turn_damage(160) for _ in range(3)] == [10, 20, 30]
    s.switch_out()
    assert s.end_turn_damage(160) == 10
    s.cure()
    assert s.end_turn_damage(160) == 0
    assert s.inflict(Status.BURN)
    assert s.end_turn_damage(160) == 20
    s.cure()
    assert s.inflict(Status.POISON)
    assert s.end_turn_damage(160) == 20
    s.cure()
    assert s.inflict(Status.PARALYSIS)
    assert paralysis_speed(100, s) == 25
    assert paralysis_speed(100, s, exempt=True) == 100
    assert s.can_act(Random(1))[0] in (True, False)
    s.cure()
    assert s.inflict(Status.SLEEP, sleep_turns=2)
    assert s.can_act(Random(0)) == (False, 'asleep')
    assert s.can_act(Random(0)) == (True, 'woke_up')
    assert s.status == Status.NONE
    assert s.inflict(Status.FREEZE)
    assert s.can_act(Random(0), thawing_move=True) == (True, 'thawed')
    try:
        StatusState().inflict(Status.SLEEP)
        raise AssertionError('Sleep duration validation failed')
    except ValueError:
        pass
    try:
        StatusState().end_turn_damage(0)
        raise AssertionError('HP validation failed')
    except ValueError:
        pass

if __name__ == '__main__':
    self_test()
    print('MT-STATUS-001 V0.1: 16 status checks passed')