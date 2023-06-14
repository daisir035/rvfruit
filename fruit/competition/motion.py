import time
from param import *
from Arm_Lib import Arm_Device


# 创建机械臂对象
Arm = Arm_Device()
time.sleep(.01)


def arm_standby(direction, claw=loose):
    # 待命位(左中右)
    Arm.Arm_serial_servo_write6(direction + delta_yaw_servo_1, level_servo_2, level_servo_3, level_servo_4, 90, claw, 800)
    time.sleep(1)
    
    
def arm_scout(direction):
    Arm.Arm_serial_servo_write6(direction + delta_yaw_servo_1, 90, 90, 0, 90, loose, 800)
    time.sleep(1)  
    
    
def arm_midway():
    # 中途防碰撞位
    Arm.Arm_serial_servo_write6(90, 90, 30, 30, 90, loose, 800)
    time.sleep(1)


def arm_grab(data_ik):
    # 居中待命
    Arm.Arm_serial_servo_write6(90 + delta_yaw_servo_1, level_servo_2, level_servo_3, level_servo_4, 90, loose, 800)
    time.sleep(1)
    # 中途防撞
    arm_midway()
    # 张开,前出,预备
    Arm.Arm_serial_servo_write6(data_ik[0], data_ik[1], data_ik[2], data_ik[3]-25, 90, loose, 500)
    time.sleep(1)
    # 张开,前出,到位
    Arm.Arm_serial_servo_write6(data_ik[0], data_ik[1], data_ik[2], data_ik[3], 90, loose, 500)
    time.sleep(1)
    # 抓紧
    Arm.Arm_serial_servo_write6(data_ik[0], data_ik[1], data_ik[2], data_ik[3], 90, tight, 500)
    time.sleep(1)
    # 抓紧，摘下
    Arm.Arm_serial_servo_write6(data_ik[0], data_ik[1], data_ik[2], data_ik[3]-15, 90, tight, 500)
    time.sleep(1)
    # 回中
    Arm.Arm_serial_servo_write6(90 + delta_yaw_servo_1, level_servo_2, level_servo_3, level_servo_4, 90, tight, 800)
    time.sleep(1)
    # 回中
    Arm.Arm_serial_servo_write6(90 + delta_yaw_servo_1, level_servo_2, level_servo_3, level_servo_4, 90, tight, 800)
    time.sleep(1)


def put_in_basket(direction):
    print("\nPut\n")
    # 放球
    Arm.Arm_serial_servo_write6(direction, level_servo_2, level_servo_3, level_servo_4, 90, tight, 500)  # 转向到位
    time.sleep(.5)
    Arm.Arm_serial_servo_write6(direction, 91, 13, 65, 90, tight, 500)  # 伸出
    time.sleep(.5)
    Arm.Arm_serial_servo_write6(direction, 91, 13, 65, 90, loose, 500)  # 松开
    time.sleep(.5)
    Arm.Arm_serial_servo_write6(90 + delta_yaw_servo_1, level_servo_2, level_servo_3, level_servo_4, 90, loose, 500)  # 回
    time.sleep(.5)
    return 1
