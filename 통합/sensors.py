"""
-------------------------------------------------------------------
  FILE NAME: sensors.py
  센서 데이터 처리 모듈

  기능:
  1) 카메라 차선 인식
  2) 라이다 장애물 감지
  3) 초음파 센서 거리 측정
  4) 센서 초기화
-------------------------------------------------------------------
  Generated: 2025-12-29
-------------------------------------------------------------------
"""

import Function_Library as fl
from Lib_LiDAR import libLidar
import config

# ==================== 전역 변수 (센서 객체) ====================
camera = None
lidar = None
arduino = None
ultrasonic_distance = 0

# ==================== 초기화 함수 ====================
def initialize():
    """
    모든 센서 및 통신 초기화

    Returns:
        ch0, ch1: 카메라 채널 객체
    """
    global camera, lidar, arduino

    print("=" * 50)
    print("자율주행 시스템 초기화 중...")
    print("=" * 50)

    # 1. 카메라 초기화
    print("\n[1/3] 카메라 초기화...")
    camera = fl.libCAMERA()
    ch0, ch1 = camera.initial_setting(capnum=config.CAMERA_COUNT)
    print("✓ 카메라 초기화 완료")

    # 2. 라이다 초기화
    print("\n[2/3] 라이다 초기화...")
    lidar = libLidar(config.LIDAR_PORT)
    lidar.init()
    print("✓ 라이다 초기화 완료")

    # 3. 아두이노 초기화
    print("\n[3/3] 아두이노 초기화...")
    arduino_lib = fl.libARDUINO()
    arduino = arduino_lib.init(config.ARDUINO_PORT, config.BAUDRATE)
    print("✓ 아두이노 초기화 완료")

    print("\n" + "=" * 50)
    print("모든 시스템 초기화 완료!")
    print("=" * 50 + "\n")

    return ch0, ch1


# ==================== 카메라 센서 ====================
def get_lane_direction(frame):
    """
    카메라로 차선 방향 감지

    Args:
        frame: OpenCV 영상 프레임

    Returns:
        int: FORWARD(0), LEFT(1), RIGHT(2) 또는 None

    처리 과정:
        1) 그레이스케일 변환
        2) 히스토그램 평탄화
        3) Canny Edge 감지
        4) Hough Line Transform
        5) 차선 기울기 분석
    """
    direction = camera.edge_detection(
        frame,
        width=config.LANE_WIDTH,
        height=config.LANE_HEIGHT,
        gap=config.LANE_GAP,
        threshold=config.LANE_THRESHOLD,
        print_enable=False
    )
    return direction


def get_traffic_light(frame):
    """
    신호등 색상 감지

    Args:
        frame: OpenCV 영상 프레임

    Returns:
        str: "RED", "GREEN", "YELLOW", "BLUE" 또는 None

    처리 과정:
        1) HSV 색상 필터링
        2) Hough Circle Transform
        3) 원 중심 주변 픽셀 색상 검증
    """
    color = camera.object_detection(frame, sample=16, print_enable=False)
    return color


# ==================== 라이다 센서 ====================
def check_obstacle(scan_data):
    """
    라이다로 전방 장애물 감지

    Args:
        scan_data: 라이다 스캔 데이터 [[각도, 거리], ...]

    Returns:
        tuple: (장애물_있음: bool, 가장_가까운_거리: int)

    예시:
        (True, 245) → 245mm 거리에 장애물 있음
        (False, 0) → 장애물 없음
    """
    # 전방 범위 내에서 위험 거리 이내의 장애물 검색
    obstacles = lidar.getAngleDistanceRange(
        scan_data,
        config.OBSTACLE_ANGLE_MIN,  # 350도
        config.OBSTACLE_ANGLE_MAX,  # 10도
        0,
        config.OBSTACLE_DISTANCE    # 500mm
    )

    has_obstacle = len(obstacles) > 0
    nearest_distance = 0

    if has_obstacle:
        # 가장 가까운 장애물 찾기
        nearest_obj = lidar.get_near_distance(
            scan_data,
            config.OBSTACLE_ANGLE_MIN,
            config.OBSTACLE_ANGLE_MAX
        )
        nearest_distance = int(nearest_obj[1]) if len(nearest_obj) > 1 else 0

    return has_obstacle, nearest_distance


def get_lidar_scanning():
    """
    라이다 스캔 제너레이터 반환

    Returns:
        generator: 라이다 스캔 데이터를 계속 생성

    사용법:
        for scan in get_lidar_scanning():
            # scan 데이터 처리
    """
    return lidar.scanning()


# ==================== 초음파 센서 ====================
def read_ultrasonic():
    """
    아두이노에서 초음파 센서 거리 읽기

    Returns:
        int: 거리 (mm)

    동작:
        - 아두이노가 시리얼로 보낸 거리값 수신
        - 데이터가 없으면 이전 값 반환
    """
    global ultrasonic_distance

    if arduino.in_waiting > 0:
        try:
            data = arduino.readline().decode('utf-8').strip()
            if data.isdigit():
                ultrasonic_distance = int(data)
        except:
            pass

    return ultrasonic_distance


# ==================== 카메라 읽기 ====================
def read_camera(ch0, ch1=None):
    """
    카메라 영상 읽기

    Args:
        ch0: 카메라 채널 0
        ch1: 카메라 채널 1 (선택 사항)

    Returns:
        tuple: (ret0, frame0, ret1, frame1)
               카메라 1개면 ret1=None, frame1=None
    """
    if config.CAMERA_COUNT == 1:
        ret0, frame0 = camera.camera_read(ch0)
        return ret0, frame0, None, None
    else:
        ret0, frame0, ret1, frame1 = camera.camera_read(ch0, ch1)
        return ret0, frame0, ret1, frame1


def show_camera_image(frame0, frame1=None):
    """
    카메라 영상 표시

    Args:
        frame0: 카메라 0 영상
        frame1: 카메라 1 영상 (선택 사항)
    """
    if config.SHOW_VIDEO:
        camera.image_show(frame0, frame1)


def check_quit_key():
    """
    'q' 키 입력 확인

    Returns:
        bool: True면 종료 요청
    """
    return camera.loop_break()


# ==================== 종료 함수 ====================
def cleanup():
    """
    센서 및 통신 종료

    동작:
        1) 라이다 정지
        2) 아두이노 포트 닫기
    """
    print("\n센서 시스템 종료 중...")
    try:
        lidar.stop()
        arduino.close()
    except:
        pass
    print("✓ 센서 시스템 종료 완료")
