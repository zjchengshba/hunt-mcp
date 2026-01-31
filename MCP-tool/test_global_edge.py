import cv2
import numpy as np
import requests
import os

# 块图片（保留，兼容原有逻辑）
blockJpg = 'image/block.jpg'
# 模板图片
templateJpg = 'image/template.jpg'

# 创建图片目录
os.makedirs('image', exist_ok=True)

# 验证码图片 URL
bg_url = 'https://cas-captcha-static.sf-express.com/captcha-fdn/hypic/7142313a32a0413fa665e7a661b851ba.png'
block_url = 'https://cas-captcha-static.sf-express.com/captcha-fdn/hypic/9de335f3695843fcb21a2f07fd045af5.png'

print("正在下载验证码图片...")

# 下载背景图
response = requests.get(bg_url)
with open(templateJpg, 'wb') as f:
    f.write(response.content)
print(f"背景图已保存到: {templateJpg}")

# 下载滑块图
response = requests.get(block_url)
with open(blockJpg, 'wb') as f:
    f.write(response.content)
print(f"滑块图已保存到: {blockJpg}")

print("\n开始计算缺口位置（使用全局边缘匹配）...")

# 计算缺口的位置（替换为全局边缘匹配方案）
def calculate_distance(bkg, blk):
    try:
        # 读取图片
        tp = cv2.imread(bkg, cv2.IMREAD_COLOR)
        blk_img = cv2.imread(blk, cv2.IMREAD_COLOR)
        if tp is None or blk_img is None:
            print("图片读取失败")
            return None, None

        # ===================== 1. 对拼图块做边缘检测（生成边缘模板） =====================
        gray_piece = cv2.cvtColor(blk_img, cv2.COLOR_BGR2GRAY)
        gray_piece_blur = cv2.GaussianBlur(gray_piece, (3,3), 0)
        edges_piece = cv2.Canny(gray_piece_blur, 50, 150)
        # 膨胀边缘，增强特征
        kernel = np.ones((2, 2), np.uint8)
        edges_piece = cv2.dilate(edges_piece, kernel, iterations=1)
        cv2.imwrite('image/debug_piece_edges.jpg', edges_piece)

        # ===================== 2. 对背景图做全局边缘检测 =====================
        gray_bg = cv2.cvtColor(tp, cv2.COLOR_BGR2GRAY)
        gray_bg_blur = cv2.GaussianBlur(gray_bg, (3,3), 0)
        edges_bg = cv2.Canny(gray_bg_blur, 50, 150)
        edges_bg = cv2.dilate(edges_bg, kernel, iterations=1)
        cv2.imwrite('image/debug_bg_edges.jpg', edges_bg)

        # ===================== 3. 全局边缘模板匹配 =====================
        res = cv2.matchTemplate(edges_bg, edges_piece, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        gap_x, gap_y = max_loc  # 匹配到的峰值坐标就是缺口位置

        # 获取拼图块尺寸
        h, w = edges_piece.shape

        # ===================== 4. 精准标注缺口 =====================
        # 黄色粗线：匹配到的边缘区域
        cv2.rectangle(tp, (gap_x, gap_y), (gap_x + w, gap_y + h), (0, 255, 255), 3)
        # 蓝色框：缺口范围
        cv2.rectangle(tp, (gap_x, gap_y), (gap_x + w, gap_y + h), (255, 0, 0), 2)
        # 文字标注
        cv2.putText(tp, f'Gap X: {gap_x}', (gap_x, gap_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imwrite('image/result_with_gap.jpg', tp)

        print(f"✅ 缺口已精准标注，位置：x={gap_x}")
        return gap_x, tp

    except Exception as e:
        print(f"计算距离出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# 模拟人为拖动滑块行为（保留原有逻辑）
def get_tracks(dis):
    v = 0
    m = 0.3
    tracks = []
    current = 0
    mid = dis * 4 / 5

    while current <= dis:
        if current < mid:
            a = 2
        else:
            a = -3

        v0 = v
        s = v0 * m + 0.5 * a * (m ** 2)
        current += s
        tracks.append(round(s))
        v = v0 + a * m

    return tracks

if __name__ == "__main__":
    bkg = templateJpg
    blk = blockJpg

    print("请先使用 Playwright MCP 获取验证码图片并保存到:")
    print(f"  背景图: {templateJpg}")
    print(f"  滑块图: {blockJpg}")
    print("\n然后运行此脚本计算移动距离")

    if os.path.exists(bkg) and os.path.exists(blk):
        distance, temp = calculate_distance(bkg, blk)

        if distance is not None:
            print(f"\n========== 需要移动的距离: {distance} 像素 ==========\n")

            # 计算实际需要移动的距离（考虑图片缩放）
            scale_factor = 1  # 根据实际网页尺寸调整
            double_distance = int(distance * scale_factor)

            print(f"调整后的移动距离: {double_distance} 像素")

            # 生成拖动轨迹
            tracks = get_tracks(double_distance)
            tracks.append(-(sum(tracks) - double_distance))

            print(f"拖动轨迹: {tracks}")
            print(f"轨迹总长度: {sum(tracks)} 像素")

            # 保存轨迹到文件
            with open('image/tracks.txt', 'w') as f:
                f.write(f"{double_distance}\n")
                f.write(','.join(map(str, tracks)))

            print(f"\n轨迹已保存到 image/tracks.txt")
            print("✅ 缺口标注图已保存到 image/result_with_gap.jpg")
            print("请将此距离传递给 Playwright MCP 执行拖动操作")
        else:
            print("无法计算缺口位置，请刷新验证码重试")
    else:
        print(f"验证码图片不存在，请先获取图片")
