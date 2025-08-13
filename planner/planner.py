from commonroad.common.solution import CommonRoadSolutionReader
from commonroad.common.solution import VehicleType, VehicleModel, CostFunction
from commonroad.scenario.scenario import Scenario

from simulation.simulations import simulate_with_planner
from simulation.utility import save_solution


def motion_planner(scenario: Scenario, solution_dir: str):
    """
    Motion planner that takes a scenario and outputs a solution.

    Drivability Checker toolbox (`commonroad_dc`) can be used
    here to make sure the solution is feasible and does not
    collide with other scenario
    elements.
    """

    # Implement your own planner here

    # As a template, load already existing dummy solution and return
    solution_path = "/commonroad/dummy_solutions/dummy_solution_KS2:SM1:CHN_Sha-4_1_T-1:2018b.xml"
    return CommonRoadSolutionReader.open(solution_path)


def motion_planner_interactive(scenario_path: str, solution_dir: str):
    """
    Motion planner that takes the path of the folder with an interactive scenario folder and saves a solution.

    Drivability Checker toolbox (`commonroad_dc`) can be used here to make sure the solution is feasible and does not
    collide with other scenario elements.
    """
    # a sample code
    vehicle_type = VehicleType.FORD_ESCORT
    vehicle_model = VehicleModel.KS
    cost_function = CostFunction.TR1

    # option 1: run your motion planner with closed-loop simulation
    # Implement your own planner in the simulate_scenario function within simulation/simulations.py.
    # You can Implement your own planner without saving videos
    scenario_with_planner, pps, ego_vehicles_planner = simulate_with_planner(interactive_scenario_path=scenario_path)
    # You can also Implement your own planner with saving videos
    # scenario_with_planner, pps, ego_vehicles_planner = simulate_with_planner(interactive_scenario_path=scenario_path, output_folder_path=solution_dir, create_video=True)

    # save the planned trajectory to solution file
    if scenario_with_planner:
        print("Saving solutions..")
        save_solution(scenario_with_planner, pps, ego_vehicles_planner, vehicle_type, vehicle_model, cost_function,
                      solution_dir, overwrite=True)

        # comment out to return the solution file
        # name_scenario = scenario_path.split("/")[-1]
        # solution_path = f"/commonroad/solutions/solution_KS1:TR1:{name_scenario}:2020a.xml"
        # return CommonRoadSolutionReader.open(solution_path)

    # option 2: retrieve the initial state of the interactive scenario and perform an open-loop planning
    # name_scenario = scenario_path.split("/")[-1]
    # path_scenario_cr = f"{scenario_path}/{name_scenario}.cr.xml"
    # scenario, planning_problem_set = CommonRoadFileReader(path_scenario_cr).open()
    return None
