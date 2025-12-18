import random

PHYS_PAGES = 3  # 物理内存页面数
TOTAL_PAGES = 10  # 进程总页数
ACCESS_SEQ_LENGTH = 20  # 页面访问序列长度

# 生成页面访问序列
def generate_access_sequence():
    access_sequence = [random.randint(0, TOTAL_PAGES - 1) for _ in range(ACCESS_SEQ_LENGTH)]
    print("生成的页面访问序列:")
    for page in access_sequence:
        print(f"{page} ", end="")
    print("\n")
    return access_sequence

# 检查页面是否在物理内存中
def is_page_in_memory(frames, page_num):
    for i in range(PHYS_PAGES):
        if frames[i][0] == page_num:
            return i  # 返回页框索引
    return -1  # 不在内存中

# 查找最近最少使用的页框
def find_lru_page(frames):
    lru_index = 0
    min_time = frames[0][1]
    
    for i in range(1, PHYS_PAGES):
        if frames[i][1] < min_time:
            min_time = frames[i][1]
            lru_index = i
    
    return lru_index

# 打印物理内存页框状态
def print_page_frames(frames, step):
    print(f"步骤 {step:2d}: ", end="")
    for i in range(PHYS_PAGES):
        page_num = frames[i][0]
        if page_num == -1:
            print("[   ] ", end="")
        else:
            print(f"[{page_num:3d}] ", end="")

# 实现LRU页面置换算法
def lru_page_replacement(access_sequence):
    # 初始化物理内存页框，每个页框存储(page_num, last_access_time)
    frames = [(-1, -1) for _ in range(PHYS_PAGES)]
    clock = 0
    hit_count = 0
    miss_count = 0
    
    print("LRU页面置换算法模拟")
    print(f"物理内存页框数: {PHYS_PAGES}")
    print(f"进程总页数: {TOTAL_PAGES}")
    print("-" * 50)
    print()
    
    # 处理每个页面访问
    for step in range(ACCESS_SEQ_LENGTH):
        page_num = access_sequence[step]
        print(f"访问页面: {page_num} -> ", end="")
        
        # 检查页面是否在物理内存中
        frame_index = is_page_in_memory(frames, page_num)
        
        if frame_index != -1:
            # 页面命中
            hit_count += 1
            # 更新最后访问时间
            frames[frame_index] = (page_num, clock)
            print_page_frames(frames, step + 1)
            print("[命中]")
        else:
            # 页面缺失
            miss_count += 1
            
            # 查找最近最少使用的页框
            lru_index = find_lru_page(frames)
            
            # 替换页面
            frames[lru_index] = (page_num, clock)
            
            print_page_frames(frames, step + 1)
            print("[缺失]")
        
        clock += 1
    
    # 计算缺页率
    miss_rate = miss_count / ACCESS_SEQ_LENGTH
    
    # 输出统计结果
    print()
    print("-" * 50)
    print("LRU页面置换算法统计结果")
    print("-" * 50)
    print(f"访问序列长度: {ACCESS_SEQ_LENGTH}")
    print(f"命中次数: {hit_count}")
    print(f"缺页次数: {miss_count}")
    print(f"缺页率: {miss_rate:.2%}")
    print("-" * 50)

def main():
    # 生成页面访问序列
    access_sequence = generate_access_sequence()
    
    # 执行LRU页面置换算法
    lru_page_replacement(access_sequence)

if __name__ == "__main__":
    main()