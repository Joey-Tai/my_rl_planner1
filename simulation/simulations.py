# simulation/simulations.py (Modified for Subprocess)

import os
import subprocess
import pickle
import uuid
from typing import Tuple, Dict
# ... 其他原有导入 ...
from commonroad.scenario.scenario import Scenario
from sumocr.interface.ego_vehicle import EgoVehicle
from sumocr.interface.sumo_simulation import SumoSimulation
# ... 等

# ... SimulationOption Enum 和其他函数保持不变 ...

def call_rl_planner(scenario, ego_state, cost_weights):
    """
    使用子进程调用隔离的 Frenetix-RL 规划器脚本。
    """
    # 1. 创建临时文件路径
    tmp_dir = "/tmp"
    unique_id = uuid.uuid4()
    input_file = os.path.join(tmp_dir, f"rl_input_{unique_id}.pkl")
    output_file = os.path.join(tmp_dir, f"rl_output_{unique_id}.pkl")

    # 2. 序列化并写入输入数据
    input_data = {'scenario': scenario, 'ego_state': ego_state, 'cost_weights': cost_weights}
    with open(input_file, 'wb') as f:
        pickle.dump(input_data, f)
    
    # 3. 定义项目和配置文件的路径 (这些路径是 Docker 镜像内部的路径)
    frenetix_root = "/frenetix_rl"
    model_path = os.path.join(frenetix_root, "logs/best_model/best_model.zip")
    config_path = os.path.join(frenetix_root, "frenetix_rl/gym_environment/configs.yaml")
    frenetix_config_path = os.path.join(frenetix_root, "configurations/default") # Frenetix planner config

    # 4. 构建并执行子进程命令
    command = [
        "/opt/venv_frenetix/bin/python", # 使用 Frenetix 的虚拟环境
        "/commonroad/planner/rl_planner_script.py",
        "--input-file", input_file,
        "--output-file", output_file,
        "--model-path", model_path,
        "--config-path", config_path,
        "--frenetix-config-path", frenetix_config_path
    ]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=10) # 增加超时
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print("--- Subprocess Error ---")
        print(f"Error calling RL planner script for scenario {scenario.scenario_id}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise e

    # 5. 读取输出数据
    with open(output_file, 'rb') as f:
        output_data = pickle.load(f)
    
    # 6. 清理临时文件
    os.remove(input_file)
    os.remove(output_file)
    
    return output_data['next_state'], output_data['cost_weights']


def simulate_scenario(mode: SimulationOption,
                      conf: DefaultConfig,
                      # ... 其他参数 ...
                      ) -> Tuple[Scenario, Dict[int, EgoVehicle]]:
    # ... 函数开头部分不变 ...
    if mode is SimulationOption.MOTION_PLANNER:
        def run_simulation():
            # 初始化成本权重
            cost_weights = {
                "prediction": 0.0, "lat": 0.0, "lon": 0.0, "v": 0.0,
                "a": 0.0, "jerk": 0.0, "curv": 0.0, "yaw": 0.0
            }

            ego_vehicles = sumo_sim.ego_vehicles
            for step in range(num_of_steps):
                current_scenario = sumo_sim.commonroad_scenario_at_time_step(sumo_sim.current_time_step)
                
                for idx, ego_vehicle in enumerate(ego_vehicles.values()):
                    state_current_ego = ego_vehicle.current_state

                    # --- 调用子进程进行RL规划 ---
                    next_state, cost_weights = call_rl_planner(current_scenario, state_current_ego, cost_weights)
                    
                    next_state.time_step = 1
                    trajectory_ego = [next_state]
                    ego_vehicle.set_planned_trajectory(trajectory_ego)

                sumo_sim.simulate_step()
        
        run_simulation()
    
    # ... 函数其余部分不变 ...
    return simulated_scenario, ego_vehicles