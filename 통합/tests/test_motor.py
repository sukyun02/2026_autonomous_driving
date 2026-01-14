"""
-------------------------------------------------------------------
  모터 제어 테스트 프로그램

  목적: 아두이노 모터 제어(DC모터 + 서보모터)가 정상 작동하는지 테스트

  실행 방법:
    python tests/test_motor.py

  사용법:
    - W/S: 전진/정지
    - A/D: 좌회전/우회전
    - X: 후진
    - Q: 종료
-------------------------------------------------------------------
"""

import serial
import time
import sys
import os
import msvcrt  # Windows 키보드 입력

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config

def test_motor():
    """모터 제어 테스트"""
    print("=" * 60)
    print("모터 제어 테스트 프로그램")
    print("=" * 60)
    print(f"포트: {config.ARDUINO_PORT}")
    print(f"통신 속도: {config.BAUDRATE}")
    print("=" * 60)
    print("조작법:")
    print("  W - 전진 (Forward)")
    print("  A - 좌회전 (Left)")
    print("  D - 우회전 (Right)")
    print("  X - 후진 (Backward)")
    print("  S - 정지 (Stop)")
    print("  Q - 종료 (Quit)")
    print("=" * 60)

    try:
        # 아두이노 연결
        print("\n아두이노 연결 중...")
        arduino = serial.Serial(config.ARDUINO_PORT, config.BAUDRATE, timeout=1)
        time.sleep(2)  # 아두이노 초기화 대기
        print("✓ 아두이노 연결 완료\n")

        # 초기 정지
        arduino.write(b'S')
        print("초기 상태: 정지 (S)\n")

        print("키보드로 조작하세요! (Q=종료)")
        print("-" * 60)

        current_command = 'S'

        while True:
            # 키 입력 확인 (non-blocking)
            if msvcrt.kbhit():
                key = msvcrt.getch().decode('utf-8').upper()

                # 종료
                if key == 'Q':
                    print("\n종료 명령 수신")
                    arduino.write(b'S')  # 정지 후 종료
                    break

                # 명령 매핑
                command_map = {
                    'W': ('F', '전진 (Forward)'),
                    'A': ('L', '좌회전 (Left)'),
                    'D': ('R', '우회전 (Right)'),
                    'X': ('B', '후진 (Backward)'),
                    'S': ('S', '정지 (Stop)')
                }

                if key in command_map:
                    command, description = command_map[key]
                    arduino.write(command.encode())
                    current_command = command
                    print(f"[명령 전송] {command} - {description}")

            # 아두이노에서 데이터 수신 (초음파 센서 등)
            if arduino.in_waiting > 0:
                try:
                    line = arduino.readline().decode('utf-8').strip()
                    if line:
                        print(f"  [아두이노] {line}")
                except:
                    pass

            time.sleep(0.05)  # CPU 부하 감소

    except KeyboardInterrupt:
        print("\n\n사용자가 종료했습니다 (Ctrl+C)")

    except serial.SerialException as e:
        print(f"\n❌ 시리얼 포트 오류: {e}")
        print(f"   - 포트 '{config.ARDUINO_PORT}'가 올바른지 확인하세요 (장치 관리자)")
        print(f"   - 아두이노가 연결되어 있는지 확인하세요")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            # 정지 명령
            arduino.write(b'S')
            time.sleep(0.5)
            arduino.close()
            print("\n✅ 모터 정지 및 아두이노 연결 종료")
        except:
            pass

if __name__ == "__main__":
    test_motor()
