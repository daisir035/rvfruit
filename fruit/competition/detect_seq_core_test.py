import cv2
import time
from detect_ball_seq_test import detect_type


def go_detect_seq(cam, mode=0):
    """
    根据区域，进行四个位置上的水果种类的测序
    :param cam: 摄像头
    :param mode: 模式  1 放置区   0 采摘区
    :return: 果序
    """
    seq = [0, 0, 0, 0]  # 初始化识别区种类序列

    # 前往识别起始点，开始循环识别
    similarity_data = []  # 记录全部识别数据
#    pos = 6 if mode else 4  # 根据模式确定识别起始点位  
    cap = cv2.VideoCapture(cam)
    print("画面到位时按空格开始识别\n")
    for i in range(4):  # 识别4棵树
        print(f"\n第 {i + 1} 棵树")  # 树号从1起
#        # 0 1 在第一个节点   2 3 在下一个节点
#        if i == 0:
#            ret = serial_communicate(str(pos))
#        elif i == 2:
#            pos = pos + 1
#            ret = serial_communicate(str(pos))

#        # 摄像头接近
#        if mode:  # 放置区只需左右转动机械臂(此时应是抓取到了的，需保持抓紧)
#            if i & 1:  # 1, 3   2， 4号树
#                direction = arm_right  # 记录方向，后需复用
#                arm_standby(direction, claw=tight)
#            else:  # 0, 2   1， 3号树
#                direction = arm_left  # 记录方向，后需复用
#                arm_standby(direction, claw=tight)
#        else:  # 采摘区，需从主路行驶状态进入支路
#            if i & 1:  # 0, 2   1， 3号树
#                ret = serial_communicate(turn_right)
#                direction = turn_left  # 记录后续回退时的转向方向
#            else:  # 1, 3   2， 4号树
#                ret = serial_communicate(turn_left)
#                direction = turn_right  # 记录后续回退时的转向方向
#            ret = serial_communicate(drive_ahead)  # 前进
#            arm_standby(arm_middle)
        
        while 1:
            key = cv2.waitKey(1) & 0xff
            ret, img = cap.read()
            cv2.imshow('video', img)
            if key == ord(' '):
                break
            elif key == 27:
                exit()
        # 种类识别
        fruit_type = 0  # 初始化水果种类为0
        t0 = time.time()
        similarity = []
        # 当种类为0，或者种类为空，或者种类已经出现在之前检测的序列中(即重复)，循环识别
        while not fruit_type or fruit_type is None or fruit_type in seq:  # 注：该判断条件存在缺陷，需自行改进。即：若第一个识别结果即错误，会影响后面某个检测正确的结果
            fruit_type, similarity = detect_type(cap, mode=mode, time_out=8, time_out_en=False)
            print(f"current similarity data:\n{similarity}\n\n")
            if time.time() - t0 > 10:  # 为防止上述缺陷导致进入死循环，超时退出
                break
        
        seq[i] = fruit_type  # 记录果号
        similarity_data.append(similarity)  # 记录全部识别数据
        print(f"seq: {seq}")

        if seq[i] == 4:  # 最高权重果
            if mode:  # 放置区
                print("\n将4号放入框\n")
#                ok = put_in_basket(direction)  # 复用转向方向
            else:  # 采摘区
                print("\n将4号摘下\n")
#                ok = go_grab_retreat(cam, tree=i + 1, color=yellow, circle_number=2, go=False)  # 摘下一个黄球，此前未采摘，数量为2，已到位，go=False
#        
#        if not mode:  # 采摘区
#            ret = serial_communicate(drive_back)  # 退回
#            ret = serial_communicate(direction)  # 回到主路行驶状态

    print(f"\nDetected Sequence:\n{seq}\n")
    print(f"\nAll Similarity Data:\n{similarity_data}\n")
    return seq


if __name__ == '__main__':
    cam = "samples/detect_seq_1423.mp4"  # 录像测试专用
    go_detect_seq(cam, mode=0)
    