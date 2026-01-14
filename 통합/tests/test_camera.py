"""
-------------------------------------------------------------------
  카메라 2대 테스트 프로그램

  목적: 카메라 2대가 정상 작동하고 차선 인식이 되는지 테스트

  실행 방법:
    python tests/test_camera.py

  종료 방법:
    'q' 키 입력
-------------------------------------------------------------------
"""

import cv2
import sys
import os
import numpy as np

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import Function_Library as fl
import config

def test_camera():
    """카메라 테스트"""
    print("=" * 60)
    print("카메라 2대 + 차선 인식 테스트 프로그램")
    print("=" * 60)
    print(f"카메라 개수: {config.CAMERA_COUNT}")
    print("종료: 'q' 키")
    print("-" * 60)

    camera = None
    ch0, ch1 = None, None

    try:
        # 카메라 초기화
        print("\n카메라 초기화 중...")
        camera = fl.libCAMERA()
        ch0, ch1 = camera.initial_setting(capnum=config.CAMERA_COUNT)
        print("✓ 카메라 초기화 완료\n")

        print("=" * 60)
        print("카메라 영상 표시 중...")
        print("=" * 60)
        print("- 녹색 창: 원본 영상")
        print("- 'q' 키를 누르면 종료")
        print("-" * 60)

        frame_count = 0

        while True:
            frame_count += 1

            # 카메라 읽기
            if config.CAMERA_COUNT == 1:
                ret0, frame0 = camera.camera_read(ch0)
                ret1, frame1 = None, None
            else:
                ret0, frame0, ret1, frame1 = camera.camera_read(ch0, ch1)

            if not ret0:
                print("카메라 0 읽기 실패!")
                break

            # 차선 방향 감지
            direction = camera.edge_detection(
                frame0,
                width=config.LANE_WIDTH,
                height=config.LANE_HEIGHT,
                gap=config.LANE_GAP,
                threshold=config.LANE_THRESHOLD,
                print_enable=False
            )

            # 방향 텍스트 표시
            direction_names = {
                fl.FORWARD: "FORWARD (직진)",
                fl.LEFT: "LEFT (좌회전)",
                fl.RIGHT: "RIGHT (우회전)",
                None: "UNKNOWN (인식 실패)"
            }
            direction_text = direction_names.get(direction, "UNKNOWN")

            # 프레임에 정보 표시
            cv2.putText(frame0, f"Frame: {frame_count}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame0, f"Direction: {direction_text}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # 영상 표시
            camera.image_show(frame0, frame1)

            # 상태 출력 (10프레임마다)
            if frame_count % 10 == 0:
                print(f"[프레임 {frame_count}] 차선 방향: {direction_text}")

            # 종료 확인
            if camera.loop_break():
                print("\n사용자가 종료했습니다 ('q' 키)")
                break

    except KeyboardInterrupt:
        print("\n\n사용자가 종료했습니다 (Ctrl+C)")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 카메라 해제
        try:
            if ch0 is not None:
                ch0.release()
            if ch1 is not None:
                ch1.release()
            cv2.destroyAllWindows()
            print("\n✅ 카메라 종료 완료")
        except:
            pass

if __name__ == "__main__":
    test_camera()
