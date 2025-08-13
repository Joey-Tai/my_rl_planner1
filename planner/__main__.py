import os.path
import os

from commonroad.common.solution import Solution, CommonRoadSolutionWriter

# Load planner module
from planner import motion_planner, motion_planner_interactive
from iterator import scenario_iterator_interactive, scenario_iterator_non_interactive


def save_solution(solution: Solution, path: str) -> None:
    """
    Save the given solution to the given path.
    """
    return CommonRoadSolutionWriter(solution).write_to_file(
        output_path=path,
        overwrite=True,
        pretty=True
    )


# Run Main Process
if __name__ == "__main__":
    #Original directory, please recover after finished
    # scenario_dir = "/commonroad/scenarios"
    # solution_dir = "/commonroad/solutions"

    #Temporary directory for testing
    home = os.path.expanduser("~")
    scenario_dir = os.path.join(home, "commonroad", "scenarios")
    solution_dir = os.path.join(home, "commonroad", "solutions")

    # solve all non-interactive scenarios
    for scenario, planning_problem_set in scenario_iterator_non_interactive(scenario_dir):
        print(f"Processing scenario {str(scenario.scenario_id)} ...")
        solution = motion_planner(scenario, solution_dir)

    # solve all interactive scenarios
    for scenario_path in scenario_iterator_interactive(scenario_dir):
        print(f"Processing scenario {os.path.basename(scenario_path)} ...")
        solution = motion_planner_interactive(scenario_path, solution_dir)
