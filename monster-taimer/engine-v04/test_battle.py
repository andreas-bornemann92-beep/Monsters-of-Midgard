"""Standard-library regression tests for the isolated battle engine."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("battle",Path(__file__).with_name("battle.py"))
battle = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = battle
spec.loader.exec_module(battle)
Move,Slot,Monster,Battle = battle.Move,battle.Slot,battle.Monster,battle.Battle

def monster(name, speed=50, hp=100, types=("Feuer",), power=40, effect="damage", category="special", accuracy=100):
    move=Move("m1","Test",types[0],category,power,accuracy,10,effect=effect,chance=100)
    return Monster(name,types,50,hp,hp,100,100,100,100,speed,{"m1":Slot(move,10)})

class BattleTests(unittest.TestCase):
    def test_damage_and_pp(self):
        a,b=monster("A"),monster("B",speed=30)
        game=Battle(a,b,seed=4)
        game.play_turn("m1","m1")
        self.assertLess(a.hp,100)
        self.assertLess(b.hp,100)
        self.assertEqual(a.moves["m1"].pp,9)
        self.assertEqual(b.moves["m1"].pp,9)

    def test_seed_reproducibility(self):
        def run():
            g=Battle(monster("A"),monster("B"),seed=12)
            g.play_turn("m1","m1")
            return g.log
        self.assertEqual(run(),run())

    def test_invalid_move_does_not_mutate(self):
        g=Battle(monster("A"),monster("B"))
        with self.assertRaises(ValueError):
            g.play_turn("m1","missing")
        self.assertEqual(g.turn,0)
        self.assertEqual(g.a.moves["m1"].pp,10)

    def test_priority(self):
        a,b=monster("A",speed=10),monster("B",speed=100)
        old=a.moves["m1"].move
        a.moves["m1"].move=Move(old.id,old.name,old.type,old.category,old.power,old.accuracy,old.max_pp,priority=1)
        g=Battle(a,b)
        g.play_turn("m1","m1")
        self.assertEqual(next(x["actor"] for x in g.log if x["kind"]=="used"),"A")

    def test_healing_capped(self):
        a,b=monster("A",effect="heal",category="status",power=0),monster("B",power=0)
        a.hp=90
        g=Battle(a,b)
        g.play_turn("m1","m1")
        self.assertEqual(a.hp,100)

    def test_status_residual(self):
        a,b=monster("A",power=0),monster("B",power=0)
        a.status="burn"
        g=Battle(a,b)
        g.play_turn("m1","m1")
        self.assertEqual(a.hp,88)

    def test_immune_damage(self):
        a=monster("A",types=("Elektro",))
        b=monster("B",types=("Boden",))
        g=Battle(a,b)
        g.play_turn("m1","m1")
        self.assertEqual(b.hp,100)

    def test_invalid_effect_rejected(self):
        with self.assertRaises(ValueError):
            Move("x","X","Feuer","special",50,100,10,effect="unknown")

    def test_faint_prevents_second_action(self):
        a,b=monster("A",speed=100,power=1000),monster("B",speed=10)
        g=Battle(a,b)
        winner=g.play_turn("m1","m1")
        self.assertEqual(winner,"A")
        self.assertEqual(b.moves["m1"].pp,10)

if __name__=="__main__":
    unittest.main()
