"""MT-DAMAGE-001 V0.1: isolated, deliberately limited Gen-V damage draft.

Supports a subset of ordinary single-hit damaging moves. Not an exact complete
Generation-V damage implementation. Canon dependencies are read, not modified.
"""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('mt_canon_battle', ROOT / 'Monster_Taimer_KANON_MT_BATTLE_001_V0_1.py')
canon = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = canon
spec.loader.exec_module(canon)

@dataclass(frozen=True)
class DamageInput:
    level: int
    power: int
    attack: int
    defense: int
    attack_type: str
    attacker_types: tuple[str, ...]
    defender_types: tuple[str, ...]
    category: str = 'physical'
    random_percent: int = 100
    critical: bool = False
    burned: bool = False
    attacker_ability: str | None = None
    defender_ability: str | None = None

@dataclass(frozen=True)
class DamageResult:
    base_damage: int
    damage: int
    type_multiplier: Fraction
    stab_multiplier: Fraction
    random_percent: int
    critical: bool
    limitations: tuple[str, ...]

LIMITATIONS = (
    'Restricted ordinary single-hit move model; not a full Gen-V damage engine',
    'Integer rounding order for all Gen-V modifier chains not independently verified',
    'Weather, items, screens, targets, spread moves, special moves and many abilities unsupported',
    'Burn and critical handling are provisional; exact Gen-V interactions require reference tests',
)

def calculate_damage(d: DamageInput) -> DamageResult:
    for field in ('level','power','attack','defense','random_percent'):
        if type(getattr(d, field)) is not int:
            raise ValueError(f'{field} must be an integer')
    if not 1 <= d.level <= 100 or not 1 <= d.power <= 250:
        raise ValueError('Invalid level or power for this draft')
    if d.attack < 1 or d.defense < 1:
        raise ValueError('Effective attack and defense must be positive')
    if not 85 <= d.random_percent <= 100:
        raise ValueError('Random roll must be 85..100')
    if d.category not in ('physical','special'):
        raise ValueError('Unsupported category')
    if d.burned and d.category != 'physical':
        raise ValueError('Burned flag only supported for physical category in this draft')
    if d.burned and d.attacker_ability is not None:
        raise NotImplementedError('Burn/ability interactions not modeled')
    interaction = canon.calculate_type_result(
        d.attack_type, d.attacker_types, d.defender_types,
        attacker_ability=d.attacker_ability,
        defender_ability=d.defender_ability,
    )
    base = (((2 * d.level // 5 + 2) * d.power * d.attack // d.defense) // 50) + 2
    if interaction.type_multiplier == 0:
        return DamageResult(base, 0, interaction.type_multiplier, interaction.stab_multiplier,
                            d.random_percent, d.critical, LIMITATIONS)
    # Simplified explicit modifier order; this is NOT asserted as Gen-V exact.
    damage = base
    if d.critical:
        damage *= 2
    if d.burned:
        damage //= 2
    damage = damage * d.random_percent // 100
    damage = damage * interaction.stab_multiplier.numerator // interaction.stab_multiplier.denominator
    damage = damage * interaction.type_multiplier.numerator // interaction.type_multiplier.denominator
    return DamageResult(base, max(1,damage), interaction.type_multiplier,
                        interaction.stab_multiplier,d.random_percent,d.critical,LIMITATIONS)

if __name__ == '__main__':
    test = DamageInput(50,80,120,100,'Feuer',('Feuer',),('Pflanze',))
    assert calculate_damage(test).base_damage == 44
    assert calculate_damage(test).damage == 132
    assert calculate_damage(DamageInput(**{**test.__dict__,'random_percent':85})).damage == 110
    assert calculate_damage(DamageInput(**{**test.__dict__,'critical':True})).damage == 264
    assert calculate_damage(DamageInput(**{**test.__dict__,'burned':True})).damage == 66
    assert calculate_damage(DamageInput(50,80,120,100,'Elektro',('Elektro',),('Wasser','Boden'))).damage == 0
    assert calculate_damage(DamageInput(50,80,120,100,'Boden',('Boden',),('Feuer',),defender_ability='Levitate')).damage == 0
    assert calculate_damage(DamageInput(50,80,120,100,'Boden',('Boden',),('Feuer',),defender_ability='Levitate',attacker_ability='Mold Breaker')).damage > 0
    assert calculate_damage(DamageInput(50,80,120,100,'Fee',('Fee',),('Drache','Unlicht'))).damage == 264
    assert calculate_damage(DamageInput(50,80,120,100,'Normal',('Normal',),('Geist',),attacker_ability='Scrappy')).damage > 0
    print('10 isolated damage-model tests passed')