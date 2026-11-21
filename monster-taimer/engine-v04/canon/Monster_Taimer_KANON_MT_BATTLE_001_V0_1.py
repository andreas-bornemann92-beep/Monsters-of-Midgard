"""Monster Taimer MT-BATTLE-001: canonical Gen-V type/STAB/ability interaction layer.
Not a full Generation V damage calculator. Uses canonical MT-TYPES-001 matrix.
"""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import json

TYPE_FILE = Path(__file__).with_name('Monster_Taimer_KANON_MT_TYPES_001_V0_1.json')
DATA = json.loads(TYPE_FILE.read_text(encoding='utf-8'))
CHART = DATA['attack_to_defense']
TYPES = frozenset(DATA['types'])

@dataclass(frozen=True)
class TypeResult:
    attack_type: str
    defender_types: tuple[str, ...]
    type_multiplier: Fraction
    stab_multiplier: Fraction
    total_multiplier: Fraction
    blocked_by: str | None = None


def calculate_type_result(attack_type: str, attacker_types: tuple[str, ...],
                          defender_types: tuple[str, ...], *,
                          attacker_ability: str | None = None,
                          defender_ability: str | None = None,
                          move_is_damaging: bool = True,
                          ignore_defender_ability: bool = False) -> TypeResult:
    """Only explicitly supported abilities are implemented; other abilities are rejected.

    Gen-V relevant effects: Adaptability STAB=2; Levitate grants Ground immunity;
    Scrappy lets Normal/Fighting hit Ghost; Mold Breaker bypasses Levitate.
    Does not resolve weather, items, Wonder Guard, move-specific type exceptions,
    damage rounding, or other ability effects.
    """
    for t in (attack_type, *attacker_types, *defender_types):
        if t not in TYPES:
            raise ValueError(f'Unknown type: {t}')
    if not 1 <= len(attacker_types) <= 2 or len(set(attacker_types)) != len(attacker_types):
        raise ValueError('Attacker must have one or two distinct types')
    if not 1 <= len(defender_types) <= 2 or len(set(defender_types)) != len(defender_types):
        raise ValueError('Defender must have one or two distinct types')
    if attacker_ability not in (None, 'Adaptability', 'Scrappy', 'Mold Breaker'):
        raise NotImplementedError('Attacker ability not supported')
    if defender_ability not in (None, 'Levitate'):
        raise NotImplementedError('Defender ability not supported')

    multiplier = Fraction(1)
    for t in defender_types:
        part = Fraction(str(CHART[attack_type][t]))
        if t == 'Geist' and attack_type in ('Normal', 'Kampf') and attacker_ability == 'Scrappy':
            part = Fraction(1)
        multiplier *= part

    bypass = ignore_defender_ability or attacker_ability == 'Mold Breaker'
    blocked_by = None
    if (defender_ability == 'Levitate' and attack_type == 'Boden'
            and move_is_damaging and not bypass):
        multiplier = Fraction(0)
        blocked_by = 'Levitate'

    stab = Fraction(1)
    if move_is_damaging and attack_type in attacker_types:
        stab = Fraction(2) if attacker_ability == 'Adaptability' else Fraction(3, 2)
    return TypeResult(attack_type, defender_types, multiplier, stab,
                      multiplier * stab, blocked_by)


if __name__ == '__main__':
    cases = [
        (('Boden', ('Feuer',), ('Feuer','Stahl')), Fraction(4)),
        (('Elektro', ('Elektro',), ('Wasser','Boden')), Fraction(0)),
        (('Fee', ('Fee',), ('Drache','Unlicht')), Fraction(4)),
        (('Geist', ('Geist',), ('Stahl',)), Fraction(1,2)),
    ]
    for args, expected in cases:
        assert calculate_type_result(*args).type_multiplier == expected
    assert calculate_type_result('Feuer', ('Feuer',), ('Pflanze',)).total_multiplier == 3
    assert calculate_type_result('Feuer', ('Feuer',), ('Pflanze',), attacker_ability='Adaptability').total_multiplier == 4
    assert calculate_type_result('Boden', ('Boden',), ('Feuer',), defender_ability='Levitate').total_multiplier == 0
    assert calculate_type_result('Boden', ('Boden',), ('Feuer',), defender_ability='Levitate', attacker_ability='Mold Breaker').total_multiplier == 3
    assert calculate_type_result('Normal', ('Normal',), ('Geist',), attacker_ability='Scrappy').total_multiplier == Fraction(3,2)
    assert calculate_type_result('Normal', ('Normal',), ('Geist',)).total_multiplier == 0
    print('10 interaction tests passed')