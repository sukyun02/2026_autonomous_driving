# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------
  초음파 센서 + 모터 통합 테스트 프로그램

  목적: 초음파 센서 데이터에 따라 모터가 자동으로 제어되는지 테스트

  테스트 시나리오:
    1) 전방에 장애물 없으면 → 전진 (F)
    2) 전방 장애물 감지 시 → 정지 (S)
    3) 좌전방/우전방 장애물 감지 시 → 정지 (S)

  실행 방법:
    python tests/test_ultrasonic_motor.py

  종료 방법:
    Ctrl + C
-------------------------------------------------------------------
"""

import serial
import time
import sys
import os
import io

# Windows 한글 출력 문제 해결
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config

# 초음파 센서 데이터 저장
ultrasonic_data = {
    'F': 999,      # Front (전방)
    'FL': 999,     # Front-Left (좌전방)
    'FR': 999,     # Front-Right (우전방)
    'R': 999,      # Rear (후방)
    'RL': 999,     # Rear-Left (좌후방)
    'RR': 999      # Rear-Right (우후방)
}

def parse_ultrasonic_data(line):
    """
    아두이노에서 받은 초음파 센서 데이터 파싱

    Args:
        line (str): "F:25,FL:30,FR:28,R:50,RL:45,RR:48" 형식

    Returns:
        dict: 파싱된 센서 데이터
    """
    global ultrasonic_data

    try:
        # 형식 1: "F:25,FL:30,..." (6개 센서)
        if ':' in line and ',' in line:
            parts = line.split(',')
            for part in parts:
                if ':' in part:
                    key, value = part.split(':')
                    ultrasonic_data[key] = int(value)

        # 형식 2: "123" (구버전 단일 숫자)
        elif line.isdigit():
            distance = int(line)
            ultrasonic_data['F'] = distance

    except Exception as e:
        print(f"데이터 파싱 오류: {e}")

    return ultrasonic_data


def decide_motor_command(sensor_data, safe_distance_cm):
    """
    초음파 센서 데이터를 분석하여 모터 명령 결정

    Args:
        sensor_data (dict): 초음파 센서 데이터
        safe_distance_cm (int): 안전 거리 (cm)

    Returns:
        tuple: (명령, 설명)

    센서 매핑 (사진 기준):
        1번(F)  = 좌측방
        2번(FL) = 우측방
        3번(FR) = 우측
        4번(R)  = 좌측
        5번(RL) = 우전방
        6번(RR) = 좌전방

    로직:
        1) 5번(우전방) 감지 → 왼쪽 조향 (l)
        2) 6번(좌전방) 감지 → 오른쪽 조향 (r)
        3) 1번, 2번, 3번, 4번(측면) 감지 → 정지 (S)
        4) 모두 안전 → 전진 (F)
    """
    # 센서 데이터 추출 (0이면 측정 실패로 간주하여 999 대입)
    sensor_1_left_side = sensor_data.get('F', 999)      # 1번 = 좌측방
    sensor_2_right_side = sensor_data.get('FL', 999)    # 2번 = 우측방
    sensor_3_right = sensor_data.get('FR', 999)         # 3번 = 우측
    sensor_4_left = sensor_data.get('R', 999)           # 4번 = 좌측
    sensor_5_front_right = sensor_data.get('RL', 999)   # 5번 = 우전방
    sensor_6_front_left = sensor_data.get('RR', 999)    # 6번 = 좌전방

    # 0은 측정 실패 → 999로 대체
    if sensor_1_left_side == 0:
        sensor_1_left_side = 999
    if sensor_2_right_side == 0:
        sensor_2_right_side = 999
    if sensor_3_right == 0:
        sensor_3_right = 999
    if sensor_4_left == 0:
        sensor_4_left = 999
    if sensor_5_front_right == 0:
        sensor_5_front_right = 999
    if sensor_6_front_left == 0:
        sensor_6_front_left = 999

    # 우선순위 1: 5번(우전방) 감지 → 왼쪽 조향
    if sensor_5_front_right < safe_distance_cm:
        return ('l', f"⚠️  5번(우전방) 장애물 감지! ({int(sensor_5_front_right)}cm) → 왼쪽 조향")

    # 우선순위 2: 6번(좌전방) 감지 → 오른쪽 조향
    if sensor_6_front_left < safe_distance_cm:
        return ('r', f"⚠️  6번(좌전방) 장애물 감지! ({int(sensor_6_front_left)}cm) → 오른쪽 조향")

    # 우선순위 3: 1번(좌측방) 감지 → 정지
    if sensor_1_left_side < safe_distance_cm:
        return ('S', f"⚠️  1번(좌측방) 장애물 감지! ({int(sensor_1_left_side)}cm) → 정지")

    # 우선순위 4: 2번(우측방) 감지 → 정지
    if sensor_2_right_side < safe_distance_cm:
        return ('S', f"⚠️  2번(우측방) 장애물 감지! ({int(sensor_2_right_side)}cm) → 정지")

    # 우선순위 5: 3번(우측) 감지 → 정지
    if sensor_3_right < safe_distance_cm:
        return ('S', f"⚠️  3번(우측) 장애물 감지! ({int(sensor_3_right)}cm) → 정지")

    # 우선순위 6: 4번(좌측) 감지 → 정지
    if sensor_4_left < safe_distance_cm:
        return ('S', f"⚠️  4번(좌측) 장애물 감지! ({int(sensor_4_left)}cm) → 정지")

    # 모두 안전 → 전진
    all_min = min(sensor_1_left_side, sensor_2_right_side, sensor_3_right,
                  sensor_4_left, sensor_5_front_right, sensor_6_front_left)
    return ('F', f"✓ 모든 센서 안전 (최소: {int(all_min)}cm) → 전진")


def test_ultrasonic_motor():
    """초음파 센서 + 모터 통합 테스트"""
    print("=" * 70)
    print("초음파 센서 → 모터 제어 통합 테스트")
    print("=" * 70)
    print(f"포트: {config.ARDUINO_PORT}")
    print(f"통신 속도: {config.BAUDRATE}")
    print(f"안전 거리: {config.ULTRASONIC_SAFE_DISTANCE / 10:.0f} cm")
    print("=" * 70)
    print("\n센서 매핑:")
    print("  1번(F)  = 좌측방")
    print("  2번(FL) = 우측방")
    print("  3번(FR) = 우측")
    print("  4번(R)  = 좌측")
    print("  5번(RL) = 우전방")
    print("  6번(RR) = 좌전방")
    print("\n테스트 시나리오:")
    print("  1) 5번(우전방) 감지 → 왼쪽 조향 (l)")
    print("  2) 6번(좌전방) 감지 → 오른쪽 조향 (r)")
    print("  3) 1번(좌측방) 감지 → 정지 (S)")
    print("  4) 2번(우측방) 감지 → 정지 (S)")
    print("  5) 3번(우측) 감지 → 정지 (S)")
    print("  6) 4번(좌측) 감지 → 정지 (S)")
    print("  7) 모두 안전 → 전진 (F)")
    print("\n종료: Ctrl + C")
    print("-" * 70)

    try:
        # 아두이노 연결
        print("\n아두이노 연결 중...")
        arduino = serial.Serial(config.ARDUINO_PORT, config.BAUDRATE, timeout=1)
        time.sleep(2)  # 아두이노 초기화 대기
        print("✓ 아두이노 연결 완료\n")

        # 초기 버퍼 비우기
        arduino.reset_input_buffer()

        # 초기 정지
        arduino.write(b'S')
        print("[초기 명령] 정지 (S)\n")

        print("=" * 70)
        print("초음파 센서 모니터링 & 자동 모터 제어 시작")
        print("=" * 70)

        safe_distance_cm = config.ULTRASONIC_SAFE_DISTANCE / 10  # mm → cm
        frame_count = 0
        last_command = 'S'

        while True:
            # 아두이노에서 데이터 수신
            if arduino.in_waiting > 0:
                try:
                    # 데이터 읽기
                    line = arduino.readline().decode('utf-8').strip()

                    # 초음파 센서 데이터만 처리 (빈 줄 무시)
                    if line and (':' in line or line.isdigit()):
                        frame_count += 1

                        # 파싱
                        sensor_data = parse_ultrasonic_data(line)

                        # 화면 출력 - 실제 센서 위치에 맞게 표시
                        print(f"\n[프레임 {frame_count}] 초음파 센서 데이터:")
                        print(f"  1번(F)  좌측방:  {sensor_data.get('F', 0):3d} cm")
                        print(f"  2번(FL) 우측방:  {sensor_data.get('FL', 0):3d} cm")
                        print(f"  3번(FR) 우측:    {sensor_data.get('FR', 0):3d} cm")
                        print(f"  4번(R)  좌측:    {sensor_data.get('R', 0):3d} cm")
                        print(f"  5번(RL) 우전방:  {sensor_data.get('RL', 0):3d} cm")
                        print(f"  6번(RR) 좌전방:  {sensor_data.get('RR', 0):3d} cm")

                        # 모터 명령 결정
                        command, reason = decide_motor_command(sensor_data, safe_distance_cm)

                        # 명령이 바뀌었을 때만 전송 (불필요한 통신 감소)
                        if command != last_command:
                            arduino.write(command.encode())
                            print(f"\n>>> [모터 명령 변경] {last_command} → {command}")
                            print(f">>> {reason}")
                            last_command = command
                        else:
                            print(f"\n>>> [모터 상태 유지] {command}")
                            print(f">>> {reason}")

                    # 아두이노 디버그 메시지 (센서 데이터가 아닌 경우)
                    elif line:
                        print(f"  [아두이노] {line}")

                except Exception as e:
                    print(f"데이터 처리 오류: {e}")
                    continue

            time.sleep(0.05)  # CPU 부하 감소

    except KeyboardInterrupt:
        print("\n\n사용자가 종료했습니다 (Ctrl+C)")

    except serial.SerialException as e:
        print(f"\n❌ 시리얼 포트 오류: {e}")
        print(f"   - 포트 '{config.ARDUINO_PORT}'가 올바른지 확인하세요")
        print(f"   - 아두이노가 연결되어 있는지 확인하세요")
        print(f"   - 다른 프로그램이 포트를 사용 중이지 않은지 확인하세요")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            # 정지 명령 및 종료
            arduino.write(b'S')
            time.sleep(0.5)
            arduino.close()
            print("\n✅ 모터 정지 및 아두이노 연결 종료")
        except:
            pass


if __name__ == "__main__":
    test_ultrasonic_motor()
