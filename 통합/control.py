"""
-------------------------------------------------------------------
  FILE NAME: control.py
  모터 제어 모듈

  기능:
  1) 모터 명령 전송
  2) 자율주행 제어 로직
  3) 의사 결정 알고리즘
-------------------------------------------------------------------
  Generated: 2025-12-29
-------------------------------------------------------------------
"""

import Function_Library as fl
import sensors
import config

# ==================== 모터 명령 전송 ====================
def send_motor_command(command):
    """
    아두이노로 모터 제어 명령 전송

    Args:
        command (str): 모터 명령
            'F' - 전진 (Forward)
            'B' - 후진 (Backward)
            'L' - 좌회전 (Left)
            'R' - 우회전 (Right)
            'S' - 정지 (Stop)

    동작:
        - 시리얼 통신으로 1바이트 전송
        - 아두이노가 받아서 모터 제어
    """
    sensors.arduino.write(command.encode())

    # 명령에 따른 메시지 출력
    messages = {
        'F': '전진',
        'B': '후진',
        'L': '좌회전',
        'R': '우회전',
        'S': '정지'
    }
    print(messages.get(command, f'[모터 명령] {command}'))


# ==================== 제어 결정 로직 ====================
def decide_action(direction, has_obstacle, nearest_distance, ultrasonic_dist):
    """
    센서 데이터를 분석해서 모터 제어 명령 결정

    Args:
        direction (int): 차선 방향 (FORWARD=0, LEFT=1, RIGHT=2, None)
        has_obstacle (bool): 라이다 장애물 감지 여부
        nearest_distance (int): 가장 가까운 장애물 거리 (mm)
        ultrasonic_dist (int): 초음파 센서 거리 (mm)

    Returns:
        str: 모터 명령 ('F', 'B', 'L', 'R', 'S')

    우선순위:
        1. 장애물 감지 → 정지 ('S')
        2. 차선 방향 따라가기 → 전진/좌회전/우회전
        3. 차선 못 찾으면 → 정지 ('S')
    """
    # 우선순위 1: 장애물 감지 시 정지
    if has_obstacle:
        print(f"라이다 장애물 감지! (거리: {nearest_distance}mm)")
        return 'S'

    if ultrasonic_dist > 0 and ultrasonic_dist < config.ULTRASONIC_SAFE_DISTANCE:
        print(f"초음파 장애물 감지! (거리: {ultrasonic_dist}mm)")
        return 'S'

    # 우선순위 2: 차선 따라가기
    if direction == fl.FORWARD:
        return 'F'  # 직진
    elif direction == fl.LEFT:
        return 'L'  # 좌회전
    elif direction == fl.RIGHT:
        return 'R'  # 우회전

    # 우선순위 3: 차선 인식 실패 시 정지
    print(" 차선 인식 실패 - 정지")
    return 'S'


# ==================== 고급 제어 로직 (선택 사항) ====================
def decide_action_advanced(direction, has_obstacle, nearest_distance,
                          ultrasonic_dist, traffic_light=None):
    """
    신호등까지 고려한 고급 제어 로직

    Args:
        direction: 차선 방향
        has_obstacle: 장애물 감지 여부
        nearest_distance: 장애물 거리
        ultrasonic_dist: 초음파 거리
        traffic_light: 신호등 색상 ("RED", "GREEN", "YELLOW")

    Returns:
        str: 모터 명령
    """
    # 우선순위 1: 빨간 신호등 → 정지
    if traffic_light == "RED":
        print("빨간 신호! 정지")
        return 'S'

    # 우선순위 2: 노란 신호등 → 감속 (현재는 정지)
    if traffic_light == "YELLOW":
        print("노란 신호! 정지")
        return 'S'

    # 우선순위 3: 장애물 감지 → 정지
    if has_obstacle or (ultrasonic_dist > 0 and
                        ultrasonic_dist < config.ULTRASONIC_SAFE_DISTANCE):
        print(f"장애물 감지! (라이다: {nearest_distance}mm, 초음파: {ultrasonic_dist}mm)")
        return 'S'

    # 우선순위 4: 초록 신호 + 차선 따라가기
    if traffic_light == "GREEN":
        print("초록 신호! 주행")

    # 차선 따라가기
    if direction == fl.FORWARD:
        return 'F'
    elif direction == fl.LEFT:
        return 'L'
    elif direction == fl.RIGHT:
        return 'R'
    else:
        return 'S'


# ==================== 긴급 정지 ====================
def emergency_stop():
    """
    긴급 정지

    사용 시점:
        - 오류 발생 시
        - 프로그램 종료 시
        - 긴급 상황 발생 시
    """
    print("\n긴급 정지!")
    send_motor_command('S')


# ==================== 종료 처리 ====================
def cleanup():
    """
    제어 시스템 종료

    동작:
        1) 모터 정지
        2) 잠시 대기 (모터가 완전히 멈출 때까지)
    """
    print("\n제어 시스템 종료 중...")
    emergency_stop()
    import time
    time.sleep(0.5)  # 0.5초 대기
    print("✓ 제어 시스템 종료 완료")
