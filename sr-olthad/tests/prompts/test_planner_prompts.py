from sr_olthad.prompts.planner import PlannerLmResponseOutputData


class TestPlannerLmResponseOutputData:
    def test_parses_from_json_str(self):
        json_str = """{"new_planned_subtasks": ["mine oak logs observed in the 'north' direction", "dig around the found oak logs to better inspect the ground"]}"""
        parsed = PlannerLmResponseOutputData.model_validate_json(json_str)
        assert len(parsed.new_planned_subtasks) == 2


if __name__ == "__main__":
    test = TestPlannerLmResponseOutputData()
    test.test_parses_from_json_str()
