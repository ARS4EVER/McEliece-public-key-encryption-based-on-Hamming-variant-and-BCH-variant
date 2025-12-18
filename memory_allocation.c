#include <stdio.h> 
 #include <stdlib.h> 
 #include <time.h> 
 #include <stdbool.h> 
 
 #define M_S 1024//内存的总字节数 
 #define Total_Procs 10//总进程数 
 #define Min_R 100//最少的请求内存 
 #define Max_R 200//最多的请求内存 
 
 typedef struct Block { 
     int id;// 块号 
     int startAddr; // 起始地址 
     int endAddr;// 结束地址 
     bool free; //表示一个块是否空闲 
     int pid;//进程号, -1表示没有分配 
     struct Block* prev;//指向上一个块 
     struct Block* next;//指向下一个块 
 } Block; 
 
 typedef struct PCB { 
     int pid;//进程的编号 
     int req;//请求内存大小 
     int status;//1表示已分配，-1表示分配 
     int blockID;//分配的块id，-1表示未分配 
     struct PCB* next; 
 } PCB; 
 
 static int Block_ID = 0;//分配全局ID 
 static Block* head = NULL; //指向内存块链表的头 
 
 //从双向链表数组指定索引的链表中删除节点 
 void remove_node(Block* node) { 
     if (!node) return; 
     if (node->prev) node->prev->next = node->next; 
     else head = node->next; // node 是头节点 
     if (node->next) node->next->prev = node->prev; 
     node->prev = node->next = NULL; 
 } 
 
 //创建新的内存块 
 Block* new_block(int startAddr, int endAddr, bool free, int pid) { 
     Block* b = (Block*)malloc(sizeof(Block)); 
     if (!b) { perror("malloc"); exit(1); } 
     b->id = ++Block_ID; 
     b->startAddr = startAddr; 
     b->endAddr = endAddr; 
     b->free = free; 
     b->pid = pid; 
     b->prev = b->next = NULL; 
     return b; 
 } 
 
 //把节点根据起始地址的升序，插入到全局链表里面 
 void insert_sorted(Block* node) { 
   if (!node) return; 
     if (!head) { 
         head = node; 
         return; 
     } 
     //插入到头部 
     if (node->startAddr < head->startAddr) { 
         node->next = head; 
         head->prev = node; 
         head = node; 
         return; 
     } 
     //从前向后查找插入节点的位置 
     Block* cur = head; 
    while (cur->next && cur->next->startAddr < node->startAddr) cur = cur->next; 
    node->next = cur->next; 
    if (cur->next) cur->next->prev = node; 
    cur->next = node; 
    node->prev = cur; 
 } 
 
 //这里是实现首次适用算法的部分，需要按照块的大小，查找第一个可以放下need大小的字节的空闲块 
 Block* find_first_fit(int need) { 
     Block* t = head; 
     while (t) { 
         if (t->free) { 
             int sz = t->endAddr - t->startAddr + 1; 
             if (sz >= need) return t; 
         } 
         t = t->next; 
     } 
     return NULL; 
 } 
 
 //实现最佳适应算法，查找最小的可以放下need大小的空闲块 
 Block* find_best_fit(int need) { 
     Block* t = head; 
     Block* best = NULL; 
     int best_size = M_S + 1; // 初始化为大于最大内存的值 
     while (t) { 
         if (t->free) { 
             int sz = t->endAddr - t->startAddr + 1; 
             if (sz >= need && sz < best_size) { 
                 best = t; 
                 best_size = sz; 
             } 
         } 
         t = t->next; 
     } 
     return best; 
 } 
 
 //实现最坏适应算法，查找最大的可以放下need大小的空闲块 
 Block* find_worst_fit(int need) { 
     Block* t = head; 
     Block* worst = NULL; 
     int worst_size = 0; 
     while (t) { 
         if (t->free) { 
             int sz = t->endAddr - t->startAddr + 1; 
             if (sz >= need && sz > worst_size) { 
                 worst = t; 
                 worst_size = sz; 
             } 
         } 
         t = t->next; 
     } 
     return worst; 
 } 
 
 //根据起始地址查找内存块，用于定位 
 Block* find_by_start(int start) { 
     Block* t = head; 
     while (t) { 
         if (t->startAddr == start) return t; 
         t = t->next; 
     } 
     return NULL; 
 } 
 
 //根据块ID查找内存块，也是用于定位 
 Block* find_by_id(int id) { 
     Block* t = head; 
     while (t) { 
         if (t->id == id) return t; 
         t = t->next; 
     } 
     return NULL; 
 } 
 
 //打印现在各个内存块的状态 
 void print_state() { 
     printf("空闲块 起始地址 大小\n"); 
     Block* t = head; 
     while (t) { 
         if (t->free) { 
             printf("%6d %9d %5d\n", t->id, t->startAddr, t->endAddr - t->startAddr + 1); 
         } 
         t = t->next; 
     } 
     printf("————————————————————————————————————————————————————\n"); 
     printf("已用的块 起始地址 大小 进程号\n"); 
     t = head; 
     while (t) { 
         if (!t->free) { 
             printf("%6d %9d %5d %6d\n", t->id, t->startAddr, t->endAddr - t->startAddr + 1, t->pid); 
         } 
         t = t->next; 
     } 
     printf("————————————————————————————————————————————————————\n\n"); 
 } 
 
 //这里是将选出的空闲块作为target，按照请求的大小req，进行随机起始地址的分配，并且分割成三块，剩余块、分配块、剩余块； 
 //随机选择好起始地址，将选出的空闲块target删除，然后将分割后的三块插入链表 
 Block* split_and_alloc(Block* target, int req) { 
     if (!target) return NULL; 
     int bsize = target->endAddr - target->startAddr + 1; 
     if (req > bsize) return NULL; 
     int maxStart = target->endAddr - req + 1; 
     int allocStart = target->startAddr + (rand() % (maxStart - target->startAddr + 1)); 
     int allocEnd = allocStart + req - 1; 
     remove_node(target); 
     if (target->startAddr <= allocStart - 1) { 
         Block* left = new_block(target->startAddr, allocStart - 1, true, -1); 
         insert_sorted(left); 
     } 
     Block* alloc = new_block(allocStart, allocEnd, false, -1); 
     insert_sorted(alloc); 
     if (allocEnd + 1 <= target->endAddr) { 
         Block* right = new_block(allocEnd + 1, target->endAddr, true, -1); 
         insert_sorted(right); 
     } 
     free(target); 
     return alloc; 
 } 
 
 //遍历内存块链表，检查当前块和下一块是否同时满足空闲且两者地址连续；若满足，将两块合并：更新当前块的结束地址为下一块的结束地址，删除下一块节点并释放内存；若不满足，继续遍历下一个节点 
 void combine_free() { 
     Block* t = head; 
     while (t && t->next) { 
         if (t->free && t->next->free && t->endAddr + 1 == t->next->startAddr) { 
             Block* nxt = t->next; 
             t->endAddr = nxt->endAddr; 
             t->next = nxt->next; 
             if (nxt->next) nxt->next->prev = t; 
             free(nxt); 
         } 
         else { 
             t = t->next; 
         } 
     } 
 } 
 
 //这里是打印题目中所要求的十个进程所需要的内存 
 void print_Procreq(int reqs[], int n) { 
     printf("这10个进程的所需要的内存:\n"); 
     for (int i = 0; i < n; ++i) { 
         printf("进程 %2d: %d\n", i, reqs[i]); 
     } 
     printf("\n"); 
 } 
 
 //首次适应算法的实现 
 void first_fit(int reqs[], int n) { 
     printf("———————————— 首次适应算法 (FF) ————————————\n"); 
     while (head) { Block* t = head; head = head->next; free(t); } //要先清理旧的链表 
     Block_ID = 0; 
     head = new_block(0, M_S - 1, true, -1);//初始化了一个空闲的块 
     PCB* pcb_head = NULL; 
     PCB* pcb_tail = NULL; 
     for (int i = 0; i < n; ++i) { 
         PCB* p = (PCB*)malloc(sizeof(PCB));//每个进程都需要PCB节点 
         p->pid = i; 
         p->req = reqs[i]; 
         p->status = -1; 
         p->blockID = -1; 
         p->next = NULL;//这里的属性的值含义与前面的PCB结构体描述的一样 
         if (!pcb_head) pcb_head = pcb_tail = p; 
         else { pcb_tail->next = p; pcb_tail = p; } 
     } 
     printf("初始内存状态:\n"); 
     print_state(); 
     //这是为每个进程分配内存的环节 
     PCB* p = pcb_head; 
     while (p) { 
         printf("为进程 %d 分配内存, 需求=%d 字节\n", p->pid, p->req); 
         Block* candidate = find_first_fit(p->req); 
         if (!candidate) { 
             printf("分配失败: 没有足够大的空闲分区!\n"); 
         } 
         else { 
             Block* alloc = split_and_alloc(candidate, p->req); 
             if (alloc) { 
                 alloc->pid = p->pid; 
                 p->blockID = alloc->id; 
                 p->status = 1; 
                 printf("分配成功!\n"); 
             } 
             else { 
                 printf("分配失败: 划分出错!\n"); 
             } 
         } 
         printf("————————————————————————————————————————\n"); 
         print_state(); 
         p = p->next; 
     } 
     // 按PCB顺序回收已经分配的分块 
    printf("———————————— FF 回收阶段 ————————————\n"); 
     p = pcb_head; 
     while (p) { 
         if (p->status == 1 && p->blockID != -1) { 
             printf("回收进程 %d 所占用的内存（块ID=%d）...\n", p->pid, p->blockID); 
             Block* blk = find_by_id(p->blockID); 
             if (blk) { 
                 blk->free = true; 
                 blk->pid = -1; 
                 combine_free();//回收后要尝试合并空闲块 
             } 
             printf("————————————————————————————————————————\n"); 
             print_state(); 
         } 
         p = p->next; 
     } 
     while (pcb_head) { PCB* tmp = pcb_head; pcb_head = pcb_head->next; free(tmp); } 
     while (head) { Block* tmp = head; head = head->next; free(tmp); }//清理内存，释放所有的节点 
     head = NULL; 
 } 
 
 //循环首次适应算法的实现 
 void next_fit(int reqs[], int n) { 
     printf("———————————— 循环首次适应算法 (NF) ————————————\n"); 
     while (head) { Block* t = head; head = head->next; free(t); }//清理旧链表 
     Block_ID = 0; 
     head = new_block(0, M_S - 1, true, -1); 
     PCB* pcb_head = NULL; 
     PCB* pcb_tail = NULL; 
     for (int i = 0; i < n; ++i) { 
         PCB* p = (PCB*)malloc(sizeof(PCB)); 
         p->pid = i; 
         p->req = reqs[i]; 
         p->status = -1; 
         p->blockID = -1; 
         p->next = NULL;//这里的属性值的含义与前面的一样 
         if (!pcb_head) pcb_head = pcb_tail = p; 
         else { pcb_tail->next = p; pcb_tail = p; } 
     } 
     printf("初始内存状态:\n"); 
     print_state(); 
     int last_addr = 0;//这里是与FF的区别，用last_addr记录下一次查找的起始地址，从last_addr开始向后查找符合条件的空闲块，若向后未找到则从头开始查找到last_addr之前 
     PCB* p = pcb_head; 
     while (p) { 
         printf("为进程 %d 分配内存, 需求=%d 字节\n", p->pid, p->req); 
         Block* candidate = NULL; 
         Block* t = head; 
         while (t) { 
             if (t->startAddr >= last_addr && t->free) { 
                 int bsize = t->endAddr - t->startAddr + 1; 
                 if (bsize >= p->req) { candidate = t; break; } 
             } 
             t = t->next; 
         } 
         if (!candidate) { 
             t = head; 
             while (t && t->startAddr < last_addr) { 
                 if (t->free) { 
                     int bsize = t->endAddr - t->startAddr + 1; 
                     if (bsize >= p->req) { candidate = t; break; } 
                 } 
                 t = t->next; 
             } 
         } 
         if (!candidate) { 
             printf("分配失败: 没有足够大的空闲分区!\n"); 
         } 
         else { 
             Block* alloc = split_and_alloc(candidate, p->req); 
             if (alloc) { 
                 alloc->pid = p->pid; 
                 p->blockID = alloc->id; 
                 p->status = 1; 
                 last_addr = alloc->endAddr + 1;//把本次分配块的下一个地址作为last_addr，作为下一次查找的起始地址 
                 if (last_addr >= M_S) last_addr = 0; 
                 printf("分配成功!\n"); 
             } 
             else { 
                 printf("分配失败: 划分出错!\n"); 
             } 
         } 
         printf("————————————————————————————————————————\n"); 
         print_state(); 
         p = p->next; 
     } 
     // 按PCB顺序回收 
     printf("———————————— NF 回收阶段 ————————————\n"); 
     p = pcb_head; 
     while (p) { 
         if (p->status == 1 && p->blockID != -1) { 
             printf("回收进程 %d 所占用的内存（块ID=%d）...\n", p->pid, p->blockID); 
             Block* blk = find_by_id(p->blockID); 
             if (blk) { 
                 blk->free = true; 
                 blk->pid = -1; 
                 combine_free(); 
             } 
             printf("—————————————————————————————————————\n"); 
             print_state(); 
         } 
         p = p->next; 
     } 
     //与FF算法的实现相同，也要清理内存 
     while (pcb_head) { PCB* tmp = pcb_head; pcb_head = pcb_head->next; free(tmp); } 
     while (head) { Block* tmp = head; head = head->next; free(tmp); } 
     head = NULL; 
 } 
 
 //最佳适应算法的实现 
 void best_fit(int reqs[], int n) { 
     printf("———————————— 最佳适应算法 (BF) ————————————\n"); 
     while (head) { Block* t = head; head = head->next; free(t); } 
     Block_ID = 0; 
     head = new_block(0, M_S - 1, true, -1); 
     PCB* pcb_head = NULL; 
     PCB* pcb_tail = NULL; 
     for (int i = 0; i < n; ++i) { 
         PCB* p = (PCB*)malloc(sizeof(PCB)); 
         p->pid = i; 
         p->req = reqs[i]; 
         p->status = -1; 
         p->blockID = -1; 
         p->next = NULL; 
         if (!pcb_head) pcb_head = pcb_tail = p; 
         else { pcb_tail->next = p; pcb_tail = p; } 
     } 
     printf("初始内存状态:\n"); 
     print_state(); 
     PCB* p = pcb_head; 
     while (p) { 
         printf("为进程 %d 分配内存, 需求=%d 字节\n", p->pid, p->req); 
         Block* candidate = find_best_fit(p->req); 
         if (!candidate) { 
             printf("分配失败: 没有足够大的空闲分区!\n"); 
         } 
         else { 
             Block* alloc = split_and_alloc(candidate, p->req); 
             if (alloc) { 
                 alloc->pid = p->pid; 
                 p->blockID = alloc->id; 
                 p->status = 1; 
                 printf("分配成功!\n"); 
             } 
             else { 
                 printf("分配失败: 划分出错!\n"); 
             } 
         } 
         printf("————————————————————————————————————————\n"); 
         print_state(); 
         p = p->next; 
     } 
     printf("———————————— BF 回收阶段 ————————————\n"); 
     p = pcb_head; 
     while (p) { 
         if (p->status == 1 && p->blockID != -1) { 
             printf("回收进程 %d 所占用的内存（块ID=%d）...\n", p->pid, p->blockID); 
             Block* blk = find_by_id(p->blockID); 
             if (blk) { 
                 blk->free = true; 
                 blk->pid = -1; 
                 combine_free(); 
             } 
             printf("————————————————————————————————————————\n"); 
             print_state(); 
         } 
         p = p->next; 
     } 
     while (pcb_head) { PCB* tmp = pcb_head; pcb_head = pcb_head->next; free(tmp); } 
     while (head) { Block* tmp = head; head = head->next; free(tmp); } 
     head = NULL; 
 } 
 
 //最坏适应算法的实现 
 void worst_fit(int reqs[], int n) { 
     printf("———————————— 最坏适应算法 (WF) ————————————\n"); 
     while (head) { Block* t = head; head = head->next; free(t); } 
     Block_ID = 0; 
     head = new_block(0, M_S - 1, true, -1); 
     PCB* pcb_head = NULL; 
     PCB* pcb_tail = NULL; 
     for (int i = 0; i < n; ++i) { 
         PCB* p = (PCB*)malloc(sizeof(PCB)); 
         p->pid = i; 
         p->req = reqs[i]; 
         p->status = -1; 
         p->blockID = -1; 
         p->next = NULL; 
         if (!pcb_head) pcb_head = pcb_tail = p; 
         else { pcb_tail->next = p; pcb_tail = p; } 
     } 
     printf("初始内存状态:\n"); 
     print_state(); 
     PCB* p = pcb_head; 
     while (p) { 
         printf("为进程 %d 分配内存, 需求=%d 字节\n", p->pid, p->req); 
         Block* candidate = find_worst_fit(p->req); 
         if (!candidate) { 
             printf("分配失败: 没有足够大的空闲分区!\n"); 
         } 
         else { 
             Block* alloc = split_and_alloc(candidate, p->req); 
             if (alloc) { 
                 alloc->pid = p->pid; 
                 p->blockID = alloc->id; 
                 p->status = 1; 
                 printf("分配成功!\n"); 
             } 
             else { 
                 printf("分配失败: 划分出错!\n"); 
             } 
         } 
         printf("————————————————————————————————————————\n"); 
         print_state(); 
         p = p->next; 
     } 
     printf("———————————— WF 回收阶段 ————————————\n"); 
     p = pcb_head; 
     while (p) { 
         if (p->status == 1 && p->blockID != -1) { 
             printf("回收进程 %d 所占用的内存（块ID=%d）...\n", p->pid, p->blockID); 
             Block* blk = find_by_id(p->blockID); 
             if (blk) { 
                 blk->free = true; 
                 blk->pid = -1; 
                 combine_free(); 
             } 
             printf("————————————————————————————————————————\n"); 
             print_state(); 
         } 
         p = p->next; 
     } 
     while (pcb_head) { PCB* tmp = pcb_head; pcb_head = pcb_head->next; free(tmp); } 
     while (head) { Block* tmp = head; head = head->next; free(tmp); } 
     head = NULL; 
 } 
 
 int main(int argc, char* argv[]) { 
     unsigned int seed; 
     if (argc >= 2) seed = (unsigned int)atoi(argv[1]); 
     else seed = (unsigned int)time(NULL); 
     srand(seed); 
     //这里生成了10个随机请求，分别用于FF和NF 
     int reqs[Total_Procs]; 
     for (int i = 0; i < Total_Procs; ++i) { 
         reqs[i] = Min_R + rand() % (Max_R - Min_R + 1); 
     } 
 
     //起始的时候的内存状态 
     printf("随机种子: %u\n", seed); 
     printf("初始的内存状态:\n"); 
     printf("空闲块 起始地址 大小\n"); 
     printf("    0 %9d %5d\n", 0, M_S); 
     printf("————————————————————————————————————————————————————\n"); 
     printf("已用的块 起始地址 大小 进程号\n"); 
     printf("————————————————————————————————————————————————————\n\n"); 
 
     print_Procreq(reqs, Total_Procs); 
     first_fit(reqs, Total_Procs); 
     printf("\n\n"); 
     next_fit(reqs, Total_Procs); 
     printf("\n\n"); 
     best_fit(reqs, Total_Procs); 
     printf("\n\n"); 
     worst_fit(reqs, Total_Procs); 
 
     return 0; 
 }