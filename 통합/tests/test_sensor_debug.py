# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------
  초음파 센서 디버깅 프로그램

  목적: 6개 센서가 모두 정상적으로 데이터를 전송하는지 확인

  실행 방법:
    python tests/test_sensor_debug.py
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

def test_sensor_debug():
    """센서 디버깅"""
    print("=" * 70)
    print("초음파 센서 6개 디버깅 프로그램")
    print("=" * 70)
    print(f"포트: {config.ARDUINO_PORT}")
    print(f"통신 속도: {config.BAUDRATE}")
    print("=" * 70)
    print("\n이 프로그램은 아두이노에서 받는 원시 데이터를 그대로 출력합니다.")
    print("종료: Ctrl + C\n")
    print("-" * 70)

    try:
        # 아두이노 연결
        print("\n아두이노 연결 중...")
        arduino = serial.Serial(config.ARDUINO_PORT, config.BAUDRATE, timeout=1)
        time.sleep(2)
        print("✓ 아두이노 연결 완료\n")

        # 버퍼 비우기
        arduino.reset_input_buffer()

        print("=" * 70)
        print("데이터 수신 시작 (원시 데이터)")
        print("=" * 70)

        line_count = 0

        while True:
            if arduino.in_waiting > 0:
                try:
                    # 원시 데이터 읽기
                    line = arduino.readline().decode('utf-8').strip()

                    if line:
                        line_count += 1
                        print(f"\n[{line_count}] 원시 데이터: {line}")

                        # 데이터 파싱 시도
                        if ':' in line and ',' in line:
                            print("  → 6개 센서 형식 감지!")
                            parts = line.split(',')
                            print(f"  → 분리된 데이터 개수: {len(parts)}개")

                            for i, part in enumerate(parts, 1):
                                print(f"     [{i}] {part}")

                                if ':' in part:
                                    key, value = part.split(':')
                                    print(f"         키: '{key}', 값: '{value}'")

                                    # 센서 이름 매핑
                                    sensor_names = {
                                        'F': '1번(전방)',
                                        'FL': '2번(좌전방)',
                                        'FR': '3번(우전방)',
                                        'R': '4번(후방)',
                                        'RL': '5번(좌후방)',
                                        'RR': '6번(우후방)'
                                    }

                                    sensor_name = sensor_names.get(key, '알 수 없음')
                                    print(f"         => {sensor_name}: {value} cm")

                        elif line.isdigit():
                            print("  → 단일 숫자 형식 (구버전)")
                            print(f"  → 값: {line} cm")

                        else:
                            print("  → 아두이노 메시지 또는 알 수 없는 형식")

                except Exception as e:
                    print(f"❌ 에러: {e}")
                    import traceback
                    traceback.print_exc()

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n\n사용자가 종료했습니다 (Ctrl+C)")

    except serial.SerialException as e:
        print(f"\n❌ 시리얼 포트 오류: {e}")
        print(f"   - 포트 '{config.ARDUINO_PORT}'가 올바른지 확인하세요")

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
    test_sensor_debug()
