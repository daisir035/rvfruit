from motion import *
from detect_ball import detect_circles, detect_type, check_grab
from arm_coord_2_claw import arm_coord_2_claw
from serial_communication import serial_communicate
from socket_communication import socket_communicate


def go_put_in_basket(basket):
    """
    输入篮号，前往放置
    :param basket: 目标放置篮  0 1 2 3
    """
    print(f"\nPut in basket {basket + 1}\n")
    # 前往节点 0 1 --> 6    2 3 --> 7
    ret = serial_communicate("6" if basket < 2 else "7")
    # 奇偶判断左右 0 2 --> 左放  1 3 --> 右放
    put_in_basket(arm_right if basket & 1 else arm_left)


def go_grab_retreat(cam, tree, color, circle_number, grab_time_out=10, go=True, retreat=True):
    """
    输入树号，前往，到位抓取一个球，退回
    :param cam: 摄像头
    :param tree: 目标树  1 2 3 4
    :param color: 目标颜色
    :param circle_number: 当前树上应有目标颜色的果的数量
    :param grab_time_out: 抓取超时时间
    :param go: 是否需要前往目标树（默认需要）
    :param retreat: 是否需要退回交叉点（默认需要）
    :return: 抓取成功标志位
    """
    print(f"\nGrab Tree:{tree}  color:{color}  circle_number:{circle_number}\n")
    if go:
        ret = serial_communicate("4" if tree <= 2 else "5")  # 1 2 --> 4    3 4 --> 5
        if tree & 1:  # 奇数树号左转
            ret = serial_communicate(turn_left)
        else:
            ret = serial_communicate(turn_right)
        ret = serial_communicate(drive_ahead)  # 前往停止线

    grab_ok = 0  # 初始化抓取成功标志位为失败
    trial_time = 0  # 初始化已尝试抓取次数为0
    t0 = time.time()  # 初始时间
    while not grab_ok and trial_time < 5 and (time.time() - t0) < grab_time_out:  # 当未抓取成功，且已尝试次数小于5，且未超过设定用时时，循环
        arm_standby(arm_middle)  # 居中待命，稳定镜头
        arm_standby(arm_middle)  # 居中待命，稳定镜头
        # 检测圆，需给定目标颜色与圆数量
        circle, _ = detect_circles(cam, color=color, circle_number=circle_number, time_out=10, time_out_en=False)
        if not circle[2]:  # xyr，半径为0
            print(f"\n未检测到圆\n")
            continue
        print(f"\n当前圆位置参数： {circle}\n\n------开始抓取------\n")
        trial_time += 1  # 尝试次数更新

        coord = arm_coord_2_claw([circle[0], circle[1]])  # 解算第一个圆
        data_ik = socket_communicate(coord)  # 将解算结果发给解算服务器
        arm_grab(data_ik)  # 使用解算服务器返回的数据进行抓取

        # 抓取检查
        grab_ok = check_grab(cam, color)

    # 退回
    if retreat:
        ret = serial_communicate(drive_back)
        # 回到主路行驶状态
        if tree & 1:  # 奇数树号右转
            ret = serial_communicate(turn_right)
        else:
            ret = serial_communicate(turn_left)

    return grab_ok


def go_detect_seq(cam, mode):
    """
    根据区域，进行四个位置上的水果种类的测序
    :param cam: 摄像头
    :param mode: 模式  1 放置区   0 采摘区
    :return: 果序
    """
    seq = [0, 0, 0, 0]  # 初始化识别区种类序列
    similarity_data = []  # 接收全部识别数据，当识别有误时用户可自行尝试通过历史数据勘误
    # 前往识别起始点，开始循环识别
    pos = 6 if mode else 4  # 根据模式确定识别起始点位  
    ok = 0  # 初始化返回标志位为未完成识别(未识别到4或抓取到4)

    for i in range(4):  # 识别4棵树/个篮
        print(f"\n第 {i + 1} 棵树/个篮")  # 树/篮号从1起
        # 0 1 在第一个节点   2 3 在下一个节点
        if i == 0:
            ret = serial_communicate(str(pos))
        elif i == 2:
            pos = pos + 1
            ret = serial_communicate(str(pos))

        # 摄像头接近
        if mode:  # 放置区只需左右转动机械臂(此时应是抓取到了的，需保持抓紧)
            if i & 1:  # 1, 3   2， 4号树
                direction = arm_right  # 记录方向，后需复用
                arm_standby(direction, claw=tight)
            else:  # 0, 2   1， 3号树
                direction = arm_left  # 记录方向，后需复用
                arm_standby(direction, claw=tight)
        else:  # 采摘区，需从主路行驶状态进入支路
            if i & 1:  # 0, 2   1， 3号树
                ret = serial_communicate(turn_right)
                direction = turn_left  # 记录后续回退时的转向方向
            else:  # 1, 3   2， 4号树
                ret = serial_communicate(turn_left)
                direction = turn_right  # 记录后续回退时的转向方向
            ret = serial_communicate(drive_ahead)  # 前进
            arm_standby(arm_middle)
        
        # 种类识别
        fruit_type = 0  # 初始化水果种类为0
        t0 = time.time()
        similarity = []

        # 当种类为0，或者种类为空，或者种类已经出现在之前检测的序列中(即重复)，循环识别
        # 注：该判断条件存在缺陷，需自行改进。即：若第一个识别结果即错误，会影响后面某个检测正确的结果， 用户可在4次识别结束后尝试通过历史数据勘误
        while not fruit_type or fruit_type is None or fruit_type in seq:
            fruit_type, similarity = detect_type(cam, mode=mode, time_out=8, time_out_en=False)
            if time.time() - t0 > 10:  # 为防止上述缺陷导致进入死循环，超时退出
                break
        seq[i] = fruit_type  # 记录果号
        similarity_data.append(similarity)  # 记录全部识别数据
        print(f"seq: {seq}")

        if seq[i] == 4:  # 最高权重果
            if mode:  # 放置区
                print("\n将4号放入框\n")
                ok = put_in_basket(direction)  # 复用转向方向
            else:  # 采摘区
                print("\n将4号摘下\n")
                ok = go_grab_retreat(cam, tree=i + 1, color=yellow, circle_number=2, go=False)  # 摘下一个黄球，此前未采摘，数量为2，已到位，go=False
        
        if not mode:  # 采摘区
            ret = serial_communicate(drive_back)  # 退回
            ret = serial_communicate(direction)  # 回到主路行驶状态

    print(f"\nDetected Sequence:\n{seq}\n")
    print(f"\nAll Similarity Data:\n{similarity_data}\n")
    return seq, ok


if __name__ == '__main__':
    """
    功能测试  每次仅可取注一个测试命令
    """
    cam = 0

    """
    在位抓取测试
    """
#    go_grab_retreat(cam, tree=1, color=yellow, circle_number=1, grab_time_out=50, go=False, retreat=False)

    """
    前往抓取退回测试
    """
#    go_grab_retreat(cam, tree=1, color=yellow, circle_number=2, grab_time_out=20)

    """
    前往放置测试
    """
#    go_put_in_basket(basket=1)

    """
    前往测序测试
    """
#    go_detect_seq(cam, mode=1)
