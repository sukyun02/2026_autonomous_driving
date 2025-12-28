#include <Car_Library.h>

// ==================== 핀 설정 ====================
// 왼쪽 모터
int motorLeftA = 3;     // 왼쪽 모터 IN1
int motorLeftB = 5;     // 왼쪽 모터 IN2

// 오른쪽 모터
int motorRightA = 6;    // 오른쪽 모터 IN3
int motorRightB = 9;    // 오른쪽 모터 IN4

// 초음파 센서
int trig = 10;          // trig 핀
int echo = 11;          // echo 핀

// ==================== 속도 설정 ====================
int SPEED_FORWARD = 100;    // 전진 속도 (0~255)
int SPEED_BACKWARD = 100;   // 후진 속도
int SPEED_TURN = 80;        // 회전 속도

// ==================== 전역 변수 ====================
char command = 'S';         // 수신한 명령

// ==================== 초기화 ====================
void setup() {
  Serial.begin(9600);

  // 모터 핀 설정
  pinMode(motorLeftA, OUTPUT);
  pinMode(motorLeftB, OUTPUT);
  pinMode(motorRightA, OUTPUT);
  pinMode(motorRightB, OUTPUT);

  // 초음파 센서 핀 설정
  pinMode(trig, OUTPUT);
  pinMode(echo, INPUT);

  Serial.println("Arduino Ready!");
}

// ==================== 메인 루프 ====================
void loop() {
  // 1. Python에서 명령 수신
  if (Serial.available() > 0) {
    command = Serial.read();
  }

  // 2. 명령에 따라 모터 제어
  switch(command) {
    case 'F':  // 전진
      motor_forward_both(SPEED_FORWARD);
      break;

    case 'B':  // 후진
      motor_backward_both(SPEED_BACKWARD);
      break;

    case 'L':  // 좌회전
      motor_turn_left(SPEED_TURN);
      break;

    case 'R':  // 우회전
      motor_turn_right(SPEED_TURN);
      break;

    case 'S':  // 정지
      motor_stop();
      break;

    default:
      motor_stop();
      break;
  }

  // 3. 초음파 센서 거리 측정 및 전송
  long distance = ultrasonic_distance(trig, echo);
  Serial.println(distance);  // Python으로 거리 전송

  delay(50);  // 50ms 대기
}

// ==================== 모터 제어 함수 ====================

// 전진 (양쪽 모터 전진)
void motor_forward_both(int speed) {
  motor_forward(motorLeftA, motorLeftB, speed);
  motor_forward(motorRightA, motorRightB, speed);
}

// 후진 (양쪽 모터 후진)
void motor_backward_both(int speed) {
  motor_backward(motorLeftA, motorLeftB, speed);
  motor_backward(motorRightA, motorRightB, speed);
}

// 좌회전 (왼쪽 정지, 오른쪽 전진)
void motor_turn_left(int speed) {
  motor_hold(motorLeftA, motorLeftB);           // 왼쪽 모터 정지
  motor_forward(motorRightA, motorRightB, speed); // 오른쪽 모터 전진
}

// 우회전 (오른쪽 정지, 왼쪽 전진)
void motor_turn_right(int speed) {
  motor_forward(motorLeftA, motorLeftB, speed);  // 왼쪽 모터 전진
  motor_hold(motorRightA, motorRightB);          // 오른쪽 모터 정지
}

// 정지 (양쪽 모터 정지)
void motor_stop() {
  motor_hold(motorLeftA, motorLeftB);
  motor_hold(motorRightA, motorRightB);
}
