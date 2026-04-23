import time
from datetime import datetime
from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction

class GlobalState:
    def __init__(self):
        self.action_count = 0           # 当前周期内动作计数
        self.cycle_start_time = 0       # 当前周期开始时间（调整时间时重置）
        self.cycle_count = 0            # 周期计数（第几轮25分钟）

state = GlobalState()


def log_info(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO][{timestamp}] {message}")


@AgentServer.custom_action("ResetTimer")
class ResetTimerAction(CustomAction):
    """调整时间完成后调用：重置计时器和计数器"""
    def run(self, context: Context, box: tuple, param: str):
        state.cycle_start_time = time.time()
        state.action_count = 0
        state.cycle_count += 1
        
        log_info(f"========== 第 {state.cycle_count} 个25分钟周期开始 ==========")
        log_info(f"开始时间: {datetime.fromtimestamp(state.cycle_start_time).strftime('%H:%M:%S')}")
        
        return True


@AgentServer.custom_action("CheckTimer")
class CheckTimerAction(CustomAction):
    """检查是否已过25分钟，如果是则触发重新调整时间"""
    def run(self, context: Context, box: tuple, param: str):
        if state.cycle_start_time == 0:
            # 还没重置过，先重置
            state.cycle_start_time = time.time()
            state.action_count = 0
            state.cycle_count += 1
            log_info(f"========== 第 {state.cycle_count} 个25分钟周期开始 ==========")
            return True
        
        elapsed = time.time() - state.cycle_start_time
        
        if elapsed >= 1500:  # 25分钟 = 1500秒
            log_info(f"========== 25分钟已到！共执行动作 {state.action_count} 次 ==========")
            # 返回True，进入next（重新调整时间）
            return True
        else:
            # 未到25分钟，继续做动作
            remaining = 1500 - elapsed
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            log_info(f"[计时] 距离下次调整时间还有 {minutes}分{seconds}秒 | 当前周期已执行动作: {state.action_count} 次")
            # 返回False，触发on_error（继续做动作循环）
            return False


@AgentServer.custom_action("ActionCounter")
class ActionCounterAction(CustomAction):
    """每次做完动作调用：累加计数并输出info"""
    def run(self, context: Context, box: tuple, param: str):
        state.action_count += 1
        
        if state.cycle_start_time > 0:
            elapsed = time.time() - state.cycle_start_time
            elapsed_min = int(elapsed // 60)
            elapsed_sec = int(elapsed % 60)
            log_info(f"[计数] 动作+1 | 第 {state.cycle_count} 轮 | 已执行动作: {state.action_count} 次 | 本周期已过: {elapsed_min}分{elapsed_sec}秒")
        else:
            log_info(f"[计数] 动作+1 | 第 {state.cycle_count} 轮 | 已执行动作: {state.action_count} 次")
        
        return True


if __name__ == "__main__":
    AgentServer.start_up("your_socket_name")