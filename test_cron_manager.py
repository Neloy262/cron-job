import unittest
from cron_manager import parse_schedule, SCHEDULE_MAPPINGS

class TestCronManager(unittest.TestCase):
    
    def test_parse_schedule_predefined(self):
        """Test that predefined schedule strings are correctly parsed."""
        self.assertEqual(parse_schedule("hourly"), "0 * * * *")
        self.assertEqual(parse_schedule("daily"), "0 0 * * *")
        self.assertEqual(parse_schedule("weekly"), "0 0 * * 0")
        self.assertEqual(parse_schedule("monthly"), "0 0 1 * *")
        self.assertEqual(parse_schedule("yearly"), "0 0 1 1 *")
        self.assertEqual(parse_schedule("every_5_minutes"), "*/5 * * * *")
        
    def test_parse_schedule_case_insensitive(self):
        """Test that predefined schedule strings are case insensitive."""
        self.assertEqual(parse_schedule("HOURLY"), "0 * * * *")
        self.assertEqual(parse_schedule("Daily"), "0 0 * * *")
        self.assertEqual(parse_schedule("Weekly"), "0 0 * * 0")
        
    def test_parse_schedule_custom_cron(self):
        """Test that custom cron expressions are returned as-is."""
        self.assertEqual(parse_schedule("15 10 * * *"), "15 10 * * *")
        self.assertEqual(parse_schedule("0 0 1 1 0"), "0 0 1 1 0")
        
    def test_all_schedule_mappings(self):
        """Test that all predefined schedules are in the mappings."""
        expected_schedules = ["hourly", "daily", "weekly", "monthly", "yearly", "every_5_minutes"]
        for schedule in expected_schedules:
            self.assertIn(schedule, SCHEDULE_MAPPINGS)

if __name__ == '__main__':
    unittest.main()