"""Tests of the unmodified approved status source through its adapter."""
import unittest
from random import Random
from status_adapter import Status, StatusState, paralysis_speed, state_from_string

class CanonStatusTests(unittest.TestCase):
    def test_poison_and_burn(self):
        s=StatusState()
        self.assertTrue(s.inflict(Status.BURN))
        self.assertEqual(s.end_turn_damage(160),20)
        self.assertFalse(s.inflict(Status.POISON))
        s.cure()
        self.assertTrue(s.inflict(Status.POISON))
        self.assertEqual(s.end_turn_damage(160),20)

    def test_toxic_scaling_and_switch(self):
        s=state_from_string("toxic")
        self.assertEqual([s.end_turn_damage(160) for _ in range(3)],[10,20,30])
        s.switch_out()
        self.assertEqual(s.end_turn_damage(160),10)

    def test_sleep_duration(self):
        s=StatusState()
        self.assertTrue(s.inflict(Status.SLEEP,sleep_turns=2))
        self.assertEqual(s.can_act(Random(0)),(False,"asleep"))
        self.assertEqual(s.can_act(Random(0)),(True,"woke_up"))

    def test_paralysis_speed(self):
        s=state_from_string("paralysis")
        self.assertEqual(paralysis_speed(100,s),25)
        self.assertEqual(paralysis_speed(100,s,exempt=True),100)

    def test_invalid_sleep_adapter(self):
        with self.assertRaises(ValueError):
            state_from_string("sleep")

    def test_unknown_status(self):
        with self.assertRaises(ValueError):
            state_from_string("invented")

if __name__=="__main__":
    unittest.main()
