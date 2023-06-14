import cv2
import time
from param import *


def z_score(stats, ref=0.8):
    """
    数据标准化，剔除坏点
    :param stats: 输入数组
    :param ref: 参考值（默认0.8）
    :return: 输入数组满足参考值条件的对应的布尔数组
    """
    mean = np.mean(stats)  # 计算平均值
    std = np.std(stats)  # 计算标准差

    if not std:  # 标准差为0，返回全真
        return [True for _ in stats]

    stats_z = [(s - mean) / std for s in stats]  # 计算z标准值
    return np.abs(stats_z) < ref  # 判断各值是否小于参考值


def color_filter(img, color):
    """
    根据目标颜色，过滤其它颜色
    :param img: 图像帧
    :param color: 目标颜色  黄色 1   白色 0
    :return: 筛选后的二值图像
    """
    # 导入相应颜色的高低阈值
    if color:  # 黄色为真
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)  # 黄色乒乓球在HLS色彩模式下区别度较高
        thresh_lower = yellow_lower
        thresh_upper = yellow_upper
    else:  # 白色乒乓球在BGR色彩模式下区别度较高
        thresh_lower = white_lower
        thresh_upper = white_upper

    # 根据阈值进行筛选，阈值内的为255，否则为0，得到二值图
    img = cv2.inRange(img, thresh_lower, thresh_upper)

    return img


def find_circle(img, color, circle_number):
    """
    在bgr图上上找到目标数量个目标颜色的圆(即乒乓球)，得到其圆参数
    :param img: 图像帧
    :param color: 目标颜色
    :param circle_number: 当前树上应有目标颜色的果的数量
    :return: 圆参数
    """
    # 过滤其它颜色
    img = color_filter(img, color)
#    cv2.imshow("Filtered", img)

    # 高斯模糊
    img = cv2.GaussianBlur(img, (11, 11), 2, 2)
#    cv2.imshow("GaussianBlur", img)

    # 二值化
    _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
#    cv2.imshow("threshold", img)

    # 形态学闭操作，使区域闭合无空隙
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, morphology_kernel_size_ball)  # 卷积核大小
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
#    cv2.imshow("Closed", img)

    # 腐蚀和膨胀 (同形态学闭操作，但精细化调整)
    element = cv2.getStructuringElement(cv2.MORPH_RECT, erode_dilate_kernel_size_ball)
    img = cv2.erode(img, element, iterations=erode_iterations_ball)
#    cv2.imshow("erode", img)
    img = cv2.dilate(img, element, iterations=dilate_iterations_ball)
#    cv2.imshow("dilate", img)

    # canny边缘检测
    img = cv2.Canny(img, threshold1=canny_threshold1, threshold2=canny_threshold2)
#    cv2.imshow("Canny", img)

    # 自适应霍夫圆检测
    num = 0  # 初始化检测到的圆数量
    r_min = rmin  # 导入设定的最小半径
    circles = [[[0, 0, 0]]]  # 初始化圆参数
    while num != circle_number and r_min < rmin_threshold:  # 当未检测到目标数量圆，且minRadius参数未达到设置的上限时，循环检测
        r_min += 2  # 每次minRadius参数自加2
        circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, dp=1, minDist=100, param1=100,  # 不建议修改
                                   param2=HoughCircles_param2, minRadius=r_min, maxRadius=rmax)  # 可修改的参数
        # param2，越小，检测到越多近似的圆； 越大，检测到的圆越接近完美的圆形
        # minRadius，最小检测圆半径，maxRadius，最大检测圆半径
        if circles is None:  # 检测结果为空
            continue
        num = len(circles[0])  # 检测到的圆的数量
#        print("circles detected", circles)
#        print("====================\n\n")
    return circles


def detect_circles(cap, color, circle_number, sample_times=9, time_out=5, time_out_en=False):
    """
    实时检测视野内指定数量个指定颜色的圆，并多次采样求平均提高定位精度，返回最左侧的一个圆的参数
    :param cam: 摄像头
    :param color: 目标颜色
    :param circle_number: 当前树上应有目标颜色的果的数量
    :param sample_times: 采样次数
    :param time_out: 超时时间（默认5s）
    :param time_out_en: 超时允许（默认不允许超时）
    :return: 第一个(最左侧)圆参数
    """
    print("\n------开始检测圆位置------\n")
    t0 = time.time()  # 初始时间
    
    detect_fail = 0  # 初始化检测失败标志位
    sample_time = 0  # 初始化采样次数为0
    # 初始化数据记录表为空
    x_table = []
    y_table = []
    r_table = []
    
#    cap = cv2.VideoCapture(cam)  # 开启摄像头
    
    while sample_time < sample_times:  # 当采样次数小于设定次数时，循环检测采样
        detect_fail = 0  # 失败时再置位

        # 超时退出
        task_time = time.time() - t0
        if not time_out_en and task_time >= time_out:
            print("\n超时未检测到圆\n")
            detect_fail = 1  # 失败置位
            break

        # 获取摄像头图像帧
        ret, img = cap.read()
        if not ret:
            continue

        # Esc 退出
        if cv2.waitKey(1) & 0xff == 27:
            break

        circles = find_circle(img, color, circle_number)  # 获取所有圆参数
        if circles is None:  # 为空，跳过
            continue
        if circles[0][0][2] == 0:  # 半径为0，即未识别到，跳过
            continue

        num = len(circles[0])  # 计圆数
        sample_time += 1  # 采样成功次数更新

        if num == 2:  # 水平排序
            if circles[0][0][0] > circles[0][1][0]:
                temp = circles[0][0]
                circles[0][0] = circles[0][1]
                circles[0][1] = temp

        # 记录最左侧的圆的数据
        x_table.append(circles[0][0][0])
        y_table.append(circles[0][0][1])
        r_table.append(circles[0][0][2])

##        # 在原图上画圆
#        for i in range(num):
#            cv2.circle(img,
#                       (int(circles[0][i][0]), int(circles[0][i][1])),
#                       int(circles[0][i][2]),
#                       (255, 0, 100), 2)
#        cv2.imshow("circles", img)
#        cv2.waitKey(100)

    cv2.destroyAllWindows()
    
    if detect_fail:
#        cap.release()
        return [0, 0, 0], img  # 失败返回全0
    else:
#        print("\nx_table", x_table)
        x_select = z_score(x_table, ref=x_select_ref)  # 对x数据进行标准化处理(对全部xyr数据进行处理，容易会出现三者相与之后全为false的情况)
#        print("\nx_select", x_select)
        if not any(x_select):  # x的标准化数据全为false，误差率过大，丢弃
#            cap.release()
            return [0, 0, 0], img
        # 计算标准化结果为true(排除坏点干扰)的数据的平均值
        x_sum = y_sum = r_sum = real_time = 0
        for i in range(len(x_select)):
            if x_select[i]:
                x_sum += x_table[i]
                y_sum += y_table[i]
                r_sum += r_table[i]
                real_time += 1
#        cap.release()
        return [int(x_sum / real_time), int(y_sum / real_time), int(r_sum / real_time)], img


def detect_type(cam, mode, time_out=8, time_out_en=False):
    """
    根据所在区域，实时识别视野内对应个数的黄色圆上的贴纸种类
    :param cam: 摄像头
    :param mode: 检测模式（0 采摘区  1 放置区）
    :param time_out: 超时时间（默认8s）
    :param time_out_en: 超时允许（默认不允许超时）
    :return: 水果种类  相似度表
    """
    best_match = 0  # 初始化最佳匹配的种类的相似度
    fruit_type = 0  # 初始化水果种类为0(为0即识别失败)
    left_top = [0, 0]  # 初始化最佳匹配左上角点位置(画边界框时使用)
    right_bottom = [0, 0]  # 初始化最佳匹配右下角点位置

    t0 = time.time()  # 初始时间
    # 当在时间范围内，且未检测到水果种类
    while fruit_type == 0:
        task_time = time.time() - t0
        if not time_out_en and task_time >= time_out:
            print("\n超时\n")
            break

        # 先检测圆所在的位置，目的在于将圆区域提取出来，尽可能地排除背景干扰
        circle, img = detect_circles(cam, color=yellow, circle_number=2-mode, time_out=5, time_out_en=False)

        # 根据圆的xyr参数计算圆的外接正方形的左上(t_l)与右下(r_b)角点位置
        l_t_x = circle[0] - circle[2]
        l_t_y = circle[1] - circle[2]
        r_b_x = circle[0] + circle[2]
        r_b_y = circle[1] + circle[2]
        # 圆的外接正方形边界处理(防止有角点超出画面而在截取时报错)
        l_t_x = l_t_x if l_t_x >= 0 else 0
        l_t_y = l_t_y if l_t_y >= 0 else 0
        r_b_x = r_b_x if r_b_x <= 639 else 639
        r_b_y = r_b_y if r_b_y <= 479 else 479
        # 截取
        img_roi = img[l_t_y:r_b_y, l_t_x:r_b_x]
        
        # 排除因未检测到圆而未截取到roi，此时将在全视野内进行识别，会带来更多的背景干扰
        if not img_roi.shape[0]:
#            print("\n检测圆失败，无法识别种类或精度将降低\n")
            img_roi = img

        # 种类识别
#        print("\n------开始识别种类------\n")
        similarity = []  # 初始化相似度表
        for i in range(1, 5):  # 遍历水果种类，1 2 3 4
            pic = 0
            sim_data = []
            for j in range(1, n_pic_per_type + 1):  # 遍历这种水果的所有模板
                name = f"{i}{j}.jpg"  # 合成模板名
                template = cv2.imread(f"template_f/{name}")  # 读取模板图片
                temp_h, temp_w = template.shape[:2]  # 获得该模板的高和宽，画边界框时用
                
                # 判断模板尺寸是否超过输入图像尺寸(输入图像应是截取出来的圆的区域，若圆过圆会有小于模板尺寸的可能)
                roi_h, roi_w = img_roi.shape[:2]
                if temp_h > roi_h or temp_w > roi_w:
                    print("\nErr! templ oversize\n")
                    return None

                # 模板匹配
                res = cv2.matchTemplate(img_roi, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                
                sim_data.append(round(max_val, 5))
                
                if max_val > best_match:
                    best_match = max_val  # 更新最佳匹配的种类
                    fruit_type = i  # 记录当前种类
                    left_top = max_loc  # 记录左上角点位置，即minMaxLoc函数处理得的max_loc
                    right_bottom = (left_top[0] + temp_w, left_top[1] + temp_h)  # 记录右下角点位置
            
## # 结果展示
#                print(f"type:{fruit_mapping(i)} pic:{j} max_val:{max_val} currently detected as:{fruit_mapping(fruit_type)}")
#            print("\n")
            
            similarity.append(sim_data)  # 数据记录

        cv2.rectangle(img_roi, left_top, right_bottom, (255, 0, 255), 2)  # 图像上画边界框
        cv2.putText(img_roi, f"type{fruit_type}", left_top, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)  # 图像上显示结果
        cv2.namedWindow("match")
        cv2.moveWindow("match", 10, 0)
        cv2.imshow("match", img_roi)  # 显示图像
        cv2.waitKey(1500)

    cv2.destroyAllWindows()
    print(f"fruit type detected as: {fruit_mapping(fruit_type)}")
    return fruit_type, similarity
