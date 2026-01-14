"""
-------------------------------------------------------------------
  FILE NAME: main.py
  자율주행 메인 실행 프로그램 (모듈화 버전)

  실행 방법:
    python main.py

  종료 방법:
    - 'q' 키 입력
    - Ctrl + C

  파일 구조:
    config.py   - 설정 값
    sensors.py  - 센서 처리
    control.py  - 제어 로직
    main.py     - 실행 코드 (이 파일)
-------------------------------------------------------------------
  Generated: 2025-12-29
-------------------------------------------------------------------
"""

import sys
import os
# 현재 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(__file__))

from modules.vehicle import sensors
from modules.vehicle import control
import config

# ==================== 메인 자율주행 루프 ====================
def autonomous_driving_loop(ch0, ch1):
    """
    자율주행 메인 루프

    Args:
        ch0: 카메라 채널 0
        ch1: 카메라 채널 1

    동작 흐름:
        1) 센서 데이터 수집 (카메라, 라이다, 초음파)
        2) 데이터 분석 (차선, 장애물)
        3) 제어 결정 (전진/좌회전/우회전/정지)
        4) 모터 명령 전송
        5) 영상 표시 (디버깅용)
        6) 'q' 키 입력 시 종료
    """
    print("\n🚦 자율주행 시작!")
    print("종료: 'q' 키 또는 Ctrl+C")
    print("-" * 50)

    frame_count = 0

    # 라이다 스캔 루프
    for scan in sensors.get_lidar_scanning():
        frame_count += 1

        # ==================== 1. 센서 데이터 수집 ====================
        # 카메라 영상 읽기
        ret0, frame0, ret1, frame1 = sensors.read_camera(ch0, ch1)

        # 차선 방향 감지
        direction = sensors.get_lane_direction(frame0)

        # 신호등 감지 (선택 사항 - 주석 해제하면 사용)
        # traffic_light = sensors.get_traffic_light(frame0)

        # 장애물 감지 (라이다)
        has_obstacle, nearest_distance = sensors.check_obstacle(scan)

        # 초음파 센서 읽기
        ultrasonic_dist = sensors.read_ultrasonic()

        # ==================== 2. 제어 결정 ====================
        command = control.decide_action(
            direction,
            has_obstacle,
            nearest_distance,
            ultrasonic_dist
        )

        # 신호등 고려 버전 (선택 사항)
        # command = control.decide_action_advanced(
        #     direction, has_obstacle, nearest_distance,
        #     ultrasonic_dist, traffic_light
        # )

        # ==================== 3. 모터 명령 전송 ====================
        control.send_motor_command(command)

        # ==================== 4. 영상 표시 (디버깅용) ====================
        sensors.show_camera_image(frame0, frame1)

        # ==================== 5. 상태 출력 ====================
        if frame_count % config.DEBUG_PRINT_INTERVAL == 0:
            print(f"\n[프레임 {frame_count}]")
            print(f"  차선: {direction}")
            print(f"  라이다: {nearest_distance}mm")
            print(f"  초음파: {ultrasonic_dist}mm")
            print(f"  명령: {command}\n")

        # ==================== 6. 종료 확인 ====================
        if sensors.check_quit_key():
            print("\n🛑 자율주행 종료 (사용자 요청)")
            break


# ==================== 메인 실행 ====================
if __name__ == "__main__":
    """
    프로그램 실행 시작점

    실행 흐름:
        1) 센서 초기화
        2) 자율주행 루프 실행
        3) 오류 발생 또는 종료 시 정리
    """
    ch0, ch1 = None, None

    try:
        # ==================== 초기화 ====================
        ch0, ch1 = sensors.initialize()

        # ==================== 자율주행 시작 ====================
        autonomous_driving_loop(ch0, ch1)

    except KeyboardInterrupt:
        # Ctrl+C로 중단한 경우
        print("\n\n⚠️  사용자가 중단했습니다 (Ctrl+C)")

    except Exception as e:
        # 오류 발생 시
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # ==================== 종료 처리 ====================
        # 무조건 실행되는 부분 (오류 발생해도 실행)
        control.cleanup()      # 모터 정지
        sensors.cleanup()      # 센서 종료

        print("\n✅ 프로그램 종료 완료")
