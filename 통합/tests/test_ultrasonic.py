# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------
  초음파 센서 6개 테스트 프로그램

  목적: 아두이노와 초음파 센서 6개가 정상 작동하는지 테스트

  실행 방법:
    python tests/test_ultrasonic.py

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

def test_ultrasonic():
    """초음파 센서 6개 테스트"""
    print("=" * 60)
    print("초음파 센서 6개 테스트 프로그램")
    print("=" * 60)
    print(f"포트: {config.ARDUINO_PORT}")
    print(f"통신 속도: {config.BAUDRATE}")
    print("종료: Ctrl + C")
    print("-" * 60)

    try:
        # 아두이노 연결
        print("\n아두이노 연결 중...")
        arduino = serial.Serial(config.ARDUINO_PORT, config.BAUDRATE, timeout=1)
        time.sleep(2)  # 아두이노 초기화 대기
        print("✓ 아두이노 연결 완료\n")

        # 초기 버퍼 비우기
        arduino.reset_input_buffer()

        print("=" * 60)
        print("초음파 센서 데이터 수신 중...")
        print("=" * 60)
        print("위치 약어: F=전방, FL=좌전방, FR=우전방, R=후방, RL=좌후방, RR=우후방")
        print("-" * 60)

        frame_count = 0

        while True:
            if arduino.in_waiting > 0:
                try:
                    # 데이터 읽기
                    line = arduino.readline().decode('utf-8').strip()

                    # 형식: "F:25,FL:30,FR:28,R:50,RL:45,RR:48"
                    if ':' in line and ',' in line:
                        frame_count += 1

                        # 파싱
                        sensor_data = {}
                        parts = line.split(',')
                        for part in parts:
                            if ':' in part:
                                key, value = part.split(':')
                                sensor_data[key] = int(value)

                        # 화면 출력 (매 프레임) - TX 핀 번호와 센서 번호로 표시
                        print(f"\n[프레임 {frame_count}]")
                        print(f"  TX 23 (번호 1): {sensor_data.get('F', 0):3d} cm")
                        print(f"  TX 25 (번호 2): {sensor_data.get('FL', 0):3d} cm")
                        print(f"  TX 27 (번호 3): {sensor_data.get('FR', 0):3d} cm")
                        print(f"  TX 29 (번호 4): {sensor_data.get('R', 0):3d} cm")
                        print(f"  TX 31 (번호 5): {sensor_data.get('RL', 0):3d} cm")
                        print(f"  TX 33 (번호 6): {sensor_data.get('RR', 0):3d} cm")

                        # 경고 (안전 거리 이내)
                        safe_dist = config.ULTRASONIC_SAFE_DISTANCE / 10  # mm → cm
                        warnings = []
                        for key, value in sensor_data.items():
                            if value > 0 and value < safe_dist:
                                warnings.append(f"{key}:{value}cm")

                        if warnings:
                            print(f"\n  경고: {', '.join(warnings)} - 안전거리({safe_dist}cm) 이내!")

                    # 구버전 형식 (단일 숫자)
                    elif line.isdigit():
                        frame_count += 1
                        distance = int(line)
                        print(f"[프레임 {frame_count}] 전방: {distance} cm")

                except Exception as e:
                    print(f"데이터 파싱 오류: {e}")
                    continue

            time.sleep(0.01)  # CPU 부하 감소

    except KeyboardInterrupt:
        print("\n\n사용자가 종료했습니다 (Ctrl+C)")

    except serial.SerialException as e:
        print(f"\n❌ 시리얼 포트 오류: {e}")
        print(f"   - 포트 '{config.ARDUINO_PORT}'가 올바른지 확인하세요 (장치 관리자)")
        print(f"   - 아두이노가 연결되어 있는지 확인하세요")
        print(f"   - 다른 프로그램이 포트를 사용 중이지 않은지 확인하세요")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            arduino.close()
            print("\n✅ 아두이노 연결 종료")
        except:
            pass

if __name__ == "__main__":
    test_ultrasonic()
