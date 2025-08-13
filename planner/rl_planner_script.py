# planner/rl_planner_script.py

import os
import pickle
import argparse
import numpy as np

# --- 这些导入将在 Frenetix-RL 的虚拟环境中执行 ---
from sb3_contrib import RecurrentPPO
from frenetix_rl.gym_environment.observation import ObservationCollector
from frenetix_rl.utils.helper_functions import load_environment_configs
from frenetix_rl.gym_environment.paths import PATH_PARAMS
from cr_scenario_handler.utils.configuration_builder import ConfigurationBuilder
from cr_scenario_handler.planner.frenet_planner import FrenetPlanner


# 一个简化的对象，用于满足 ObservationCollector 的接口需求
class MockAgent:
    def __init__(self, scenario, state, planner_interface):
        self.scenario = scenario
        self.state = state
        self.planner_interface = planner_interface


class MockPlannerInterface:
    def __init__(self, cost_weights):
        self.planner = self.MockPlanner(cost_weights)

    class MockPlanner:
        def __init__(self, cost_weights):
            self.cost_weights = cost_weights


def plan_with_rl():
    # --- 1. 解析从主进程传入的参数 ---
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", required=True, help="Path to the pickled input data file.")
    parser.add_argument("--output-file", required=True, help="Path to write the pickled output data file.")
    parser.add_argument("--model-path", required=True, help="Path to the trained RL model.")
    parser.add_argument("--config-path", required=True, help="Path to the Frenetix-RL environment config.")
    parser.add_argument("--frenetix-config-path", required=True, help="Path to the Frenetix planner config.")
    args = parser.parse_args()

    # --- 2. 加载输入数据 ---
    with open(args.input_file, 'rb') as f:
        data = pickle.load(f)
    current_scenario = data['scenario']
    current_ego_state = data['ego_state']
    cost_weights = data['cost_weights']

    # --- 3. 加载RL模型和配置 ---
    model = RecurrentPPO.load(args.model_path)
    env_configs = load_environment_configs(args.config_path)
    observation_collector = ObservationCollector(env_configs)

    # --- 4. 生成观测 ---
    # 创建模拟的 agent 对象以匹配 observation_collector 的接口
    mock_planner_interface = MockPlannerInterface(cost_weights)
    mock_agent = MockAgent(current_scenario, current_ego_state, mock_planner_interface)
    observation = observation_collector.observe(mock_agent)

    # --- 5. RL模型决策 ---
    action, _ = model.predict(observation, deterministic=True)

    # --- 6. 应用动作（成本权重）并调用分析型规划器 ---
    # Rescale action to actual weight values (logic from AgentEnv)
    action_configs = env_configs["action_configs"]
    rescale_factor = (np.array(action_configs["weight_update_high"]) - np.array(
        action_configs["weight_update_low"])) / 2.0
    rescale_bias = np.array(action_configs["weight_update_high"]) - rescale_factor

    # Prediction weight
    pred_rescale_factor = (action_configs["weight_prediction_update_high"] - action_configs[
        "weight_prediction_update_low"]) / 2.
    pred_rescale_bias = action_configs["weight_prediction_update_high"] - pred_rescale_factor

    action[0] = action[0] * pred_rescale_factor + pred_rescale_bias
    action[1:] = action[1:] * rescale_factor + rescale_bias

    # Update cost weights cumulatively
    new_cost_weights = cost_weights
    new_cost_weights["prediction"] += action[0]
    for i, name in enumerate(action_configs["cost_terms"]):
        new_cost_weights[name] += action[1 + i]

    # 钳位以确保权重在有效范围内
    new_cost_weights["prediction"] = np.clip(new_cost_weights["prediction"], action_configs["weight_prediction_low"],
                                             action_configs["weight_prediction_high"])
    for name in action_configs["cost_terms"]:
        new_cost_weights[name] = np.clip(new_cost_weights[name], action_configs["weight_low"],
                                         action_configs["weight_high"])

    # --- 7. 运行 Frenetix 分析型规划器 ---
    config_planner = ConfigurationBuilder.build_frenetplanner_configuration(args.frenetix_config_path)
    planner = FrenetPlanner(config_planner, current_scenario, current_ego_state.time_step)
    planner.cost_weights = new_cost_weights

    planned_trajectory, _ = planner.plan_motion(current_ego_state)
    next_state = planned_trajectory.state_list[1]

    # --- 8. 保存输出结果 ---
    output_data = {
        'next_state': next_state,
        'cost_weights': new_cost_weights  # 返回更新后的权重，用于下一步
    }
    with open(args.output_file, 'wb') as f:
        pickle.dump(output_data, f)


if __name__ == '__main__':
    plan_with_rl()