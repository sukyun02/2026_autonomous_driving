"""
-------------------------------------------------------------------
  FILE NAME: test_lidar.py
  라이다 센서 단독 테스트 프로그램

  기능:
  - 라이다 센서만 테스트
  - 360도 스캔 데이터 실시간 출력
  - 장애물 감지 테스트
  - 카메라, 아두이노 없이 실행 가능

  실행 방법:
    python test_lidar.py

  종료 방법:
    Ctrl + C
-------------------------------------------------------------------
  Generated: 2025-12-29
-------------------------------------------------------------------
"""

from modules.lidar.Lib_LiDAR import libLidar
import time

# ==================== 설정 ====================
LIDAR_PORT = 'COM3'  # 라이다 포트 (장치 관리자에서 확인)

# 장애물 감지 설정
OBSTACLE_ANGLE_MIN = 350    # 전방 감지 시작 각도
OBSTACLE_ANGLE_MAX = 10     # 전방 감지 끝 각도
OBSTACLE_DISTANCE = 500     # 위험 거리 (mm)

# 출력 설정
PRINT_INTERVAL = 10         # 몇 프레임마다 출력할지
SHOW_ALL_POINTS = False     # True면 모든 포인트 출력, False면 요약만

# ==================== 라이다 초기화 ====================
def initialize_lidar():
    """라이다 센서 초기화"""
    print("=" * 60)
    print("🛰️  라이다 센서 테스트 프로그램")
    print("=" * 60)
    print(f"\n라이다 포트: {LIDAR_PORT}")
    print("초기화 중...\n")

    try:
        lidar = libLidar(LIDAR_PORT)
        lidar.init()

        # 라이다 모터 시작 (중요!)
        print("\n라이다 모터 시작 중...")
        lidar.lidar.start_motor()
        print("✓ 모터 시작됨")

        time.sleep(2)  # 모터 안정화 대기

        print("\n✅ 라이다 초기화 완료!")
        print("=" * 60)
        return lidar
    except Exception as e:
        print(f"\n❌ 라이다 초기화 실패: {e}")
        print("\n해결 방법:")
        print("1. 라이다가 USB에 연결되어 있는지 확인")
        print("2. 장치 관리자에서 포트 번호 확인 (COM3, COM4 등)")
        print("3. 다른 프로그램에서 라이다를 사용 중인지 확인")
        return None


# ==================== 스캔 데이터 분석 ====================
def analyze_scan(scan):
    """
    스캔 데이터 분석

    Args:
        scan: 라이다 스캔 데이터 [[각도, 거리], ...]

    Returns:
        dict: 분석 결과
    """
    if len(scan) == 0:
        return {
            'total_points': 0,
            'min_distance': 0,
            'max_distance': 0,
            'avg_distance': 0
        }

    distances = scan[:, 1]  # 거리값만 추출

    return {
        'total_points': len(scan),
        'min_distance': int(distances.min()),
        'max_distance': int(distances.max()),
        'avg_distance': int(distances.mean())
    }


# ==================== 전방 장애물 감지 ====================
def check_front_obstacle(lidar, scan):
    """
    전방 장애물 감지

    Args:
        lidar: 라이다 객체
        scan: 스캔 데이터

    Returns:
        tuple: (장애물_있음, 가장_가까운_거리, 각도)
    """
    # 전방 범위에서 장애물 검색
    obstacles = lidar.getAngleDistanceRange(
        scan,
        OBSTACLE_ANGLE_MIN,
        OBSTACLE_ANGLE_MAX,
        0,
        OBSTACLE_DISTANCE
    )

    if len(obstacles) > 0:
        # 가장 가까운 장애물 찾기
        nearest = lidar.get_near_distance(scan, OBSTACLE_ANGLE_MIN, OBSTACLE_ANGLE_MAX)
        angle = nearest[0]
        distance = int(nearest[1])
        return True, distance, angle
    else:
        return False, 0, 0


# ==================== 특정 방향 거리 확인 ====================
def check_direction_distance(lidar, scan, angle_min, angle_max):
    """
    특정 방향의 평균 거리 확인

    Args:
        lidar: 라이다 객체
        scan: 스캔 데이터
        angle_min: 시작 각도
        angle_max: 끝 각도

    Returns:
        int: 평균 거리 (mm)
    """
    data = lidar.getAngleRange(scan, angle_min, angle_max)
    if len(data) > 0:
        return int(data[:, 1].mean())
    else:
        return 0


# ==================== 메인 테스트 루프 ====================
def test_lidar_loop(lidar):
    """라이다 테스트 메인 루프"""
    print("\n" + "=" * 60)
    print("📡 라이다 스캔 시작!")
    print("종료: Ctrl + C")
    print("=" * 60 + "\n")

    frame_count = 0

    try:
        for scan in lidar.scanning():
            frame_count += 1

            # 스캔 데이터 분석
            analysis = analyze_scan(scan)

            # 전방 장애물 감지
            has_obstacle, obstacle_dist, obstacle_angle = check_front_obstacle(lidar, scan)

            # 좌/우/후방 거리 확인
            left_dist = check_direction_distance(lidar, scan, 270, 290)      # 좌측
            right_dist = check_direction_distance(lidar, scan, 70, 90)       # 우측
            rear_dist = check_direction_distance(lidar, scan, 170, 190)      # 후방

            # 출력 (일정 간격마다)
            if frame_count % PRINT_INTERVAL == 0:
                print(f"\n{'='*60}")
                print(f"🔄 프레임: {frame_count}")
                print(f"{'='*60}")

                # 스캔 데이터 요약
                print(f"\n📊 스캔 데이터:")
                print(f"   포인트 수: {analysis['total_points']:,}개")
                print(f"   최소 거리: {analysis['min_distance']:,} mm")
                print(f"   최대 거리: {analysis['max_distance']:,} mm")
                print(f"   평균 거리: {analysis['avg_distance']:,} mm")

                # 방향별 거리
                print(f"\n🧭 방향별 거리:")
                print(f"   전방 (350~10°):  ", end="")
                if has_obstacle:
                    print(f"⚠️  {obstacle_dist:,} mm (각도: {obstacle_angle:.1f}°)")
                else:
                    print(f"✅ 안전 (>{OBSTACLE_DISTANCE} mm)")

                print(f"   좌측 (270~290°): {left_dist:,} mm" if left_dist > 0 else "   좌측 (270~290°): - mm")
                print(f"   우측 (70~90°):   {right_dist:,} mm" if right_dist > 0 else "   우측 (70~90°):   - mm")
                print(f"   후방 (170~190°): {rear_dist:,} mm" if rear_dist > 0 else "   후방 (170~190°): - mm")

                # 장애물 경고
                if has_obstacle:
                    print(f"\n🚨 경고: 전방 {obstacle_dist} mm 거리에 장애물!")

            # 모든 포인트 출력 (옵션)
            if SHOW_ALL_POINTS and frame_count % PRINT_INTERVAL == 0:
                print(f"\n📍 스캔 포인트 (처음 10개):")
                for i, point in enumerate(scan[:10]):
                    angle, distance = point
                    print(f"   [{i}] 각도: {angle:6.2f}°, 거리: {int(distance):5,} mm")
                if len(scan) > 10:
                    print(f"   ... 외 {len(scan) - 10}개 포인트")

            # CPU 부하 감소
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n\n🛑 사용자가 테스트를 중단했습니다 (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


# ==================== 메인 실행 ====================
if __name__ == "__main__":
    lidar = None

    try:
        # 라이다 초기화
        lidar = initialize_lidar()

        if lidar is None:
            print("\n프로그램을 종료합니다.")
            exit(1)

        # 테스트 시작
        test_lidar_loop(lidar)

    finally:
        # 라이다 정리
        if lidar is not None:
            print("\n라이다 센서 종료 중...")
            try:
                lidar.stop()
                print("✅ 라이다 센서 종료 완료")
            except:
                pass

        print("\n프로그램 종료\n")
