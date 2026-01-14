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

from utils import Function_Library as fl
from lidar.Lib_LiDAR import libLidar
import config

# ==================== 전역 변수 (센서 객체) ====================
camera = None
lidar = None
arduino = None
ultrasonic_distance = 0  # 구버전 호환용 (단일 값)

# 초음파 센서 6개 데이터 저장 딕셔너리
ultrasonic_data = {
    'F': 0,      # Front (전방)
    'FL': 0,     # Front-Left (좌전방)
    'FR': 0,     # Front-Right (우전방)
    'R': 0,      # Rear (후방)
    'RL': 0,     # Rear-Left (좌후방)
    'RR': 0      # Rear-Right (우후방)
}

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
    아두이노에서 6개 초음파 센서 거리 읽기

    Arduino 전송 형식: "F:25,FL:30,FR:28,R:50,RL:45,RR:48"

    Returns:
        dict: 6개 센서 거리 딕셔너리 (단위: cm)
              {'F': 25, 'FL': 30, 'FR': 28, 'R': 50, 'RL': 45, 'RR': 48}
              데이터가 없으면 이전 값 반환

    동작:
        1) 시리얼 포트에 데이터가 있는지 확인
        2) 한 줄 읽기 (newline까지)
        3) "key:value,key:value,..." 형식 파싱
        4) 딕셔너리로 변환하여 전역 변수 업데이트
        5) 구버전 호환 (단일 숫자만 오면 'F' 키에 저장)
    """
    global ultrasonic_data, ultrasonic_distance
    

    # 시리얼 버퍼에 데이터가 있는지 확인
    if arduino.in_waiting > 0:
        try:
            # 한 줄 읽기 (\n까지 읽고 디코딩)
            line = arduino.readline().decode('utf-8').strip() #결과 예시 "F:25,FL:30,FR:28,R:50,RL:45,RR:48"

            # 형식 1: "F:25,FL:30,..." (신규 6개 센서 형식)
            if ':' in line and ',' in line:
                # 쉼표로 분리: ["F:25", "FL:30", "FR:28", ...]
                parts = line.split(',')

                # 각 부분을 "key:value"로 분리하여 딕셔너리 생성
                for part in parts:
                    if ':' in part:  # 안전성 체크
                        key, value = part.split(':')
                        # 문자열을 정수로 변환하여 저장
                        ultrasonic_data[key] = int(value)

                # 구버전 호환: 전방 센서값을 단일 변수에도 저장
                ultrasonic_distance = ultrasonic_data.get('F', 0)

            # 형식 2: "123" (구버전 단일 숫자 - Exercise_1.ino 호환)
            elif line.isdigit():
                distance_value = int(line)
                # 전방 센서로 간주
                ultrasonic_data['F'] = distance_value
                ultrasonic_distance = distance_value

        except Exception as e:
            # 파싱 오류 시 무시 (이전 값 유지)
            pass

    # 딕셔너리 반환 (6개 센서 데이터)
    return ultrasonic_data


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
