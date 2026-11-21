"""Read-only adapter for approved MT-DAMAGE-001 V0.2.

Preserves original source names and dependencies in canon/.
The approved model explicitly does NOT claim Gen-V-exact rounding.
"""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

SOURCE = Path(__file__).with_name("canon") / "Monster_Taimer_ENTWURF_MT_DAMAGE_001_V0_2.py"
spec = spec_from_file_location("monster_taimer_canon_damage_v02", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("Canonical damage source missing")
module = module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

DamageInput = module.v01.DamageInput
BattleConditions = module.BattleConditions
calculate_extended = module.calculate_extended
end_turn_weather_damage = module.end_turn_weather_damage

def calculate_move_damage(*, actor, target, move, random_percent=100, conditions=None,
                          attacker_ability=None, defender_ability=None):
    if move.category not in ("physical","special") or move.power < 1:
        raise ValueError("Canonical damage adapter requires a damaging move with power >= 1")
    data = DamageInput(
        level=actor.level, power=move.power,
        attack=actor.attack if move.category=="physical" else actor.sp_attack,
        defense=target.defense if move.category=="physical" else target.sp_defense,
        attack_type=move.type, attacker_types=actor.types, defender_types=target.types,
        category=move.category, random_percent=random_percent,
        burned=actor.status=="burn" and move.category=="physical",
        attacker_ability=attacker_ability, defender_ability=defender_ability,
    )
    return calculate_extended(data, conditions or BattleConditions())
