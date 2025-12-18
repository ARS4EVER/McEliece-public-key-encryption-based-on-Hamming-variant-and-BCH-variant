#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// 常量定义
#define PHYS_PAGES 3       // 物理内存页面数
#define TOTAL_PAGES 10     // 进程总页数
#define ACCESS_SEQ_LENGTH 20 // 页面访问序列长度

// 页面访问序列
int access_sequence[ACCESS_SEQ_LENGTH];

// 物理内存页框结构
typedef struct {
    int page_num;     // 页面号，-1表示空闲
    int last_access;  // 最后访问时间（时钟值）
} PageFrame;

// 生成页面访问序列
void generate_access_sequence() {
    int i;
    srand((unsigned int)time(NULL));
    printf("生成的页面访问序列:\n");
    for (i = 0; i < ACCESS_SEQ_LENGTH; i++) {
        // 随机生成0-9的页面号
        access_sequence[i] = rand() % TOTAL_PAGES;
        printf("%d ", access_sequence[i]);
    }
    printf("\n\n");
}

// 检查页面是否在物理内存中
int is_page_in_memory(PageFrame frames[], int page_num) {
    int i;
    for (i = 0; i < PHYS_PAGES; i++) {
        if (frames[i].page_num == page_num) {
            return i;  // 返回页框索引
        }
    }
    return -1;  // 不在内存中
}

// 查找最近最少使用的页框
int find_lru_page(PageFrame frames[]) {
    int i, lru_index = 0, min_time = frames[0].last_access;
    
    for (i = 1; i < PHYS_PAGES; i++) {
        if (frames[i].last_access < min_time) {
            min_time = frames[i].last_access;
            lru_index = i;
        }
    }
    
    return lru_index;
}

// 打印物理内存页框状态
void print_page_frames(PageFrame frames[], int step) {
    int i;
    printf("步骤 %2d: ", step);
    for (i = 0; i < PHYS_PAGES; i++) {
        if (frames[i].page_num == -1) {
            printf("[   ] ");
        } else {
            printf("[%3d] ", frames[i].page_num);
        }
    }
}

// 实现LRU页面置换算法
void lru_page_replacement() {
    PageFrame frames[PHYS_PAGES];
    int i, step, clock = 0, hit_count = 0, miss_count = 0;
    int page_num, frame_index, lru_index;
    float miss_rate;
    
    // 初始化物理内存页框
    for (i = 0; i < PHYS_PAGES; i++) {
        frames[i].page_num = -1;
        frames[i].last_access = -1;
    }
    
    printf("LRU页面置换算法模拟\n");
    printf("物理内存页框数: %d\n", PHYS_PAGES);
    printf("进程总页数: %d\n", TOTAL_PAGES);
    printf("--------------------------------------------------\n");
    
    // 处理每个页面访问
    for (step = 0; step < ACCESS_SEQ_LENGTH; step++) {
        page_num = access_sequence[step];
        printf("访问页面: %d -> ", page_num);
        
        // 检查页面是否在物理内存中
        frame_index = is_page_in_memory(frames, page_num);
        
        if (frame_index != -1) {
            // 页面命中
            hit_count++;
            frames[frame_index].last_access = clock;
            print_page_frames(frames, step + 1);
            printf("[命中]\n");
        } else {
            // 页面缺失
            miss_count++;
            
            // 查找最近最少使用的页框
            lru_index = find_lru_page(frames);
            
            // 替换页面
            frames[lru_index].page_num = page_num;
            frames[lru_index].last_access = clock;
            
            print_page_frames(frames, step + 1);
            printf("[缺失]\n");
        }
        
        clock++;
    }
    
    // 计算缺页率
    miss_rate = (float)miss_count / ACCESS_SEQ_LENGTH;
    
    // 输出统计结果
    printf("\n");
    printf("--------------------------------------------------\n");
    printf("LRU页面置换算法统计结果\n");
    printf("--------------------------------------------------\n");
    printf("访问序列长度: %d\n", ACCESS_SEQ_LENGTH);
    printf("命中次数: %d\n", hit_count);
    printf("缺页次数: %d\n", miss_count);
    printf("缺页率: %.2f%%\n", miss_rate * 100);
    printf("--------------------------------------------------\n");
}

// 主函数
int main() {
    // 生成页面访问序列
    generate_access_sequence();
    
    // 执行LRU页面置换算法
    lru_page_replacement();
    
    return 0;
}