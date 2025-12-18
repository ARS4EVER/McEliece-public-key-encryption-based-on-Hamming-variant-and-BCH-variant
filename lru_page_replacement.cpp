#include <iostream>
#include <cstdlib>
#include <ctime>
#include <iomanip>

// 常量定义
const int PHYS_PAGES = 3;       // 物理内存页面数
const int TOTAL_PAGES = 10;     // 进程总页数
const int ACCESS_SEQ_LENGTH = 20; // 页面访问序列长度

// 页面访问序列
int access_sequence[ACCESS_SEQ_LENGTH];

// 物理内存页框结构
typedef struct {
    int page_num;     // 页面号，-1表示空闲
    int last_access;  // 最后访问时间（时钟值）
} PageFrame;

// 生成页面访问序列
void generate_access_sequence() {
    std::srand(static_cast<unsigned int>(std::time(nullptr)));
    std::cout << "生成的页面访问序列:" << std::endl;
    for (int i = 0; i < ACCESS_SEQ_LENGTH; i++) {
        // 随机生成0-9的页面号
        access_sequence[i] = std::rand() % TOTAL_PAGES;
        std::cout << access_sequence[i] << " ";
    }
    std::cout << "\n" << std::endl;
}

// 检查页面是否在物理内存中
int is_page_in_memory(PageFrame frames[], int page_num) {
    for (int i = 0; i < PHYS_PAGES; i++) {
        if (frames[i].page_num == page_num) {
            return i;  // 返回页框索引
        }
    }
    return -1;  // 不在内存中
}

// 查找最近最少使用的页框
int find_lru_page(PageFrame frames[]) {
    int lru_index = 0;
    int min_time = frames[0].last_access;
    
    for (int i = 1; i < PHYS_PAGES; i++) {
        if (frames[i].last_access < min_time) {
            min_time = frames[i].last_access;
            lru_index = i;
        }
    }
    
    return lru_index;
}

// 打印物理内存页框状态
void print_page_frames(PageFrame frames[], int step) {
    std::cout << "步骤 " << std::setw(2) << step << ": ";
    for (int i = 0; i < PHYS_PAGES; i++) {
        if (frames[i].page_num == -1) {
            std::cout << "[   ] ";
        } else {
            std::cout << "[" << std::setw(3) << frames[i].page_num << "] ";
        }
    }
}

// 实现LRU页面置换算法
void lru_page_replacement() {
    PageFrame frames[PHYS_PAGES];
    int clock = 0;
    int hit_count = 0;
    int miss_count = 0;
    
    // 初始化物理内存页框
    for (int i = 0; i < PHYS_PAGES; i++) {
        frames[i].page_num = -1;
        frames[i].last_access = -1;
    }
    
    std::cout << "LRU页面置换算法模拟" << std::endl;
    std::cout << "物理内存页框数: " << PHYS_PAGES << std::endl;
    std::cout << "进程总页数: " << TOTAL_PAGES << std::endl;
    std::cout << "--------------------------------------------------" << std::endl;
    
    // 处理每个页面访问
    for (int step = 0; step < ACCESS_SEQ_LENGTH; step++) {
        int page_num = access_sequence[step];
        std::cout << "访问页面: " << page_num << " -> ";
        
        // 检查页面是否在物理内存中
        int frame_index = is_page_in_memory(frames, page_num);
        
        if (frame_index != -1) {
            // 页面命中
            hit_count++;
            frames[frame_index].last_access = clock;
            print_page_frames(frames, step + 1);
            std::cout << "[命中]" << std::endl;
        } else {
            // 页面缺失
            miss_count++;
            
            // 查找最近最少使用的页框
            int lru_index = find_lru_page(frames);
            
            // 替换页面
            frames[lru_index].page_num = page_num;
            frames[lru_index].last_access = clock;
            
            print_page_frames(frames, step + 1);
            std::cout << "[缺失]" << std::endl;
        }
        
        clock++;
    }
    
    // 计算缺页率
    double miss_rate = static_cast<double>(miss_count) / ACCESS_SEQ_LENGTH;
    
    // 输出统计结果
    std::cout << "\n";
    std::cout << "--------------------------------------------------" << std::endl;
    std::cout << "LRU页面置换算法统计结果" << std::endl;
    std::cout << "--------------------------------------------------" << std::endl;
    std::cout << "访问序列长度: " << ACCESS_SEQ_LENGTH << std::endl;
    std::cout << "命中次数: " << hit_count << std::endl;
    std::cout << "缺页次数: " << miss_count << std::endl;
    std::cout << "缺页率: " << std::fixed << std::setprecision(2) << miss_rate * 100 << "%" << std::endl;
    std::cout << "--------------------------------------------------" << std::endl;
}

// 主函数
int main() {
    // 生成页面访问序列
    generate_access_sequence();
    
    // 执行LRU页面置换算法
    lru_page_replacement();
    
    return 0;
}