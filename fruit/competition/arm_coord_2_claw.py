import math
from param import *


def arm_coord_2_claw(pixel):
    """
    运动学逆解服务器不解算执行机构，故需更正机械臂末端位置
    :param pixel: 像素平面上点的坐标
    :return: 夹爪中心应在底座坐标系下的位置
    """
    # 像素平面坐标系 --> 相平面坐标系
    x_image = pixel[0] - u0
    y_image = pixel[1] - v0

    # 根据高度判断物体距离(因每次停止位置变动很小而可以认为距离为定值，或可自行获取底盘超声波测距结果进行处理)
    if pixel[1] < sight_middle:
        D_object_to_camera = D_object_to_camera_upper
    else:
        D_object_to_camera = D_object_to_camera_lower
#    print(f"\n物体到相机CCD距离: {D_object_to_camera}")

    # 相平面坐标系 --> 相机坐标系
    x_camera = x_image * D_object_to_camera / f_x_div_dx
    y_camera = y_image * D_object_to_camera / f_y_div_dy

    # 相机坐标系 --> 底座坐标系     车头超前，x正方向指向车身右侧，y正方向指向车头，z正方向竖直向上
    coord = []  # 机械臂5号舵机末端的夹取位姿 [x y z Roll Pitch Yaw]  其中Roll表征绕x轴旋转的角度，Pitch表征绕y轴旋转的角度，Yaw表征绕z轴旋转的角度
    coord.append(x_camera - x_camera_to_base)  # 写入x
    coord.append(D_object_to_camera - y_camera_to_base)  # 写入y，结果为两种固定值(视上下层而定)
    coord.append(z_camera_to_base - y_camera)  # 写入z，相机坐标系y轴与底座坐标系z轴平行
#    print(f"原始底座坐标系坐标: {['%.2f' %coord[i] for i in range(2)]}")

    # 底座坐标系中球心在xoy平面内的投影点与原点的夹角
    theta = math.atan2(coord[1], coord[0])
#    print(f"偏移角度: {theta * RA2DE :.2f}")

    # 写入夹取姿态
    # Roll值选取，仰夹为(-90, 0)，水平夹为-90，俯夹为(-90, -180)
    if coord[2] >= 25:  # 根据物体高度进行俯仰角判断（或可自定义一映射关系使抓取姿态变化更柔顺）
        coord.append(-80.0)  # 10度仰角夹取
    else:
        coord.append(-100.0)  # 10度俯角夹取
#    print(f"俯仰角度: {coord[3]:.2f}")
    coord.append(0.0)  # Pitch
    coord.append(0.0)  # Yaw

    # 解算服务器不解算夹具，故需引入夹爪长度，根据俯仰角，目标点与原点的夹角更新xyz
    l_j5_claw = math.sqrt(j5_claw_delta_y**2 + j5_claw_delta_z**2)  # 夹爪实际长度
    roll_claw = (coord[3] + 180) * DE2RA - math.atan2(j5_claw_delta_z, j5_claw_delta_y)  # 5号舵机末端位于夹爪基线所在直线下方，俯仰角需相应减去一个偏移角
    coord[0] = coord[0] - l_j5_claw * math.sin(roll_claw) * math.cos(theta)  # 投影在xoy平面内计算
    coord[1] = coord[1] - l_j5_claw * math.sin(roll_claw) * math.sin(theta)  # 投影在xoy平面内计算
    coord[2] = coord[2] + l_j5_claw * math.cos(roll_claw)  # roll_claw > 90°

#    print(f"\n更新数据结果:\n{['%.2f' %i for i in coord]}\n")
    return coord


if __name__ == '__main__':
    circle = [100, 200, 30]  # 测试样本
    coord = arm_coord_2_claw([int(circle[0]), int(circle[1])])
    print("coord", coord)
    