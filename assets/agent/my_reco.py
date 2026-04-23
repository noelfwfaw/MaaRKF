import sys
import time
from datetime import datetime
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context


class GlobalState:
    def __init__(self):
        self.action_count = 0
        self.cycle_start_time = 0
        self.cycle_count = 0

state = GlobalState()


def log_info(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO][{timestamp}] {message}")


@AgentServer.custom_recognition("ResetTimer")
class ResetTimerRecognition(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        state.cycle_start_time = time.time()
        state.action_count = 0
        state.cycle_count += 1

        log_info(f"========== 第 {state.cycle_count} 个25分钟周期开始 ==========")
        log_info(f"开始时间: {datetime.fromtimestamp(state.cycle_start_time).strftime('%H:%M:%S')}")

        # 设置下一步为选择精灵1
        context.override_next(argv.node_name, ["选择精灵1"])

        return CustomRecognition.AnalyzeResult(box=(0, 0, 0, 0), detail="timer_reset")


@AgentServer.custom_recognition("CheckTimer")
class CheckTimerRecognition(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        # 首次运行
        if state.cycle_start_time == 0:
            log_info(f"[计时] 首次运行，开始计时")
            state.cycle_start_time = time.time()
            state.cycle_count += 1
            context.override_next(argv.node_name, ["做动作"])
            return CustomRecognition.AnalyzeResult(box=(0, 0, 0, 0), detail="first_start")

        elapsed = time.time() - state.cycle_start_time

        if elapsed >= 1500:
            log_info(f"========== 25分钟已到！共执行动作 {state.action_count} 次 ==========")
            state.action_count = 0
            context.override_next(argv.node_name, ["调整时间"])
            return CustomRecognition.AnalyzeResult(box=(0, 0, 0, 0), detail="time_to_reset")
        else:
            remaining = 1500 - elapsed
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            log_info(f"[计时] 距离下次调整时间还有 {minutes}分{seconds}秒 | 当前周期已执行动作: {state.action_count} 次")
            context.override_next(argv.node_name, ["做动作"])
            return CustomRecognition.AnalyzeResult(box=(0, 0, 0, 0), detail="still_waiting")


@AgentServer.custom_recognition("ActionCounter")
class ActionCounterRecognition(CustomRecognition):
    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        state.action_count += 1

        if state.cycle_start_time > 0:
            elapsed = time.time() - state.cycle_start_time
            elapsed_min = int(elapsed // 60)
            elapsed_sec = int(elapsed % 60)
            log_info(f"[计数] 动作+1 | 第 {state.cycle_count} 轮 | 已执行动作: {state.action_count} 次 | 本周期已过: {elapsed_min}分{elapsed_sec}秒")
        else:
            log_info(f"[计数] 动作+1 | 第 {state.cycle_count} 轮 | 已执行动作: {state.action_count} 次")

        context.override_next(argv.node_name, ["[Anchor]LoopPoint"])

        return CustomRecognition.AnalyzeResult(box=(0, 0, 0, 0), detail=f"count_{state.action_count}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python agent_main.py <socket_id>")
        exit(1)

    socket_id = sys.argv[-1]
    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()