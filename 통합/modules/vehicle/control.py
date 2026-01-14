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

import sys
import os
# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from utils import Function_Library as fl
from modules.vehicle import sensors
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
def decide_action(direction, has_obstacle, nearest_distance, ultrasonic_data):
    """
    센서 데이터를 분석해서 모터 제어 명령 결정

    Args:
        direction (int): 차선 방향 (FORWARD=0, LEFT=1, RIGHT=2, None)
        has_obstacle (bool): 라이다 장애물 감지 여부
        nearest_distance (int): 가장 가까운 장애물 거리 (mm)
        ultrasonic_data (dict): 초음파 6개 센서 거리 딕셔너리 (cm)
                                {'F': 25, 'FL': 30, 'FR': 28, 'R': 50, 'RL': 45, 'RR': 48}

    Returns:
        str: 모터 명령 ('F', 'B', 'L', 'R', 'S')

    우선순위:
        1. 라이다 장애물 감지 → 정지 ('S')
        2. 전방 3개 초음파 센서 장애물 감지 → 정지 ('S')
        3. 차선 방향 따라가기 → 전진/좌회전/우회전
        4. 차선 못 찾으면 → 정지 ('S')
    """
    # 우선순위 1: 라이다 장애물 감지 시 정지
    if has_obstacle:
        print(f"⚠️  라이다 장애물 감지! (거리: {nearest_distance}mm)")
        return 'S'

    # 우선순위 2: 전방 3개 초음파 센서 체크 (F, FL, FR)
    # 안전 거리 변환: config는 mm 단위, Arduino는 cm 단위 전송
    safe_distance_cm = config.ULTRASONIC_SAFE_DISTANCE / 10  # mm → cm

    # 전방 센서 거리 추출 (센서 값이 0이면 999로 간주 = 측정 실패)
    front_distance = ultrasonic_data.get('F', 999)
    front_left_distance = ultrasonic_data.get('FL', 999)
    front_right_distance = ultrasonic_data.get('FR', 999)

    # 0은 측정 실패이므로 999로 대체 (무한대로 간주)
    if front_distance == 0:
        front_distance = 999
    if front_left_distance == 0:
        front_left_distance = 999
    if front_right_distance == 0:
        front_right_distance = 999

    # 전방 3개 센서 중 가장 가까운 거리 찾기
    min_front_distance = min(front_distance, front_left_distance, front_right_distance)

    # 안전 거리 이내에 장애물이 있으면 정지
    if min_front_distance < safe_distance_cm:
        # 어느 센서가 감지했는지 출력
        sensor_name = "전방"
        if min_front_distance == front_left_distance:
            sensor_name = "좌전방"
        elif min_front_distance == front_right_distance:
            sensor_name = "우전방"

        print(f"⚠️  초음파 {sensor_name} 장애물 감지! (거리: {int(min_front_distance)}cm)")
        print(f"   (전방: {front_distance}cm, 좌전: {front_left_distance}cm, 우전: {front_right_distance}cm)")
        return 'S'

    # 우선순위 3: 차선 따라가기
    if direction == fl.FORWARD:
        return 'F'  # 직진
    elif direction == fl.LEFT:
        return 'L'  # 좌회전
    elif direction == fl.RIGHT:
        return 'R'  # 우회전

    # 우선순위 4: 차선 인식 실패 시 정지
    print("⚠️  차선 인식 실패 - 정지")
    return 'S'


# ==================== 고급 제어 로직 (선택 사항) ====================
def decide_action_advanced(direction, has_obstacle, nearest_distance,
                          ultrasonic_data, traffic_light=None):
    """
    신호등까지 고려한 고급 제어 로직

    Args:
        direction: 차선 방향
        has_obstacle: 장애물 감지 여부
        nearest_distance: 장애물 거리 (mm)
        ultrasonic_data (dict): 초음파 6개 센서 거리 딕셔너리 (cm)
        traffic_light: 신호등 색상 ("RED", "GREEN", "YELLOW", "BLUE")

    Returns:
        str: 모터 명령

    우선순위:
        1. 빨간 신호등 → 정지
        2. 노란 신호등 → 정지 (감속)
        3. 라이다 장애물 → 정지
        4. 초음파 전방 장애물 → 정지
        5. 초록 신호 + 차선 따라가기
    """
    # 우선순위 1: 빨간 신호등 → 정지
    if traffic_light == "RED":
        print("🚦 빨간 신호! 정지")
        return 'S'

    # 우선순위 2: 노란 신호등 → 감속 (현재는 정지)
    if traffic_light == "YELLOW":
        print("🚦 노란 신호! 정지")
        return 'S'

    # 우선순위 3: 라이다 장애물 감지 → 정지
    if has_obstacle:
        print(f"⚠️  라이다 장애물 감지! (거리: {nearest_distance}mm)")
        return 'S'

    # 우선순위 4: 전방 3개 초음파 센서 체크
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
        sensor_name = "전방"
        if min_front_distance == front_left_distance:
            sensor_name = "좌전방"
        elif min_front_distance == front_right_distance:
            sensor_name = "우전방"

        print(f"⚠️  초음파 {sensor_name} 장애물 감지! (거리: {int(min_front_distance)}cm)")
        return 'S'

    # 우선순위 5: 초록 신호 + 차선 따라가기
    if traffic_light == "GREEN":
        print("🚦 초록 신호! 주행")

    # 차선 따라가기
    if direction == fl.FORWARD:
        return 'F'
    elif direction == fl.LEFT:
        return 'L'
    elif direction == fl.RIGHT:
        return 'R'
    else:
        print("⚠️  차선 인식 실패 - 정지")
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
