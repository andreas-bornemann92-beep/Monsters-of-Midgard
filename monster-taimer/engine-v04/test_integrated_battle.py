"""Integration regressions for the opt-in canonical battle subclass."""
import unittest
from battle import Move, Monster, Slot
from integrated_battle import IntegratedBattle

def build(name, types=("Feuer",), speed=50, power=80, effect="damage", category="special"):
    m=Move("m","Move",types[0],category,power,100,10,effect=effect,chance=100)
    return Monster(name,types,50,160,160,120,100,120,100,speed,{"m":Slot(m,10)})

class IntegratedBattleTests(unittest.TestCase):
    def test_damage_uses_canonical_calculator(self):
        a=build("A")
        b=build("B",types=("Pflanze",),speed=10)
        game=IntegratedBattle(a,b,seed=7)
        game.play_turn("m","m")
        self.assertTrue(any(x["kind"]=="damage" and x["actor"]=="A" and x["amount"]>0 for x in game.log))

    def test_poison_residual(self):
        a=build("A",power=0,effect="heal",category="status")
        b=build("B",power=0,effect="heal",category="status")
        a.status="poison"
        game=IntegratedBattle(a,b)
        game.play_turn("m","m")
        self.assertEqual(a.hp,140)

    def test_toxic_scaling(self):
        a=build("A",power=0,effect="heal",category="status")
        b=build("B",power=0,effect="heal",category="status")
        a.status="toxic"
        game=IntegratedBattle(a,b)
        game.play_turn("m","m")
        game.play_turn("m","m")
        self.assertEqual([e["amount"] for e in game.log if e["kind"]=="residual" and e["target"]=="A"],[10,20])

    def test_status_infliction_sync(self):
        a=build("A",effect="burn",power=0,category="status")
        b=build("B",power=0,effect="heal",category="status",speed=10)
        game=IntegratedBattle(a,b)
        game.play_turn("m","m")
        self.assertEqual(b.status,"burn")
        self.assertEqual(game.state(b).status.value,"burn")
        self.assertEqual(b.hp,140)

    def test_immune_damage(self):
        a=build("A",types=("Elektro",))
        b=build("B",types=("Boden",),power=0)
        game=IntegratedBattle(a,b)
        game.play_turn("m","m")
        self.assertEqual(b.hp,160)

if __name__=="__main__":
    unittest.main()
