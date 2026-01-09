"""
-------------------------------------------------------------------
  FILE NAME: test_lidar_visual.py
  라이다 센서 시각화 테스트 프로그램

  기능:
  - 라이다 360도 스캔 실시간 시각화
  - matplotlib로 극좌표 그래프 표시
  - 장애물 감지 영역 표시
  - 거리별 색상 구분

  실행 방법:
    python test_lidar_visual.py

  종료 방법:
    창 닫기 또는 Ctrl + C
-------------------------------------------------------------------
"""

from modules.lidar.Lib_LiDAR import libLidar
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Wedge
import time

# ==================== 설정 ====================
LIDAR_PORT = 'COM3'  # 라이다 포트

# 장애물 감지 설정 (180도를 정면으로 설정)
OBSTACLE_ANGLE_MIN = 170    # 전방 감지 시작 (180도 기준 좌측 10도)
OBSTACLE_ANGLE_MAX = 190    # 전방 감지 끝 (180도 기준 우측 10도)
OBSTACLE_DISTANCE = 500     # 위험 거리 (mm)

# 시각화 설정
MAX_DISPLAY_DISTANCE = 3000  # 최대 표시 거리 (mm)
UPDATE_INTERVAL = 50         # 업데이트 간격 (ms)
DISPLAY_ANGLE_MIN = 90       # 시각화 표시 최소 각도 (왼쪽)
DISPLAY_ANGLE_MAX = 270      # 시각화 표시 최대 각도 (오른쪽)

# ==================== 전역 변수 ====================
lidar = None
scan_data = {'angles': [], 'distances': []}
obstacle_detected = False
nearest_obstacle = 0

# ==================== 라이다 초기화 ====================
def initialize_lidar():
    """라이다 센서 초기화"""
    global lidar

    print("=" * 60)
    print("🛰️  라이다 센서 실시간 시각화")
    print("=" * 60)
    print(f"\n라이다 포트: {LIDAR_PORT}")
    print("초기화 중...\n")

    try:
        lidar = libLidar(LIDAR_PORT)
        lidar.init()

        print("\n✅ 라이다 초기화 완료!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n❌ 라이다 초기화 실패: {e}")
        print("\n해결 방법:")
        print("1. 라이다가 USB에 연결되어 있는지 확인")
        print("2. 장치 관리자에서 포트 번호 확인")
        print("3. 다른 프로그램에서 라이다 사용 중인지 확인")
        return False

# ==================== 스캔 데이터 수집 ====================
def scan_worker():
    """백그라운드에서 스캔 데이터 수집"""
    global scan_data, obstacle_detected, nearest_obstacle

    try:
        print("\n📡 스캔 시작...")

        # 이 스레드에서 직접 라이다 초기화 (test_lidar.py 방식)
        print("라이다 초기화 중...")
        lidar_local = libLidar(LIDAR_PORT)
        lidar_local.init()
        print("✅ 라이다 초기화 완료!")

        # Lib_LiDAR의 scanning() 메서드 사용
        for scan in lidar_local.scanning():
            # scan은 numpy array: [[각도, 거리], ...]
            if len(scan) == 0:
                continue

            # 각도와 거리 분리
            angles = scan[:, 0].tolist()
            distances = scan[:, 1].tolist()

            # 전역 변수 업데이트
            scan_data['angles'] = angles
            scan_data['distances'] = distances

            # 장애물 감지 (170~190도 범위)
            obstacle_detected = False
            nearest_obstacle = 0

            for angle, distance in zip(angles, distances):
                # 전방 영역 체크 (170~190도)
                if (OBSTACLE_ANGLE_MIN <= angle <= OBSTACLE_ANGLE_MAX):
                    if distance < OBSTACLE_DISTANCE:
                        obstacle_detected = True
                        if nearest_obstacle == 0 or distance < nearest_obstacle:
                            nearest_obstacle = distance

    except Exception as e:
        print(f"\n❌ 스캔 오류: {e}")
        import traceback
        traceback.print_exc()

# ==================== 시각화 설정 ====================
def setup_plot():
    """matplotlib 극좌표 플롯 설정"""
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='polar')

    # 플롯 설정
    ax.set_ylim(0, MAX_DISPLAY_DISTANCE)
    ax.set_theta_zero_location('N')  # 0도를 위쪽으로
    ax.set_theta_direction(-1)        # 시계방향

    # 시야각 제한 (90~270도만 표시 = 전방 180도)
    ax.set_thetamin(DISPLAY_ANGLE_MIN)  # 90도 (왼쪽)
    ax.set_thetamax(DISPLAY_ANGLE_MAX)  # 270도 (오른쪽)

    # 격자선 설정
    ax.grid(True, linestyle='--', alpha=0.5)

    # 제목
    ax.set_title('라이다 전방 180도 스캔 (실시간)\n정면: 180도 | 감지 범위: 170~190도',
                 fontsize=16, fontweight='bold', pad=20)

    # 거리 표시
    distance_labels = [500, 1000, 1500, 2000, 2500, 3000]
    ax.set_yticks(distance_labels)
    ax.set_yticklabels([f'{d}mm' for d in distance_labels])

    return fig, ax


# ==================== 애니메이션 업데이트 ====================
def update_plot(frame, ax, scatter, obstacle_wedge, text_box):
    """프레임마다 플롯 업데이트"""
    global scan_data, obstacle_detected, nearest_obstacle

    if len(scan_data['angles']) == 0:
        return scatter, *obstacle_wedge, text_box

    # 각도를 라디안으로 변환
    angles_rad = np.deg2rad(scan_data['angles'])
    distances = np.array(scan_data['distances'])

    # 거리에 따라 색상 지정
    colors = []
    for d in distances:
        if d < 500:
            colors.append('red')
        elif d < 1000:
            colors.append('orange')
        elif d < 2000:
            colors.append('yellow')
        else:
            colors.append('green')

    # 스캔 포인트 업데이트
    scatter.set_offsets(np.c_[angles_rad, distances])
    scatter.set_color(colors)
    scatter.set_sizes([20] * len(angles_rad))

    # ✅ 이전 wedge들 제거 (안전하게)
    for w in obstacle_wedge[:]:  # 복사본으로 순회
        try:
            w.remove()
        except:
            pass  # 이미 제거됐으면 무시

    # ✅ 리스트를 비우고 새 wedge 추가 (in-place 수정)
    obstacle_wedge.clear()

    # 170~190도 영역 (전방 20도, 180도 중심)
    wedge_color = 'red' if obstacle_detected else 'lightblue'
    wedge_alpha = 0.3 if obstacle_detected else 0.1

    # 새 wedge 생성 (170~190도 단일 영역)
    new_wedge = Wedge(
        (0, 0),
        OBSTACLE_DISTANCE,
        OBSTACLE_ANGLE_MIN,  # 170도
        OBSTACLE_ANGLE_MAX,  # 190도
        facecolor=wedge_color,
        alpha=wedge_alpha,
        edgecolor='red',
        linewidth=2
    )

    # ✅ 리스트에 추가 (in-place)
    ax.add_patch(new_wedge)
    obstacle_wedge.append(new_wedge)

    # 상태 텍스트 업데이트
    status_text = f"포인트 수: {len(distances):,}개\n"

    if len(distances) > 0:
        status_text += f"최소 거리: {int(min(distances)):,} mm\n"
        status_text += f"최대 거리: {int(max(distances)):,} mm\n"
        status_text += f"평균 거리: {int(np.mean(distances)):,} mm\n"

    if obstacle_detected:
        status_text += f"\n⚠️ 전방 장애물!\n거리: {int(nearest_obstacle):,} mm"
    else:
        status_text += f"\n✅ 전방 안전"

    text_box.set_text(status_text)

    return scatter, *obstacle_wedge, text_box
# ==================== 메인 실행 ====================
def main():
    """메인 함수"""

    print("=" * 60)
    print("🛰️  라이다 센서 실시간 시각화")
    print("=" * 60)
    print(f"\n라이다 포트: {LIDAR_PORT}")
    print("=" * 60)

    # 스캔 시작 (백그라운드)
    import threading
    scan_thread = threading.Thread(target=scan_worker, daemon=True)
    scan_thread.start()

    # 시각화 준비
    print("\n🎨 시각화 창을 여는 중...")
    time.sleep(2)  # 라이다 초기화 및 첫 스캔 대기

    fig, ax = setup_plot()

    # 초기 플롯 요소
    scatter = ax.scatter([], [], c=[], s=20, alpha=0.6)

    # 초기 감지 영역 wedge (170~190도)
    initial_wedge = Wedge(
        (0, 0),
        OBSTACLE_DISTANCE,
        OBSTACLE_ANGLE_MIN,  # 170도
        OBSTACLE_ANGLE_MAX,  # 190도
        facecolor='lightblue',
        alpha=0.1,
        edgecolor='blue',
        linewidth=1
    )
    ax.add_patch(initial_wedge)
    obstacle_wedge = [initial_wedge]

    # 상태 텍스트
    text_box = ax.text(0.02, 0.98, '',
                       transform=fig.transFigure,
                       verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                       fontsize=10,
                       fontfamily='monospace')

    # 범례
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w',
                   markerfacecolor='red', markersize=10, label='< 500mm (위험)'),
        plt.Line2D([0], [0], marker='o', color='w',
                   markerfacecolor='orange', markersize=10, label='500~1000mm'),
        plt.Line2D([0], [0], marker='o', color='w',
                   markerfacecolor='yellow', markersize=10, label='1000~2000mm'),
        plt.Line2D([0], [0], marker='o', color='w',
                   markerfacecolor='green', markersize=10, label='> 2000mm (안전)')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

    # 애니메이션 시작
    ani = animation.FuncAnimation(
        fig,
        update_plot,
        fargs=(ax, scatter, obstacle_wedge, text_box),
        interval=UPDATE_INTERVAL,
        blit=False,
        cache_frame_data=False
    )

    print("✅ 시각화 시작!")
    print("창을 닫으면 종료됩니다.\n")

    try:
        plt.show()
    except KeyboardInterrupt:
        print("\n\n🛑 사용자가 중단했습니다")

    print("\n프로그램 종료\n")

if __name__ == "__main__":
    main()
