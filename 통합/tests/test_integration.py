"""
-------------------------------------------------------------------
  통합 테스트 프로그램 (MATLAB Simulink 없이)

  목적: 모든 센서와 모터가 통합되어 정상 작동하는지 테스트
        실제 자율주행과 동일하게 동작하지만 디버그 정보를 더 많이 표시

  실행 방법:
    python tests/test_integration.py

  종료 방법:
    'q' 키 또는 Ctrl + C
-------------------------------------------------------------------
"""

import sys
import os
import time

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.vehicle import sensors
from modules.vehicle import control
from utils import Function_Library as fl
import config

def print_sensor_status(frame_count, direction, has_obstacle, nearest_distance,
                        ultrasonic_data, command):
    """센서 상태를 상세하게 출력"""
    print(f"\n{'='*70}")
    print(f"프레임 {frame_count}")
    print(f"{'='*70}")

    # 차선 방향
    direction_names = {
        fl.FORWARD: "직진 (FORWARD)",
        fl.LEFT: "좌회전 (LEFT)",
        fl.RIGHT: "우회전 (RIGHT)",
        None: "인식 실패"
    }
    print(f"[차선 감지] {direction_names.get(direction, '알 수 없음')}")

    # 라이다
    obstacle_status = "⚠️ 장애물 감지!" if has_obstacle else "✓ 안전"
    print(f"[라이다] {obstacle_status} (최근거리: {nearest_distance}mm)")

    # 초음파
    print(f"[초음파 센서]")
    print(f"  전방(F):    {ultrasonic_data.get('F', 0):3d} cm")
    print(f"  좌전방(FL): {ultrasonic_data.get('FL', 0):3d} cm")
    print(f"  우전방(FR): {ultrasonic_data.get('FR', 0):3d} cm")
    print(f"  후방(R):    {ultrasonic_data.get('R', 0):3d} cm")
    print(f"  좌후방(RL): {ultrasonic_data.get('RL', 0):3d} cm")
    print(f"  우후방(RR): {ultrasonic_data.get('RR', 0):3d} cm")

    # 제어 명령
    command_names = {
        'F': '⬆️ 전진',
        'B': '⬇️ 후진',
        'L': '⬅️ 좌회전',
        'R': '➡️ 우회전',
        'S': '🛑 정지'
    }
    print(f"[모터 명령] {command_names.get(command, command)}")
    print(f"{'='*70}\n")


def integration_test():
    """통합 테스트 메인 함수"""
    print("=" * 70)
    print("자율주행 통합 테스트 프로그램")
    print("=" * 70)
    print("이 프로그램은 실제 자율주행 시스템의 모든 기능을 테스트합니다.")
    print("MATLAB Simulink 없이 독립적으로 실행됩니다.")
    print("=" * 70)
    print("종료: 'q' 키 또는 Ctrl+C")
    print("=" * 70)

    ch0, ch1 = None, None

    try:
        # ==================== 초기화 ====================
        print("\n[초기화 시작]")
        ch0, ch1 = sensors.initialize()
        print("\n[초기화 완료]")
        print("=" * 70)

        # ==================== 자율주행 시작 ====================
        print("\n🚦 자율주행 테스트 시작!")
        print("-" * 70)

        frame_count = 0

        # 라이다 스캔 루프
        for scan in sensors.get_lidar_scanning():
            frame_count += 1

            # ==================== 센서 데이터 수집 ====================
            # 카메라
            ret0, frame0, ret1, frame1 = sensors.read_camera(ch0, ch1)
            if not ret0:
                print("카메라 읽기 실패!")
                break

            # 차선 감지
            direction = sensors.get_lane_direction(frame0)

            # 라이다 장애물 감지
            has_obstacle, nearest_distance = sensors.check_obstacle(scan)

            # 초음파 센서
            ultrasonic_data = sensors.read_ultrasonic()

            # ==================== 제어 결정 ====================
            command = control.decide_action(
                direction,
                has_obstacle,
                nearest_distance,
                ultrasonic_data
            )

            # ==================== 모터 명령 전송 ====================
            control.send_motor_command(command)

            # ==================== 영상 표시 ====================
            sensors.show_camera_image(frame0, frame1)

            # ==================== 상세 상태 출력 ====================
            # 디버그 모드: 매 프레임마다 출력
            if frame_count % 5 == 0:  # 5프레임마다 출력
                print_sensor_status(
                    frame_count,
                    direction,
                    has_obstacle,
                    nearest_distance,
                    ultrasonic_data,
                    command
                )

            # ==================== 종료 확인 ====================
            if sensors.check_quit_key():
                print("\n🛑 사용자가 종료를 요청했습니다 ('q' 키)")
                break

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자가 중단했습니다 (Ctrl+C)")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # ==================== 종료 처리 ====================
        print("\n[시스템 종료 중...]")
        control.cleanup()
        sensors.cleanup()
        print("✅ 통합 테스트 종료 완료")


if __name__ == "__main__":
    integration_test()
