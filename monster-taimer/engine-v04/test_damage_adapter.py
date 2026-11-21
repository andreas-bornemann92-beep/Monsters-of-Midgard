"""Regression checks against approved MT-DAMAGE-001 V0.2 calculations."""
import unittest
from battle import Move, Monster, Slot
from damage_adapter import calculate_move_damage, BattleConditions

def sample():
    move=Move("fire","Flame","Feuer","special",80,100,10)
    a=Monster("A",("Feuer",),50,100,100,120,100,120,100,80,{"fire":Slot(move,10)})
    b=Monster("B",("Pflanze",),50,100,100,100,100,100,100,60,{"fire":Slot(move,10)})
    return a,b,move

class CanonDamageTests(unittest.TestCase):
    def test_canonical_normal(self):
        a,b,m=sample()
        self.assertEqual(calculate_move_damage(actor=a,target=b,move=m).damage,132)

    def test_sun(self):
        a,b,m=sample()
        self.assertEqual(calculate_move_damage(actor=a,target=b,move=m,conditions=BattleConditions(weather="sun")).damage,198)

    def test_rain(self):
        a,b,m=sample()
        self.assertEqual(calculate_move_damage(actor=a,target=b,move=m,conditions=BattleConditions(weather="rain")).damage,66)

    def test_light_screen(self):
        a,b,m=sample()
        self.assertEqual(calculate_move_damage(actor=a,target=b,move=m,conditions=BattleConditions(screen="light_screen")).damage,66)

    def test_type_immunity(self):
        a,b,m=sample()
        electric=Move("electric","Bolt","Elektro","special",80,100,10)
        b.types=("Boden",)
        self.assertEqual(calculate_move_damage(actor=a,target=b,move=electric).damage,0)

    def test_reject_status_move(self):
        a,b,m=sample()
        status=Move("heal","Heal","Normal","status",0,None,10,effect="heal")
        with self.assertRaises(ValueError):
            calculate_move_damage(actor=a,target=b,move=status)

if __name__=="__main__":
    unittest.main()
