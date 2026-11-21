"""MT-DAMAGE-001 V0.2: provisional weather/screen extension of V0.1.

This is NOT a Gen-V-exact implementation. Existing canonical files are not modified.
"""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import importlib.util, sys

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('mt_damage_v01',ROOT/'Monster_Taimer_ENTWURF_MT_DAMAGE_001_V0_1.py')
v01=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=v01
spec.loader.exec_module(v01)

@dataclass(frozen=True)
class BattleConditions:
    weather: str='none'  # none, sun, rain, sandstorm, hail
    screen: str='none'   # none, reflect, light_screen
    critical: bool=False
    doubles: bool=False
    weather_suppressed: bool=False

@dataclass(frozen=True)
class ExtendedResult:
    base_damage: int
    damage: int
    type_multiplier: Fraction
    stab_multiplier: Fraction
    weather_multiplier: Fraction
    screen_multiplier: Fraction
    note: str='PROVISIONAL: modifier rounding/ordering not Gen-V verified'

def calculate_extended(d: v01.DamageInput, c: BattleConditions)->ExtendedResult:
    if c.weather not in ('none','sun','rain','sandstorm','hail'):
        raise ValueError('Unknown weather')
    if c.screen not in ('none','reflect','light_screen'):
        raise ValueError('Unknown screen')
    if d.critical != c.critical:
        raise ValueError('Critical flag must agree in both inputs')
    # Existing module validates inputs and implements canonical type/ability interactions.
    result=v01.calculate_damage(d)
    if result.type_multiplier==0:
        return ExtendedResult(result.base_damage,0,result.type_multiplier,result.stab_multiplier,Fraction(1),Fraction(1))
    weather=Fraction(1)
    if not c.weather_suppressed:
        if (c.weather=='sun' and d.attack_type=='Feuer') or (c.weather=='rain' and d.attack_type=='Wasser'):
            weather=Fraction(3,2)
        elif (c.weather=='sun' and d.attack_type=='Wasser') or (c.weather=='rain' and d.attack_type=='Feuer'):
            weather=Fraction(1,2)
    screen=Fraction(1)
    if not c.critical and ((c.screen=='reflect' and d.category=='physical') or (c.screen=='light_screen' and d.category=='special')):
        screen=Fraction(2,3) if c.doubles else Fraction(1,2)
    # Simplified final application; Gen-V precise chain is deliberately not claimed.
    damage=result.damage*weather.numerator//weather.denominator
    damage=damage*screen.numerator//screen.denominator
    return ExtendedResult(result.base_damage,max(1,damage),result.type_multiplier,result.stab_multiplier,weather,screen)

def end_turn_weather_damage(max_hp:int,types:tuple[str,...],weather:str,immune:bool=False)->int:
    """Provisional end-turn weather chip; abilities/items passed as immune flag."""
    if type(max_hp) is not int or max_hp<1:
        raise ValueError('max_hp must be positive integer')
    if weather not in ('none','sun','rain','sandstorm','hail'):
        raise ValueError('Unknown weather')
    if immune:
        return 0
    if weather=='sandstorm' and not any(t in ('Gestein','Boden','Stahl') for t in types):
        return max(1,max_hp//16)
    if weather=='hail' and 'Eis' not in types:
        return max(1,max_hp//16)
    return 0

if __name__=='__main__':
    d=v01.DamageInput(50,80,120,100,'Feuer',('Feuer',),('Pflanze',))
    assert calculate_extended(d,BattleConditions()).damage==132
    assert calculate_extended(d,BattleConditions(weather='sun')).damage==198
    assert calculate_extended(d,BattleConditions(weather='rain')).damage==66
    assert calculate_extended(d,BattleConditions(screen='reflect')).damage==66
    assert calculate_extended(d,BattleConditions(screen='light_screen')).damage==132
    assert calculate_extended(d,BattleConditions(screen='reflect',doubles=True)).damage==88
    dc=v01.DamageInput(**{**d.__dict__,'critical':True})
    assert calculate_extended(dc,BattleConditions(screen='reflect',critical=True)).damage==264
    di=v01.DamageInput(50,80,120,100,'Elektro',('Elektro',),('Wasser','Boden'))
    assert calculate_extended(di,BattleConditions(weather='sun')).damage==0
    assert end_turn_weather_damage(160,('Feuer',),'sandstorm')==10
    assert end_turn_weather_damage(160,('Stahl',),'sandstorm')==0
    assert end_turn_weather_damage(160,('Eis',),'hail')==0
    assert end_turn_weather_damage(160,('Wasser',),'hail')==10
    print('12 provisional extension tests passed')