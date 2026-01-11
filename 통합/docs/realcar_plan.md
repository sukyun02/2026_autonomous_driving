# 실차 통합 문서 (초안)

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

## 현재 코드 구조 요약
### 2026 코드 (실차 검증)
- `modules/vehicle/sensors.py`: 카메라/라이다/초음파/아두이노 초기화 및 데이터 획득.
- `modules/vehicle/control.py`: 의사결정(정지/좌/우/직진) + 아두이노 명령 전송.
- `config.py`: 포트/거리/차선 인식 파라미터.

### ws-build-ai (ROS1 베이스)
- 차선 인식: `src/perception_pkg/scripts/lane_tracking_node.py`
- 신호등 인식: `src/perception_pkg/scripts/traffic_light_node.py`
- MORAI 인터페이스: `src/vehicle_interface_pkg/` (실차에서는 교체 대상)

## ROS1 통합 설계 (초안)
### 노드/토픽 구성
- Camera Driver (Front) -> `/camera/front/image` (sensor_msgs/Image or CompressedImage)
- Camera Driver (Rear) -> `/camera/rear/image` (sensor_msgs/Image or CompressedImage)
- Lane Tracking -> `/lane/steering_angle`, `/lane/center_offset`
- Traffic Light -> `/perception/traffic_light_state`
- LiDAR Driver -> `/scan` (sensor_msgs/LaserScan)
- Ultrasonic Driver -> `/ultrasonic/ranges` (Float32MultiArray, 6개 센서) 또는 `/ultrasonic/<pos>` (sensor_msgs/Range)
- Decision Node -> `/decision/cmd` (속도+조향 값 메시지, 커스텀 또는 표준)
- Motor Driver -> `/arduino/cmd` 구독, 시리얼로 속도/조향 전송

### 노드 책임
- Decision Node:
  - 입력: 차선 방향/신호등 상태/라이다 장애물/초음파 거리
  - 출력: 속도+조향 명령 (실차에서는 가변저항 기반 속도 제어 + 조향)
  - 규정 반영: 출발 지연/정지선 정차/신호 변경 후 5초 내 출발
- Motor Driver:
  - `/decision/cmd`를 아두이노 시리얼 명령으로 변환 (속도/조향 값)
  - 안전을 위해 초기 상태는 항상 정지

## 이식 절차 (권장 순서)
1) 문서/인터페이스 확정 (본 문서 업데이트)
2) ROS 스켈레톤 패키지 생성 (실차 센서/모터 드라이버)
3) 2026 코드 로직을 ROS 노드로 분리 이식
4) ws-build-ai 인지 결과와 결합하여 결정 로직 튜닝
5) 불필요한 MORAI 전용 코드 정리

## 확인 필요 항목 (미정)
- 실제 차량 치수와 센서 장착 위치(규정 범위 내 좌표 확정)
- 라이다/초음파 토픽 주기 및 처리 지연 허용치
- ROS 토픽 표준화 여부(표준 메시지 vs 커스텀 메시지)

## 실차 결정 사항 (반영 완료)
- 아두이노 명령은 속도/조향 값 기반으로 확장.
- 전원/출력 기준: 배터리 12V (최대 출력 12V).
- 카메라 2대 사용은 확정.
- 카메라 역할: 전방/후방 분리, 라이다는 전방 장애물 회피 용도.

## 표준 메시지 전환 요약
- 실차는 USB 허브 기반 센서 입력/아두이노 제어 출력이라 브릿지 노드가 필수.
- MORAI 메시지 유지 시에도 실차용 변환층이 필요하므로, 내부는 표준 메시지로 정리하는 편이 깔끔함.
- 표준 메시지로 바꿔도 기능 로직(차선/신호등/장애물 판단)은 그대로 유지 가능.
- 다만 노드 경계(센서/인지/결정/제어) 분리와 단위/주기 정리는 함께 필요.

## 표준 메시지 매핑/추가 요약 (실차)
### MORAI 메시지 -> 표준 메시지
- `morai_msgs/CtrlCmd` -> `ackermann_msgs/AckermannDrive` (추천) 또는 `geometry_msgs/Twist`
- `morai_msgs/EgoVehicleStatus` -> `nav_msgs/Odometry` (추천)

### 실차에서 추가로 필요한 표준 메시지
- 카메라: `sensor_msgs/Image` 또는 `sensor_msgs/CompressedImage`
- 라이다: `sensor_msgs/LaserScan`
- 초음파: `sensor_msgs/Range` x6 (추천) 또는 `std_msgs/Float32MultiArray`
- 신호등 상태: `std_msgs/String` 또는 `std_msgs/UInt8`
- 차선 오프셋/조향: `std_msgs/Float32`

### 라이다 라이브러리 vs 메시지
- `rplidar` 라이브러리는 센서를 읽는 드라이버 역할이고, ROS 메시지(`sensor_msgs/LaserScan`)와는 별개.
- 실제 노드는 `rplidar`로 스캔 데이터를 읽고, 이를 `LaserScan`으로 퍼블리시하는 구조.
