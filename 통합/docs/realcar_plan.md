# 실차 통합 문서 (정리본)

## 목적
- MORAI 기반 `ws-build-ai`를 실차 환경에 맞게 이식하기 위한 기준 문서.
- 대회 규정과 검증된 `2026_autonomous_driving` 코드의 동작을 함께 반영.

## 입력 자료
- 규정집: `/home/sukyun02/MORAI/2026_autonomous_driving/붙임 1. 「2026년 경기도 대학생 자율주행 경진대회 규정집」_v1.1.pdf`
- 실차 코드: `/home/sukyun02/MORAI/2026_autonomous_driving/통합`
- ROS1 베이스: `/home/sukyun02/MORAI/ws-build-ai`

## 규정 핵심 요약 (필수 반영)
### 차량/센서 설치 제한
- 대회에서 제시하는 차량/부품 사용.
- 센서 설치 범위: 전후 110cm, 좌우 60cm, 높이 75cm 이내.
- 센서 지그 제작 가능, 그 외 차량 개조 불허.

### 트랙/차선/미션 기본
- 도로 폭 850mm, 차선 폭 50mm, 출발선 폭 100mm.
- 횡단보도 1000mm x 100mm.
- 주차 공간 950mm x 1500mm.
- 차선: 흰색 선, 오른쪽 차선 따라 반시계 방향 주행.
- 출발: 출발 신호 후 노트북 키 입력으로 시작, 신호 이전 모터 구동 불가.

### 장애물 회피 구간
- 주차된 차량 3대.
- 첫 번째 장애물 위치 고정(내측 차선, 출발선 근처 OUT 연장선).
- 2, 3번째 장애물은 좌/우 차선 각 3개 후보 위치 중 랜덤(총 9가지).
- 장애물 구간에서는 중앙 차선 침범 페널티 없음.
- 종료 라인 통과 시 미션 성공.

### 횡단보도(신호등) 구간
- 접근 시 항상 빨간 신호등.
- 정차 후 심판이 임의 시점에 초록색으로 변경.
- 초록색 변경 후 5초 이내 출발 필요.
- 횡단보도 뒤쪽 종료 라인 통과 시 미션 성공.

## 결정 사항 (확정)
- 전원/출력 기준: 배터리 12V (최대 출력 12V).
- 카메라 2대 사용, 전방/후방 분리.
- 라이다는 전방 장애물 회피 용도.
- 아두이노 제어는 연속 값 기반(속도/조향)으로 확장.

## 메시지/드라이버 정책 (확정)
### 표준 메시지 매핑
- `morai_msgs/CtrlCmd` -> `ackermann_msgs/AckermannDrive`
- `morai_msgs/EgoVehicleStatus` -> `nav_msgs/Odometry`

### 실차 필수 메시지
- 카메라: `sensor_msgs/Image` 또는 `sensor_msgs/CompressedImage`
- 라이다: `sensor_msgs/LaserScan`
- 초음파: `sensor_msgs/Range` x6 또는 `std_msgs/Float32MultiArray`
- 신호등 상태: `std_msgs/String` 또는 `std_msgs/UInt8`
- 차선 오프셋/조향: `std_msgs/Float32`

### 라이다 드라이버 기준
- `rplidar` 라이브러리는 센서 드라이버이며 ROS 메시지와 분리.
- ROS에서는 `rplidar_ros` 사용, 출력은 `LaserScan`으로 통일.

## ROS1 통합 설계 (확정)
### 노드/토픽 구성
- Camera Driver (Front) -> `/camera/front/image`
- Camera Driver (Rear) -> `/camera/rear/image`
- Lane Tracking -> `/lane/steering_angle`, `/lane/center_offset`
- Traffic Light -> `/perception/traffic_light_state`
- LiDAR Driver -> `/scan`
- Ultrasonic Driver -> `/ultrasonic/ranges` 또는 `/ultrasonic/<pos>`
- Decision Node -> `/decision/cmd`
- Motor Driver -> `/arduino/cmd`

### 노드 책임
- Decision Node:
  - 입력: 차선/신호등/라이다/초음파
  - 출력: 속도+조향 명령
  - 규정 반영: 출발 지연/정지선 정차/신호 변경 후 5초 내 출발
- Motor Driver:
  - `/decision/cmd`를 아두이노 시리얼 명령으로 변환
  - 안전을 위해 초기 상태는 항상 정지

## 이식 절차 (권장 순서)
1) 문서/인터페이스 확정 ✅
2) ROS 스켈레톤 패키지 생성 ✅
3) 2026 코드 로직을 ROS 노드로 분리 이식 ✅
4) ws-build-ai 인지 결과와 결합하여 결정 로직 튜닝 ⚠️ (부분 완료, 실차 튜닝 필요)
5) 불필요한 MORAI 전용 코드 정리

## 확인 필요 항목 (미정)
- 실제 차량 치수와 센서 장착 위치(규정 범위 내 좌표 확정)
- 라이다/초음파 토픽 주기 및 처리 지연 허용치
- ROS 토픽 표준화 여부(표준 메시지 vs 커스텀 메시지)

## ROS 스켈레톤 패키지 생성 (완료)
### 생성 위치
- `/home/sukyun02/MORAI/ws-build-ai/src`

### 신규 패키지
- `bringup`
- `decision`
- `common`
- `msgs`
- `drivers/arduino_driver`
- `drivers/rplidar_driver`
- `drivers/ultrasonic_driver`

### 기존 패키지 처리
- `perception_pkg`, `planning_pkg`, `control_pkg`는 유지.
- 스켈레톤은 추가 생성만 수행하고 기존 폴더는 유지.

## 하드웨어 정보 필요 목록 (정확도 개선용)
- 아두이노 포트/baudrate: 예) `/dev/ttyUSB0`, `9600`
- 아두이노 명령 포맷: 문자(F/L/R/S) 유지 여부, 연속값 포맷(예: `V:<pwm>,S:<deg>`)
- 속도/조향 범위: PWM 범위(0~255), 서보 각도 범위(좌/우 최대 각)
- 라이다 모델명/드라이버: RPLiDAR 모델(A1/A2/A3 등), ROS1 드라이버 사용 여부
- 라이다 프레임/거리 범위: frame_id, min/max range
- 카메라 장치/토픽: 전방/후방 장치 경로, 이미지 형식(압축/비압축)
- 초음파 포맷: 아두이노 송신 문자열 형식, 단위(cm/m)
- 전원/안전 제한: 주행 속도 상한, 안전 정지 거리

## 최소 실행(MVP) 반영 항목
- Python 노드 설치 설정: `catkin_install_python()` 추가
- 의존성 관리: ROS 메시지 패키지 + `pyserial` 설치
- bringup 런치에 드라이버/decision 노드 연결
- 아두이노 포트/baud 파라미터 지정

## 신규 패키지 역할/구성
### bringup
- `launch/`: 트랙/장애물/주차 미션별 런치 파일.
- `config/`: 미션별 파라미터 YAML.

### decision
- `scripts/`: 2026 `control.py` 로직을 ROS 노드로 이식한 의사결정 노드.
- `config/`: 임계값/룰 기반 파라미터.

### common
- `scripts/`: 공통 유틸(예: 파라미터 로더, 변환 함수).
- `config/`: 공용 파라미터.

### msgs
- `msg/`: 커스텀 메시지 정의(필요 시).
- `srv/`: 커스텀 서비스 정의(필요 시).

### drivers/arduino_driver
- `scripts/`: 아두이노 시리얼 I/O 노드.
- `config/`: 시리얼 포트/baudrate/제어 범위.
- `launch/`: 드라이버 단독 런치.

### drivers/rplidar_driver
- `launch/`: `rplidar_ros` 실행 래퍼 런치.
- `config/`: 라이다 파라미터(프레임, 거리 범위 등).

### drivers/ultrasonic_driver
- `scripts/`: 초음파 파싱/퍼블리시 노드.
- `config/`: 센서 포지션/필터 임계값.
- `launch/`: 드라이버 단독 런치.

## 이식 절차 4번 상세 (ws-build-ai 인지 결과 결합)

### 현재 상태 (2026-01-21)
**✅ 완료된 부분:**
1. **차선 인식 연속값 전환**
   - 2026 코드: `FORWARD/LEFT/RIGHT` 이산 명령
   - ws-build-ai: 차선 중심 오프셋 기반 연속 조향각 (-1.0~1.0)
   - decision_node_2026이 연속값 조향각을 수신하여 처리

2. **인지 결과 통합 구조**
   - 라이다 장애물: `/perception/obstacle_flag` (Bool)
   - 초음파: `/ultrasonic/min_range` (Float32)
   - 신호등: `/perception/traffic_light_state` (String)
   - 차선: `/lane/steering_angle` (Float32)
   - decision_node_2026이 우선순위 기반 의사결정

3. **우선순위 로직 (2026 코드 기반)**
   ```
   1순위: 라이다 장애물 감지 → 정지
   2순위: 초음파 전방 장애물 → 정지
   3순위: 신호등 빨강/노랑 → 정지 (선택적)
   4순위: 차선 유효성 확인 → 없으면 정지
   5순위: 차선 따라 주행
   ```

**⚠️ 추가 필요 사항:**
1. **실차 파라미터 튜닝**
   - `cruise_speed_mps`: 현재 1.0m/s → 실차 테스트로 조정
   - `max_steer_rad`: 현재 0.6rad (34도) → 실차 조향 범위 확인
   - `ultra_safe_distance_m`: 현재 0.2m → 실차 브레이크 거리 고려

2. **ws-build-ai 고급 기능 활용 (향후)**
   - 장애물 회피 경로 생성 (현재 단순 정지만 구현)
   - 속도 표지판 인식 연동
   - 차선 변경 로직 추가

### 성능 최적화 (2026-01-21 적용)

**문제: 5초 이상 지연 발생**

**원인:**
1. USB 대역폭 부족 (카메라 고해상도 + 라이다 + 아두이노 동시 전송)
2. ROS 노드 Hz 불일치 (decision 20Hz, arduino 50Hz, lane 비동기)

**해결 적용:**
1. **ROS 노드 Hz 통일 (10Hz)**
   - `decision_node_2026.py`: 20Hz → **10Hz** (decision_cxx 참고)
   - `arduino_bridge_node.py`: 50Hz → **10Hz**
   - 파일: `src/decision/scripts/decision_node_2026.py:36`
   - 파일: `src/drivers/arduino_driver/scripts/arduino_bridge_node.py:113`

2. **시각화 활성화**
   - 차선 인식 오버레이: `lane_debug=true` 설정
   - 파일: `src/bringup/launch/track.launch:16`
   - 토픽: `/lane_overlay` (Image) - 차선 검출 결과 시각화

**추가 권장 조치 (미적용, 필요 시 적용):**
1. 카메라 해상도 낮추기: 640x480 → 320x240
2. 카메라 프레임레이트 낮추기: 30fps → 15fps
3. 카메라 압축 이미지 사용: `use_compressed=true`
4. USB 장치 분산 연결:
   - 카메라: USB 3.0 허브
   - 아두이노: USB 2.0 직접
   - 라이다: USB 3.0 직접

### 시각화 설정

**카메라 차선 인식:**
```bash
# 차선 검출 결과 (ROI + 허프 라인 + 중심선)
rosrun image_view image_view image:=/lane_overlay
# 또는
rosrun rqt_image_view rqt_image_view
```

**라이다 포인트 클라우드 (rviz):**
```bash
rosrun rviz rviz
```
rviz 설정:
1. Fixed Frame: `laser` (rplidar.yaml의 frame_id)
2. Add → LaserScan → Topic: `/scan`
3. 라이다가 USB 인식되지 않으면:
   - USB 허브 전력 문제 → 별도 USB 포트 직접 연결
   - 파란색 USB 3.0 포트 사용 권장

### 장애물 회피 로직 통합 (2026-01-21)

**문제점:**
- decision_node_2026: 장애물 감지 시 단순 정지만 수행
- ws-build-ai의 강점(카메라 기반 장애물 회피)이 활용되지 않음

**ws-build-ai의 숨겨진 능력:**
- `obstacle_detection_node`: 카메라로 장애물 감지 및 **회피 바이어스 계산**
- `/perception/obstacle_bias` 토픽: 장애물 방향을 피하는 조향 보정값 (-1.0~1.0)
  - 장애물이 왼쪽 → bias > 0 (오른쪽으로 회피)
  - 장애물이 오른쪽 → bias < 0 (왼쪽으로 회피)

**해결: decision_node_unified.py 생성 ✅**

**통합 로직:**
```
1순위: 라이다 장애물 (근거리) → 즉시 정지
2순위: 초음파 장애물 (근거리) → 즉시 정지
3순위: 카메라 장애물 (원거리) → 조향 바이어스로 회피
4순위: 신호등 (선택적) → 정지
5순위: 차선 추종 + 장애물 회피 바이어스 적용
```

**조향 계산식:**
```python
final_steering = lane_steering + (obstacle_bias × bias_weight)
```

**파라미터:**
- `use_obstacle_avoidance`: true/false (회피 기능 활성화)
- `obstacle_bias_weight`: 0.0~1.0 (회피 민감도, 기본 0.3)
  - 높을수록 장애물 회피 반응 강함
  - 낮을수록 차선 추종 우선

**실행 방법:**
```bash
roslaunch bringup track.launch decision_mode:=unified
```

**파일 위치:**
- 노드: `src/decision/scripts/decision_node_unified.py`
- 설정: `src/bringup/launch/track.launch:40-46`

**실차 튜닝 가이드:**
1. 장애물을 너무 일찍 회피하면: `obstacle_bias_weight` 감소 (0.3 → 0.2)
2. 장애물 회피가 부족하면: `obstacle_bias_weight` 증가 (0.3 → 0.4)
3. 회피 시 차선 벗어남: `cruise_speed_mps` 감소

### 런치 파일 분리 (2026-01-25) ✅

**대회 규정 반영:**
- **시간 측정 경기**: 트랙 2바퀴 빠른 주행 (7분 이내)
- **미션 수행 경기**: 장애물 회피 + 횡단보도(신호등) + 수직 주차
- 규정: "시간측정 경기 종료 후 **15분 내**에 미션수행 경기용 프로그램으로 다운로드 가능"
- 규정: "미션수행 경기는 프로그램 수정 시간 **별도 제공하지 않음**"

**런치 파일 비교:**

| 항목 | track.launch | mission.launch |
|------|--------------|----------------|
| **용도** | 시간 측정 경기 | 미션 수행 경기 |
| **전방 카메라** | ✅ (차선만) | ✅ (차선+장애물+신호등) |
| **후방 카메라** | ❌ | ✅ (주차용, TODO) |
| **라이다** | ✅ | ✅ |
| **초음파** | ✅ | ✅ |
| **장애물 회피** | ❌ (obstacle_enabled: false) | ✅ (obstacle_enabled: true) |
| **신호등 인식** | ❌ (traffic_light_enabled: false) | ✅ (traffic_light_enabled: true) |
| **decision_mode** | 2026 (단순, 빠름) | unified (장애물 회피) |
| **cruise_speed** | 1.5 m/s (빠른 주행) | 1.0 m/s (안정적 주행) |

**실행 방법:**
```bash
# 시간 측정 경기 (7분 이내 2바퀴)
roslaunch bringup track.launch

# 미션 수행 경기 (장애물 회피 + 신호등 + 주차)
roslaunch bringup mission.launch
```

**파일 위치:**
- `src/bringup/launch/track.launch`
- `src/bringup/launch/mission.launch`

**후방 카메라 설정 (TODO):**
- mission.launch에서 후방 카메라 노드 활성화 필요
- USB 카메라 2대 동시 사용 시 `video_device` 설정: `/dev/video0` (전방), `/dev/video1` (후방)
- 주차 미션용 별도 차선 인식 노드 필요 (후방 카메라 입력)

**4번 사항 완료 여부:**
- ✅ **완료**: ws-build-ai 인지 결과(장애물 회피)와 2026 안전 로직 통합
- ✅ **완료**: 대회 규정에 맞게 런치 파일 분리
- ⚠️ **실차 튜닝 필요**: 파라미터 조정은 실제 테스트 후 필요

### 5번: MORAI 전용 코드 정리 (2026-01-25) ✅

**패키지 사용 여부 확인:**

| 패키지 | 사용 여부 | 설명 | 조치 |
|--------|---------|------|------|
| **perception_pkg** | ✅ 사용 | 차선/장애물/신호등 인식 | 유지 |
| **decision** | ✅ 사용 | 의사결정 로직 | 유지 |
| **drivers/arduino_driver** | ✅ 필수 | ROS-아두이노 브리지 | 유지 |
| **drivers/ultrasonic_driver** | ✅ 사용 | 초음파 센서 | 유지 |
| **drivers/rplidar_driver** | ✅ 사용 | 라이다 센서 | 유지 |
| **bringup** | ✅ 사용 | 런치 파일 통합 | 유지 |
| **control_pkg** | ❌ 미사용 | MORAI 전용 | 무시 |
| **planning_pkg** | ❌ 미사용 | MORAI 전용 | 무시 |
| **vehicle_interface_pkg** | ❌ 미사용 | MORAI 전용 | 무시 |

**perception_pkg 노드별 사용 여부:**

| 노드 | 사용 여부 | 감지 방식 | 런치 파일 설정 | 설명 |
|------|---------|----------|---------------|------|
| **lane_tracking_node.py** | ✅ 항상 | 전통적 CV | - | ROI/HSV/Canny/Hough로 차선 중심 오프셋 계산 |
| **lane_marking_node.py** | ✅ 사용 | 전통적 CV | lane_marking_enabled: true | 색상 기반 정지선 검출 (횡단보도 미션) |
| **obstacle_detection_node.py** | ✅ mission | 전통적 CV | obstacle_enabled: true | HSV/에지 기반 장애물 회피 바이어스 |
| **traffic_light_node.py** | ✅ mission | **YOLO + HSV** | traffic_light_enabled: true | YOLO로 위치 검출 + HSV로 색상 판정 |
| **speed_sign_node.py** | ❌ 비활성화 | **YOLO** | speed_sign_enabled: false | 대회에 속도 표지판 없음 |

**YOLO 모델 정보:**
- **모델 파일**: `perception_pkg/models/traffic_sign_detector.pt` (5.3MB)
- **프레임워크**: Ultralytics YOLO (PyTorch)
- **학습 상태**: ✅ **사전 학습 완료** (MORAI 환경에서 학습된 모델)
- **인식 클래스**:
  - 신호등: `traffic_light_red`, `traffic_light_yellow`, `traffic_light_green`, `traffic_light_off`
  - 속도 표지판: `speed limit XX` 형식 (OCR)
- **사용 노드**: traffic_light_node (신호등), speed_sign_node (표지판)
- **장점**: 학습 데이터 없이도 전통적 CV로 차선/장애물 인식, YOLO는 특정 객체만 사용하여 효율적

**arduino_bridge_node.py 역할 (필수):**
- **ROS → 아두이노**: `/decision/cmd` (AckermannDrive) → 시리얼 명령 (`F`, `L`, `R`, `S` 또는 `V:pwm,S:deg`)
- **아두이노 → ROS**: 시리얼 초음파 데이터 (`F:25,FL:30,...`) → `/ultrasonic/ranges` (Float32MultiArray)
- **브리지 없이는 모터 제어 및 초음파 센서 사용 불가**

**리팩토링 조치:**
1. ✅ **speed_sign_enabled=false**: 대회 규정에 속도 표지판 미션 없음 (이미 적용)
2. ✅ **control_pkg, planning_pkg, vehicle_interface_pkg**: 런치 파일에서 사용되지 않음 (무시, 삭제 불필요)
3. ✅ **lane_marking_enabled=true**: 정지선 검출 기능 (횡단보도 미션에 필요할 수 있음)

**이식 절차 완료 여부:**
1. ✅ 문서/인터페이스 확정
2. ✅ ROS 스켈레톤 패키지 생성
3. ✅ 2026 코드 로직을 ROS 노드로 분리 이식
4. ✅ ws-build-ai 인지 결과와 결합하여 결정 로직 튜닝 + 런치 파일 분리
5. ✅ 불필요한 MORAI 전용 코드 정리

**✅ 모든 이식 절차 완료!** 실차 테스트 및 파라미터 튜닝 단계로 진행 가능.
