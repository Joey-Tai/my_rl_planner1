# ----- 阶段一: 构建 Frenetix-RL 环境 -----
FROM python:3.10-slim AS frenetix-env

# 设置工作目录
WORKDIR /frenetix_rl

# 安装 C++ 依赖 (如果需要)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libeigen3-dev \
    libboost-all-dev \
    libomp-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建并激活 Frenetix-RL 的虚拟环境
RUN python3 -m venv /opt/venv_frenetix
ENV PATH="/opt/venv_frenetix/bin:$PATH"

# 复制 Frenetix-RL 项目文件
COPY ./frenetix_rl /frenetix_rl/frenetix_rl
COPY ./configurations /frenetix_rl/configurations
COPY ./logs /frenetix_rl/logs
# 假设 Frenetix-RL 的 requirements.txt 或 pyproject.toml 在这里
# COPY ./frenetix_rl/pyproject.toml /frenetix_rl/
# COPY ./frenetix_rl/poetry.lock /frenetix_rl/

# 安装 Frenetix-RL 的依赖到它的虚拟环境中
# 注意：这里需要你有 Frenetix-RL 的依赖列表文件
# 例如: RUN pip install -r frenetix_rl/requirements.txt
# 或者，如果 frenetix-rl 本身是可安装的包:
COPY ./frenetix_rl/setup.py /frenetix_rl/
RUN pip install --no-cache-dir .


# ----- 阶段二: 构建 commonroad-challenge (最终) 环境 -----
FROM python:3.10-slim

# 安装 SUMO 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /commonroad

# 创建并激活 commonroad-challenge 的虚拟环境
RUN python3 -m venv /opt/venv_competition
ENV PATH="/opt/venv_competition/bin:$PATH"

# 从阶段一复制已经构建好的 Frenetix-RL 环境和代码
COPY --from=frenetix-env /opt/venv_frenetix /opt/venv_frenetix
COPY --from=frenetix-env /frenetix_rl /frenetix_rl

# 复制 commonroad-challenge 项目文件
COPY ./planner /commonroad/planner
COPY ./simulation /commonroad/simulation
# ... 复制其他必要的文件和文件夹 (base, demo, 等)

# 安装 commonroad-challenge 的依赖到它的虚拟环境中
# 注意：这里需要你有 commonroad-challenge 的依赖列表文件
# 例如: RUN pip install -r requirements.txt
# 或者:
RUN pip install --no-cache-dir \
    commonroad-io \
    commonroad-drivability-checker \
    commonroad-scenario-designer \
    sumocr \
    numpy \
    matplotlib \
    shapely

# 设置入口点
ENTRYPOINT ["/opt/venv_competition/bin/python", "/commonroad/planner"]