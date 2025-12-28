#include <Car_Library.h>
#include <Servo.h>

// ==================== 핀 설정 ====================
// DC 모터 (구동 모터)
int motorA1 = 3;    // 구동 모터 IN1 (PWM)
int motorA2 = 5;    // 구동 모터 IN2 (PWM)

// 서보 모터 (조향)
int SERVO_PIN = 9;  // 서보모터 PWM 핀
Servo steeringServo;

// 초음파 센서 6개 (전방, 좌전방, 우전방, 후방, 좌후방, 우후방)
int trigPins[6] = {22, 24, 26, 28, 30, 32};  // Trig 핀 배열
int echoPins[6] = {23, 25, 27, 29, 31, 33};  // Echo 핀 배열

// 센서 위치 인덱스
#define FRONT       0   // 전방
#define FRONT_LEFT  1   // 좌전방
#define FRONT_RIGHT 2   // 우전방
#define REAR        3   // 후방
#define REAR_LEFT   4   // 좌후방
#define REAR_RIGHT  5   // 우후방

// ==================== 속도 및 각도 설정 ====================
int SPEED_FORWARD = 100;      // 전진 속도 (0~255)
int SPEED_BACKWARD = 100;     // 후진 속도
int SPEED_TURN = 80;          // 회전 속도

// 서보 조향 각도
int SERVO_CENTER = 90;        // 중앙 (직진)
int SERVO_LEFT_MAX = 60;      // 최대 좌회전 각도
int SERVO_RIGHT_MAX = 120;    // 최대 우회전 각도
int SERVO_LEFT_SOFT = 75;     // 약한 좌회전
int SERVO_RIGHT_SOFT = 105;   // 약한 우회전

// ==================== 전역 변수 ====================
char command = 'S';           // 수신한 명령
long distances[6];            // 6개 초음파 센서 거리값 저장

// ==================== 초기화 ====================
void setup() {
  Serial.begin(9600);

  // DC 모터 핀 설정
  pinMode(motorA1, OUTPUT);
  pinMode(motorA2, OUTPUT);

  // 서보모터 초기화
  steeringServo.attach(SERVO_PIN);
  steeringServo.write(SERVO_CENTER);  // 중앙 위치로 초기화

  // 초음파 센서 6개 핀 설정
  for (int i = 0; i < 6; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
  }

  Serial.println("Arduino Ready!");
  Serial.println("6 Ultrasonic Sensors + Servo Steering Initialized");
}

// ==================== 메인 루프 ====================
void loop() {
  // 1. Python에서 명령 수신
  if (Serial.available() > 0) {
    command = Serial.read();
  }

  // 2. 명령에 따라 모터 및 조향 제어
  switch(command) {
    case 'F':  // 전진
      motor_forward(SPEED_FORWARD);
      steering_center();
      break;

    case 'B':  // 후진
      motor_backward(SPEED_BACKWARD);
      steering_center();
      break;

    case 'L':  // 좌회전 (최대)
      motor_forward(SPEED_TURN);
      steering_left_max();
      break;

    case 'R':  // 우회전 (최대)
      motor_forward(SPEED_TURN);
      steering_right_max();
      break;

    case 'l':  // 약한 좌회전
      motor_forward(SPEED_FORWARD);
      steering_left_soft();
      break;

    case 'r':  // 약한 우회전
      motor_forward(SPEED_FORWARD);
      steering_right_soft();
      break;

    case 'S':  // 정지
      motor_stop();
      steering_center();
      break;

    default:
      motor_stop();
      steering_center();
      break;
  }

  // 3. 초음파 센서 6개 거리 측정 및 전송
  measure_all_ultrasonic();
  send_sensor_data();

  delay(50);  // 50ms 대기
}

// ==================== DC 모터 제어 함수 ====================

// 전진
void motor_forward(int speed) {
  analogWrite(motorA1, speed);
  analogWrite(motorA2, 0);
}

// 후진
void motor_backward(int speed) {
  analogWrite(motorA1, 0);
  analogWrite(motorA2, speed);
}

// 정지
void motor_stop() {
  analogWrite(motorA1, 0);
  analogWrite(motorA2, 0);
}

// ==================== 서보 조향 제어 함수 ====================

// 중앙 (직진)
void steering_center() {
  steeringServo.write(SERVO_CENTER);
}

// 최대 좌회전
void steering_left_max() {
  steeringServo.write(SERVO_LEFT_MAX);
}

// 최대 우회전
void steering_right_max() {
  steeringServo.write(SERVO_RIGHT_MAX);
}

// 약한 좌회전
void steering_left_soft() {
  steeringServo.write(SERVO_LEFT_SOFT);
}

// 약한 우회전
void steering_right_soft() {
  steeringServo.write(SERVO_RIGHT_SOFT);
}

// 각도 직접 제어 (0~180도)
void steering_angle(int angle) {
  angle = constrain(angle, SERVO_LEFT_MAX, SERVO_RIGHT_MAX);  // 범위 제한
  steeringServo.write(angle);
}

// ==================== 초음파 센서 함수 ====================

// 특정 센서 거리 측정
long measure_ultrasonic(int index) {
  digitalWrite(trigPins[index], LOW);
  delayMicroseconds(2);
  digitalWrite(trigPins[index], HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPins[index], LOW);

  long duration = pulseIn(echoPins[index], HIGH, 30000);  // 타임아웃 30ms
  long distance = duration * 0.034 / 2;  // cm 단위

  // 유효 범위 체크 (2~400cm)
  if (distance < 2 || distance > 400) {
    distance = 0;  // 측정 실패
  }

  return distance;
}

// 6개 센서 모두 측정
void measure_all_ultrasonic() {
  for (int i = 0; i < 6; i++) {
    distances[i] = measure_ultrasonic(i);
    delayMicroseconds(100);  // 센서 간 간섭 방지
  }
}

// Python으로 센서 데이터 전송
void send_sensor_data() {
  // 형식: "F:25,FL:30,FR:28,R:50,RL:45,RR:48"
  Serial.print("F:");    Serial.print(distances[FRONT]);
  Serial.print(",FL:");  Serial.print(distances[FRONT_LEFT]);
  Serial.print(",FR:");  Serial.print(distances[FRONT_RIGHT]);
  Serial.print(",R:");   Serial.print(distances[REAR]);
  Serial.print(",RL:");  Serial.print(distances[REAR_LEFT]);
  Serial.print(",RR:");  Serial.print(distances[REAR_RIGHT]);
  Serial.println();  // 줄바꿈
}

// ==================== 디버그용 함수 ====================

// 센서 상태 출력
void print_sensor_debug() {
  Serial.println("===== Sensor Status =====");
  Serial.print("Front: ");       Serial.print(distances[FRONT]);       Serial.println(" cm");
  Serial.print("Front-Left: ");  Serial.print(distances[FRONT_LEFT]);  Serial.println(" cm");
  Serial.print("Front-Right: "); Serial.print(distances[FRONT_RIGHT]); Serial.println(" cm");
  Serial.print("Rear: ");        Serial.print(distances[REAR]);        Serial.println(" cm");
  Serial.print("Rear-Left: ");   Serial.print(distances[REAR_LEFT]);   Serial.println(" cm");
  Serial.print("Rear-Right: ");  Serial.print(distances[REAR_RIGHT]);  Serial.println(" cm");
  Serial.println("========================");
}
