import time
from socket import *


def socket_communicate(data):
    """
    向机械臂运动学反解服务器发送位姿数据，接收服务器返回的舵机数据
    :param data: 客户端发送给反解服务器的数据
    :return: 服务器发回的反解数据
    """
    ADDR = '/home/jetson/dofbot_ws/src/dofbot_moveit/src/server.sock'
    clientfd = socket(AF_UNIX, SOCK_STREAM)  # 创建socket客户端
    # 客户端连接到该套接字
    clientfd.connect(ADDR)
    time.sleep(.5)  # 留出时间，防止连接意外

    # 发送预处理，浮点数转字符串，空格隔开
    msg_send = " ".join(list(map(str, data)))
    msg_send = msg_send + " "
    print(f"\nsending object pos data : {msg_send}\n")
    if not msg_send:  # 传入的发送数据为空
        return 0

    clientfd.send(msg_send.encode())  # 发送数据

    # 接收
    msg_recv = clientfd.recv(1024)
    print(f"\nservo data received: {msg_recv.decode()}\n")
    ch = msg_recv.decode()

    # 接收后处理(将以空格为间隔字符串数组转为浮点数组)
    data_ik = []
    num_temp = ""
    for c in ch:
        if c == " ":            # 空格时，将b中存储的数字附到浮点数组a的末尾，并将b清空
            data_ik.append(float(num_temp))
            num_temp = ""
        else:                   # 非空格时，b按位累计接收到的字符
            num_temp += c

    clientfd.close()  # 关闭客户端
    return data_ik


if __name__ == '__main__':
    input("确认打开服务器后按回车运行\n>>>")
    num = [-4.5, 14.7, 27.1, -90.0, 0.0, 0.0]
    data_ik = socket_communicate(num)
    print(data_ik)
    