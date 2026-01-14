"""
-------------------------------------------------------------------
  시뮬레이션 모드 테스트 프로그램

  목적: 실제 하드웨어 없이 자율주행 로직을 테스트
        가상의 센서 데이터를 생성하여 제어 알고리즘 검증

  실행 방법:
    python tests/test_simulation.py

  종료 방법:
    Ctrl + C
-------------------------------------------------------------------
"""

import sys
import os
import time
import random

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils import Function_Library as fl
import config

# ==================== 시나리오 정의 ====================
SCENARIOS = [
    {
        "name": "시나리오 1: 직진 주행 (장애물 없음)",
        "duration": 5,  # 초
        "lane_direction": fl.FORWARD,
        "lidar_distance": 1000,  # mm
        "ultrasonic": {'F': 100, 'FL': 100, 'FR': 100, 'R': 100, 'RL': 100, 'RR': 100}
    },
    {
        "name": "시나리오 2: 좌회전",
        "duration": 3,
        "lane_direction": fl.LEFT,
        "lidar_distance": 1000,
        "ultrasonic": {'F': 100, 'FL': 80, 'FR': 120, 'R': 100, 'RL': 100, 'RR': 100}
    },
    {
        "name": "시나리오 3: 우회전",
        "duration": 3,
        "lane_direction": fl.RIGHT,
        "lidar_distance": 1000,
        "ultrasonic": {'F': 100, 'FL': 120, 'FR': 80, 'R': 100, 'RL': 100, 'RR': 100}
    },
    {
        "name": "시나리오 4: 전방 장애물 감지 (라이다)",
        "duration": 2,
        "lane_direction": fl.FORWARD,
        "lidar_distance": 300,  # 500mm 이하 → 위험!
        "ultrasonic": {'F': 100, 'FL': 100, 'FR': 100, 'R': 100, 'RL': 100, 'RR': 100}
    },
    {
        "name": "시나리오 5: 전방 장애물 감지 (초음파)",
        "duration": 2,
        "lane_direction": fl.FORWARD,
        "lidar_distance": 1000,
        "ultrasonic": {'F': 15, 'FL': 100, 'FR': 100, 'R': 100, 'RL': 100, 'RR': 100}  # 20cm 이하 → 위험!
    },
    {
        "name": "시나리오 6: 좌전방 장애물",
        "duration": 2,
        "lane_direction": fl.LEFT,
        "lidar_distance": 1000,
        "ultrasonic": {'F': 100, 'FL': 15, 'FR': 100, 'R': 100, 'RL': 100, 'RR': 100}
    },
    {
        "name": "시나리오 7: 우전방 장애물",
        "duration": 2,
        "lane_direction": fl.RIGHT,
        "lidar_distance": 1000,
        "ultrasonic": {'F': 100, 'FL': 100, 'FR': 15, 'R': 100, 'RL': 100, 'RR': 100}
    },
    {
        "name": "시나리오 8: 차선 인식 실패",
        "duration": 2,
        "lane_direction": None,
        "lidar_distance": 1000,
        "ultrasonic": {'F': 100, 'FL': 100, 'FR': 100, 'R': 100, 'RL': 100, 'RR': 100}
    },
]

# ==================== 제어 로직 (control.py의 복사) ====================
def decide_action_sim(direction, has_obstacle, nearest_distance, ultrasonic_data):
    """
    시뮬레이션용 제어 결정 로직
    (실제 control.py의 decide_action()과 동일)
    """
    # 우선순위 1: 라이다 장애물
    if has_obstacle:
        return 'S'

    # 우선순위 2: 초음파 전방 센서
    safe_distance_cm = config.ULTRASONIC_SAFE_DISTANCE / 10
    front_distance = ultrasonic_data.get('F', 999)
    front_left_distance = ultrasonic_data.get('FL', 999)
    front_right_distance = ultrasonic_data.get('FR', 999)

    # 0은 측정 실패
    if front_distance == 0:
        front_distance = 999
    if front_left_distance == 0:
        front_left_distance = 999
    if front_right_distance == 0:
        front_right_distance = 999

    min_front_distance = min(front_distance, front_left_distance, front_right_distance)

    if min_front_distance < safe_distance_cm:
        return 'S'

    # 우선순위 3: 차선 따라가기
    if direction == fl.FORWARD:
        return 'F'
    elif direction == fl.LEFT:
        return 'L'
    elif direction == fl.RIGHT:
        return 'R'

    # 우선순위 4: 차선 인식 실패
    return 'S'


def simulate_scenario(scenario):
    """시나리오 실행"""
    print("\n" + "=" * 70)
    print(f"▶️ {scenario['name']}")
    print("=" * 70)

    # 시나리오 정보 출력
    direction_names = {
        fl.FORWARD: "직진 (FORWARD)",
        fl.LEFT: "좌회전 (LEFT)",
        fl.RIGHT: "우회전 (RIGHT)",
        None: "인식 실패"
    }

    print(f"차선 방향: {direction_names.get(scenario['lane_direction'], '알 수 없음')}")
    print(f"라이다 거리: {scenario['lidar_distance']} mm")
    print(f"초음파 센서: {scenario['ultrasonic']}")
    print(f"지속 시간: {scenario['duration']}초")
    print("-" * 70)

    # 장애물 판정
    has_obstacle = scenario['lidar_distance'] < config.OBSTACLE_DISTANCE

    # 제어 결정
    command = decide_action_sim(
        scenario['lane_direction'],
        has_obstacle,
        scenario['lidar_distance'],
        scenario['ultrasonic']
    )

    # 결과 출력
    command_names = {
        'F': '⬆️ 전진 (Forward)',
        'B': '⬇️ 후진 (Backward)',
        'L': '⬅️ 좌회전 (Left)',
        'R': '➡️ 우회전 (Right)',
        'S': '🛑 정지 (Stop)'
    }

    print(f"\n[제어 결정]")
    print(f"  명령: {command_names.get(command, command)}")

    # 판단 근거 출력
    print(f"\n[판단 근거]")
    if has_obstacle:
        print(f"  ⚠️ 라이다 장애물 감지 ({scenario['lidar_distance']}mm < {config.OBSTACLE_DISTANCE}mm)")

    safe_dist_cm = config.ULTRASONIC_SAFE_DISTANCE / 10
    min_front = min(
        scenario['ultrasonic'].get('F', 999),
        scenario['ultrasonic'].get('FL', 999),
        scenario['ultrasonic'].get('FR', 999)
    )
    if min_front < safe_dist_cm:
        print(f"  ⚠️ 초음파 장애물 감지 ({min_front}cm < {safe_dist_cm}cm)")

    if not has_obstacle and min_front >= safe_dist_cm:
        if scenario['lane_direction'] is not None:
            print(f"  ✓ 안전 확인 → 차선 방향 따라가기")
        else:
            print(f"  ⚠️ 차선 인식 실패 → 안전을 위해 정지")

    # 시뮬레이션 진행
    print(f"\n시뮬레이션 진행 중", end="", flush=True)
    for i in range(scenario['duration']):
        time.sleep(1)
        print(".", end="", flush=True)
    print(" 완료!")

    # 예상 결과 검증
    print(f"\n[테스트 결과]")
    expected_results = {
        "시나리오 1: 직진 주행 (장애물 없음)": 'F',
        "시나리오 2: 좌회전": 'L',
        "시나리오 3: 우회전": 'R',
        "시나리오 4: 전방 장애물 감지 (라이다)": 'S',
        "시나리오 5: 전방 장애물 감지 (초음파)": 'S',
        "시나리오 6: 좌전방 장애물": 'S',
        "시나리오 7: 우전방 장애물": 'S',
        "시나리오 8: 차선 인식 실패": 'S',
    }

    expected = expected_results.get(scenario['name'], '?')
    if command == expected:
        print(f"  ✅ PASS - 예상 명령({expected})과 일치")
    else:
        print(f"  ❌ FAIL - 예상({expected}) ≠ 실제({command})")

    print("=" * 70)


def simulation_test():
    """시뮬레이션 테스트 메인 함수"""
    print("\n" + "=" * 70)
    print("🎮 자율주행 시뮬레이션 테스트 프로그램")
    print("=" * 70)
    print("이 프로그램은 실제 하드웨어 없이 자율주행 로직을 테스트합니다.")
    print("가상의 센서 데이터를 사용하여 다양한 시나리오를 검증합니다.")
    print("=" * 70)
    print(f"총 {len(SCENARIOS)}개의 시나리오를 실행합니다.")
    print("종료: Ctrl+C")
    print("=" * 70)

    try:
        # 설정 정보 출력
        print(f"\n[설정값]")
        print(f"  라이다 위험 거리: {config.OBSTACLE_DISTANCE}mm")
        print(f"  초음파 안전 거리: {config.ULTRASONIC_SAFE_DISTANCE}mm ({config.ULTRASONIC_SAFE_DISTANCE/10}cm)")
        print(f"  전방 감지 각도: {config.OBSTACLE_ANGLE_MIN}° ~ {config.OBSTACLE_ANGLE_MAX}°")

        # 모든 시나리오 실행
        for idx, scenario in enumerate(SCENARIOS, 1):
            print(f"\n\n{'#'*70}")
            print(f"# 테스트 진행: {idx}/{len(SCENARIOS)}")
            print(f"{'#'*70}")
            simulate_scenario(scenario)

            # 다음 시나리오로 넘어가기 전 대기
            if idx < len(SCENARIOS):
                time.sleep(1)

        # 전체 결과 요약
        print("\n\n" + "=" * 70)
        print("🎉 모든 시뮬레이션 테스트 완료!")
        print("=" * 70)
        print(f"총 {len(SCENARIOS)}개 시나리오 실행 완료")
        print("\n실제 차량에서 테스트하기 전에 이 시뮬레이션으로 로직을 검증하세요!")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자가 중단했습니다 (Ctrl+C)")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    simulation_test()
