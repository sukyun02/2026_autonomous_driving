from rplidar import RPLidar     #pip install rplidar-roboticia
import numpy as np              #pip install numpy
import time

class libLidar(object):
    def __init__(self, port):
        self.rpm = 0
        self.lidar = RPLidar(port, timeout=2)
        self.scan = []

    def init(self):
        try:
            print("모터 정지 중...")
            self.lidar.stop_motor()
            time.sleep(0.5)
        
            print("버퍼 클리어 중..")
            self.lidar.clear_input()
            time.sleep(0.5)

            try:
                info = self.lidar.get_info()
                print(f"모델 정보: {info}")
            except Exception as e:
                print(f"정보 읽기 실패: {e}")
            
            try:
                health = self.lidar.get_health()
                print(f"상태: {health}")
            except Exception as e:
                print(f"상태 읽기 실패: {e}")
            
            self.lidar.clear_input()
            time.sleep(0.5)
            print("✅ 초기화 완료!")
        except Exception as e:
            print(f"초기화 실패: {e}")
            try:
                self.lidar.start_motor()
                time.sleep(1)
            except:
                pass

    def scanning(self):
        self.lidar.clear_input()
        time.sleep(0.5)
        # iter_scans() 사용 (올바른 메서드)
        print("스캔 루프 시작...")
        scan_count = 0

        try:

            for scan in self.lidar.iter_scans(max_buf_meas=1000, min_len=10):
                if len(scan) > 10:
                    scan_array = []
                    for (quality, angle, distance) in scan:

                        if quality > 0 and distance > 0:
                            scan_array.append((angle, distance))
                if len(scan_array) > 0:
                    np_data = np.array(scan_array)
                    yield np_data
        except KeyboardInterrupt:
            print("\n스캔 중단됨")
        except Exception as e:
            print(f"\n스캔 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            raise

    def stop(self):
        try:
            self.lidar.stop()
            self.lidar.stop_motor()
            self.lidar.disconnect()
            print("✅ 라이다 연결 종료 완료")
        except:
            print("라이다 종료 중 오류 발생")

            
    def setRPM(self, rpm):
        try:
            self.lidar.motor_speed = rpm
        except:
            pass
  

    def getRPM(self):
        try:
            return self.lidar.motor_speed
        except:
            return 0

    def getAngleRange(self, scan, minAngle, maxAngle):
        data = np.array(scan)
        # 각도 범위가 0도를 넘어가는 경우 처리 (예: 350~10도)
        if minAngle > maxAngle:
            condition = np.where((data[:, 0] < maxAngle) | (data[:, 0] > minAngle))
        else:
            condition = np.where((data[:, 0] < maxAngle) & (data[:, 0] > minAngle))
        return data[condition]

    def getDistanceRange(self, scan, minDist, maxDist):
        data = np.array(scan)
        condition = np.where((data[:, 1] < maxDist) & (data[:, 1] > minDist))
        return data[condition]

    def getAngleDistanceRange(self, scan, minAngle, maxAngle, minDist, maxDist):
        data = np.array(scan)
        # 각도 범위가 0도를 넘어가는 경우 처리 (예: 350~10도)
        if minAngle > maxAngle:
            condition = np.where(((data[:, 0] < maxAngle) | (data[:, 0] > minAngle)) & (data[:, 1] < maxDist) & (data[:, 1] > minDist))
        else:
            condition = np.where((data[:, 0] < maxAngle) & (data[:, 0] > minAngle) & (data[:, 1] < maxDist) & (data[:, 1] > minDist))
        return data[condition]

    def get_far_distance(self, scan, minAngle, maxAngle):
        datas = self.getAngleRange(scan, minAngle, maxAngle)
        if len(datas) > 0:
            max_idx = datas[:, 1].argmax()
            return datas[max_idx]
        return None

    def get_near_distance(self, scan, minAngle, maxAngle):
        datas = self.getAngleRange(scan, minAngle, maxAngle)
        if len(datas) > 0:
            min_idx = datas[:, 1].argmin()
            return datas[min_idx]
        return [0, 0]  # None 대신 기본값 반환