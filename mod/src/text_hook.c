/* WitE2 中文化文本钩子：拦截引擎自身的本地化查表调用。
   定位方式为特征码扫描（函数头 + E8 调用点反查），不绑定任何固定 RVA，
   因此小版本补丁只要函数体没被重写就能继续工作。
   只改调用点的 rel32，不扫描字符串、不改游戏数据对象、不写磁盘；
   任何一步校验失败都直接放弃（游戏照常跑英文），本 DLL 只允许由配套启动器
   加载进私有 runtime。 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#include <stdint.h>
#ifdef W2CN_TEST
#include <stdio.h>
#endif

typedef const WCHAR *(__attribute__((thiscall)) *Lookup)(void *, const WCHAR *, int);
typedef int (__cdecl *CrestLoad)(const WCHAR *, void *, unsigned, int, int, int);
typedef struct { const WCHAR *key, *value; uint32_t hash; } Entry;
static HMODULE own_module;
static Entry *table;
static uint32_t table_mask, entry_count;
static BYTE *pool;
/* 第二索引：只回答精确查表未命中的键。地图标签在 MapText.csv 里是字距拆开的
   （"M o s c o w"），引擎也可能按大小写/空白变体送来；精确表仍是权威，
   这里只把忽略空格与大小写后等价的键接回同一译文。 */
static Entry *norm_table;
static uint32_t norm_mask;
static BYTE *norm_pool;
static LONG norm_hits;
static LONG probe_mask;
/* 地址覆盖表：同一条英文字面量在引擎里可能承担两种角色（CITY 既是地形图块
   目录名、又是「分配支援单位」对话框的列头），词典只有一张，只能按源串地址
   区分。这类条目在 translations.bin 里的键写成 "@@RVA:54A40C"，加载时移入本
   表、不进文本哈希；查表先用源串指针算 RVA，命中即返回该地址的译文。
   RVA 一律相对主模块（引擎自身）镜像基址，与语言包无关。 */
typedef struct { uint32_t rva; const WCHAR *value; } AddrEntry;
static AddrEntry *addr_table;
static uint32_t addr_count, addr_cap;
static BYTE *image_base;
static DWORD image_size;
static LONG addr_logged, blocked_logged;
/* 地址跳过表：有些字面量是美术路径的片段（'red'/'white'/'-green' 拼进
   //Gui//AOG-%s flag.tga、//Gui//frame%s.tga），译成中文后文件名不存在，
   引擎静默丢图、连带整行都不画。这些地址登记为「原样返回」，不参与翻译。 */
static uint32_t *skip_table;
static uint32_t skip_count, skip_cap;
static unsigned long g_ret_into_formatter;
static unsigned long g_ret_formatter_caller;
static Lookup original_lookup;
static CrestLoad original_crest;
static Entry *crest_table;
static uint32_t crest_mask, crest_count;
static LONG crest_fixes;
static LONG initialized;
static LONG hits;
static WCHAR root[MAX_PATH];
static int map_error;
static int build_norm_index(void);
static char *append_uint(char *p,unsigned long v);
static int parse_addr_key(const WCHAR *key,uint32_t *rva);
static int addr_push(uint32_t rva,const WCHAR *value);
static int parse_skip_key(const WCHAR *key,uint32_t *rva);
static int skip_push(uint32_t rva);
static const WCHAR *addr_lookup(uint32_t rva);

/* 引擎本地化查表函数的函数头：mov edx,[esp+4]; sub esp,0xAFC。
   不依赖 RVA，靠这段特征码在 .text 里定位；改版后只要函数体还在就能找到。 */
static const BYTE lookup_sig[] = {0x8b,0x54,0x24,0x04,0x81,0xec,0xfc,0x0a,0x00,0x00};
#define SIG_TRIES 200        /* 200 x 100ms = 20s，覆盖启动早期的解密/重定位 */
static int sig_tries = SIG_TRIES;

static uint32_t u32(const BYTE *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1]<<8) | ((uint32_t)p[2]<<16) | ((uint32_t)p[3]<<24);
}
static uint32_t hash_string(const WCHAR *s) {
    uint32_t h=2166136261u;
    while (*s) { h ^= (uint16_t)*s++; h *= 16777619u; }
    return h;
}
static int equal_string(const WCHAR *a,const WCHAR *b) {
    while (*a && *a==*b) { ++a; ++b; }
    return *a==*b;
}
static void copy_bytes(void *dst,const void *src,SIZE_T n) {
    BYTE *d=(BYTE *)dst; const BYTE *s=(const BYTE *)src;
    while (n--) *d++=*s++;
}
static void path_for(WCHAR *dst, const WCHAR *suffix) {
    lstrcpyW(dst,root);lstrcatW(dst,suffix);
}
/* 日志轮转：单文件超过 8 MB 就改名为 native.prev.log（只保留一份旧档），
   避免长期开着 trace 时 mod\logs\native.log 无限增长。 */
#define LOG_ROTATE_BYTES (8u*1024u*1024u)
static LONG log_lines;
static void rotate_log(const WCHAR *path) {
    WIN32_FILE_ATTRIBUTE_DATA fa;
    if(!GetFileAttributesExW(path,GetFileExInfoStandard,&fa)) return;
    if(fa.nFileSizeHigh || fa.nFileSizeLow<LOG_ROTATE_BYTES) return;
    WCHAR prev[MAX_PATH];
    int n=lstrlenW(path);
    while(n>0 && path[n-1]!=L'\\') --n;
    const WCHAR *tail=L"native.prev.log";
    int i=0;
    while(tail[i] && n+i<MAX_PATH-1) { prev[n+i]=tail[i]; ++i; }
    prev[n+i]=0;
    DeleteFileW(prev);
    MoveFileW(path,prev);
}
static void log_line(const char *s) {
    WCHAR path[MAX_PATH];DWORD count;
#ifdef W2CN_TEST
    path_for(path,L"\\logs\\native.offline-test.log");
#else
    path_for(path,L"\\logs\\native.log");
    if((InterlockedIncrement(&log_lines)&255)==0) rotate_log(path);
#endif
    HANDLE h=CreateFileW(path,FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
    if (h!=INVALID_HANDLE_VALUE) { WriteFile(h,s,(DWORD)lstrlenA(s),&count,NULL);CloseHandle(h); }
}
static int load_map(void) {
    WCHAR path[MAX_PATH];DWORD read;
    path_for(path,L"\\payload\\translations.bin");
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if (file==INVALID_HANDLE_VALUE) {map_error=1;return 0;}
    DWORD size=GetFileSize(file,NULL);
    if(size<12 || size>64u*1024u*1024u) {map_error=2;CloseHandle(file);return 0;}
    BYTE *data=HeapAlloc(GetProcessHeap(),0,size);
    if(!data) {map_error=3;CloseHandle(file);return 0;}
    int ok=ReadFile(file,data,size,&read,NULL)&&read==size;
    CloseHandle(file);
    map_error=4;
    if(!ok || data[0]!='W'||data[1]!='2'||data[2]!='C'||data[3]!='N'||data[4]!='M'||data[5]!='A'||data[6]!='P'||data[7]!='1') goto bad;
    entry_count=u32(data+8);
    map_error=5;if(!entry_count || entry_count>100000u) goto bad;
    uint32_t capacity=1;while(capacity<entry_count*2u) capacity<<=1;
    table_mask=capacity-1;
    table=HeapAlloc(GetProcessHeap(),HEAP_ZERO_MEMORY,capacity*sizeof(Entry));
    pool=HeapAlloc(GetProcessHeap(),0,size+entry_count*4u);
    map_error=6;if(!table || !pool) goto bad;
    DWORD offset=12, used=0;
    for(uint32_t i=0;i<entry_count;++i) {
        map_error=7;if(offset>size-8) goto bad;
        uint32_t a=u32(data+offset),b=u32(data+offset+4);offset+=8;
        map_error=8;if(!a || !b || a>100000u || b>100000u || (a+b)*2u>size-offset) goto bad;
        WCHAR *src=(WCHAR *)(pool+used);copy_bytes(src,data+offset,a*2u);src[a]=0;used+=(a+1)*2u;offset+=a*2u;
        WCHAR *dst=(WCHAR *)(pool+used);copy_bytes(dst,data+offset,b*2u);dst[b]=0;used+=(b+1)*2u;offset+=b*2u;
        uint32_t rva;
        if(parse_skip_key(src,&rva)) {
            map_error=11;
            if(!skip_push(rva)) goto bad;
            continue;
        }
        if(parse_addr_key(src,&rva)) {
            map_error=10;
            if(!addr_push(rva,dst)) goto bad;
            continue;
        }
        uint32_t hash=hash_string(src),index=hash&table_mask;
        while(table[index].key) index=(index+1)&table_mask;
        table[index].key=src;table[index].value=dst;table[index].hash=hash;
    }
    map_error=9;
#ifdef W2CN_TEST
    {char msg[120];DWORD wrote;wsprintfA(msg,"offset=%lu size=%lu entries=%u\r\n",offset,size,entry_count);WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),msg,lstrlenA(msg),&wrote,NULL);}
#endif
    if(offset!=size) {
        goto bad;
    }
    HeapFree(GetProcessHeap(),0,data);
    build_norm_index();
    if(addr_count) {
        char msg[64],*p=msg;
        const char *head="addr overrides: ";
        while(*head)*p++=*head++;
        p=append_uint(p,(unsigned long)addr_count);
        const char *tail="\r\n";
        while(*tail)*p++=*tail++;
        *p=0;
        log_line(msg);
    }
    if(skip_count) {
        char msg[64],*p=msg;
        const char *head="addr skips: ";
        while(*head)*p++=*head++;
        p=append_uint(p,(unsigned long)skip_count);
        const char *tail="\r\n";
        while(*tail)*p++=*tail++;
        *p=0;
        log_line(msg);
    }
    return 1;
bad:
    if(table) HeapFree(GetProcessHeap(),0,table);
    if(pool) HeapFree(GetProcessHeap(),0,pool);
    table=NULL;pool=NULL;HeapFree(GetProcessHeap(),0,data);return 0;
}
/* ---------- 地图标签键归一化（第二索引） ----------
   地图文字在 MapText.csv 里常按字距拆开（"M o s c o w"）；引擎送进查表的键
   还可能带大小写或首尾空白差异。精确表仍是唯一权威，第二索引只处理精确表
   未命中的键，且同一归一化键对应两种译文时整键停用，绝不猜。 */
static int normalize_key(const WCHAR *src,WCHAR *dst,int cap) {
    int n=0;
    for(;*src;++src) {
        WCHAR c=*src;
        if(c==0x20||c==0x09||c==0x0a||c==0x0d||c==0xa0||c==0x3000) continue;
        if(c>='A'&&c<='Z') c=(WCHAR)(c+32);
        if(n>=cap-1) return 0;
        dst[n++]=c;
    }
    dst[n]=0;
    return n>0;
}
static const WCHAR *norm_lookup(const WCHAR *norm) {
    if(!norm_table) return NULL;
    uint32_t hash=hash_string(norm),i=hash&norm_mask;
    while(norm_table[i].key) {
        if(norm_table[i].hash==hash && equal_string(norm_table[i].key,norm)) return norm_table[i].value;
        i=(i+1)&norm_mask;
    }
    return NULL;
}
/* 只读探针：地图标签到底有没有走这个查表入口、查到了什么、从哪调进来。
   每个城市只写一行；不改任何返回值。 */
static const WCHAR *probe_names[]={L"moscow",L"berlin",L"leningrad",L"stalingrad",L"kiev",L"kharkov",L"odessa",L"sevastopol",NULL};
static void append_hex(char **out,char *end,unsigned long v) {
    char tmp[12];int n=0;
    const char *hex="0123456789abcdef";
    if(!v){ if(*out<end)*(*out)++='0'; return; }
    while(v&&n<8){tmp[n++]=hex[v&15u];v>>=4;}
    while(n&&*out<end)*(*out)++=tmp[--n];
}
static void probe_map_label(const WCHAR *norm,const WCHAR *source,int exact,const WCHAR *value) {
    for(int i=0;probe_names[i];++i) {
        if(!equal_string(norm,probe_names[i])) continue;
        LONG bit=1L<<i,previous=InterlockedOr(&probe_mask,bit);
        if(previous&bit) return;
        char msg[320],*p=msg,*end=msg+sizeof(msg)-2;
        const char *head="PROBE map label: name=";
        while(*head&&p<end)*p++=*head++;
        for(const WCHAR *s=probe_names[i];*s&&p<end;++s)*p++=(char)*s;
        const char *src=" src=\"";
        while(*src&&p<end)*p++=*src++;
        for(const WCHAR *s=source;*s&&p<end;++s) {
            WCHAR c=*s;
            *p++=(c>=32&&c<127)?(char)c:'?';
        }
        *p++='"';
        const char *tail=" exact=";
        while(*tail&&p<end)*p++=*tail++;
        *p++=exact?'1':'0';
        const char *nt=" norm=";
        while(*nt&&p<end)*p++=*nt++;
        int norm_hit=0;
        if(!exact&&value) norm_hit=1;
        *p++=norm_hit?'1':'0';
        const char *ot=" out=";
        while(*ot&&p<end)*p++=*ot++;
        int zh=0;
        if(value) for(const WCHAR *s=value;*s;++s) if(*s>=0x2e80){zh=1;break;}
        *p++=zh?'z':'e';*p++=zh?'h':'n';
        const char *bp=" srcaddr=";
        while(*bp&&p<end)*p++=*bp++;
        append_hex(&p,end,(unsigned long)(ULONG_PTR)source);
        const char *pr=" prot=";
        while(*pr&&p<end)*p++=*pr++;
        MEMORY_BASIC_INFORMATION mbi;
        unsigned long protect=0;
        if(VirtualQuery((LPCVOID)source,&mbi,sizeof(mbi))==sizeof(mbi)) protect=(unsigned long)mbi.Protect;
        append_hex(&p,end,protect);
        const char *rt=" ret=";
        while(*rt&&p<end)*p++=*rt++;
        append_hex(&p,end,g_ret_into_formatter);
        const char *cl=" caller=";
        while(*cl&&p<end)*p++=*cl++;
        append_hex(&p,end,g_ret_formatter_caller);
        *p++='\r';*p++='\n';*p=0;
        log_line(msg);
        return;
    }
}
static int build_norm_index(void) {
    if(norm_table) { HeapFree(GetProcessHeap(),0,norm_table); norm_table=NULL; }
    if(norm_pool) { HeapFree(GetProcessHeap(),0,norm_pool); norm_pool=NULL; }
    if(!table) return 0;
    uint32_t capacity=table_mask+1u, used=0, need=0;
    WCHAR buf[256];
    for(uint32_t i=0;i<capacity;++i) {
        if(!table[i].key) continue;
        if(normalize_key(table[i].key,buf,256)) need+=(DWORD)(lstrlenW(buf)+1)*2u;
    }
    if(!need) return 0;
    norm_pool=HeapAlloc(GetProcessHeap(),0,need);
    norm_table=HeapAlloc(GetProcessHeap(),HEAP_ZERO_MEMORY,capacity*sizeof(Entry));
    if(!norm_pool||!norm_table) {
        if(norm_pool) { HeapFree(GetProcessHeap(),0,norm_pool); norm_pool=NULL; }
        if(norm_table) { HeapFree(GetProcessHeap(),0,norm_table); norm_table=NULL; }
        return 0;
    }
    norm_mask=table_mask;
    for(uint32_t i=0;i<capacity;++i) {
        if(!table[i].key) continue;
        if(!normalize_key(table[i].key,buf,256)) continue;
        uint32_t hash=hash_string(buf),slot=hash&norm_mask;
        int duplicate=0;
        while(norm_table[slot].key) {
            if(norm_table[slot].hash==hash && equal_string(norm_table[slot].key,buf)) {
                if(!norm_table[slot].value || !equal_string(norm_table[slot].value,table[i].value))
                    norm_table[slot].value=NULL;
                duplicate=1;
                break;
            }
            slot=(slot+1)&norm_mask;
        }
        if(duplicate) continue;
        WCHAR *copy=(WCHAR *)(norm_pool+used);
        int n=lstrlenW(buf);
        for(int k=0;k<=n;++k) copy[k]=buf[k];
        used+=(DWORD)(n+1)*2u;
        norm_table[slot].key=copy;norm_table[slot].value=table[i].value;norm_table[slot].hash=hash;
    }
    return 1;
}
/* ---------- 源串地址（RVA）覆盖 ---------- */
static void resolve_image(void) {
    BYTE *base=(BYTE *)GetModuleHandleA(NULL);
    image_base=base; image_size=0;
    if(!base) return;
    IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER *)base;
    if(dos->e_magic!=IMAGE_DOS_SIGNATURE) return;
    IMAGE_NT_HEADERS *nt=(IMAGE_NT_HEADERS *)(base+dos->e_lfanew);
    if(nt->Signature!=IMAGE_NT_SIGNATURE) return;
    image_size=nt->OptionalHeader.SizeOfImage;
}
/* 主模块镜像解析失败时退回旧行为（一律当作镜像内），绝不因此停掉翻译。 */
static int in_image(const WCHAR *s) {
    if(!image_base || !image_size) return 1;
    ULONG_PTR off=(ULONG_PTR)s-(ULONG_PTR)image_base;
    return off<image_size;
}
/* 归一化索引只为地图标签这类「大小写/字距变体」而设：输入框里用户敲的
   "guard" 不属于这一类，把它翻成「近卫」会让部队一览的英文检索永远对不上。
   放行条件 = 源串在主模块镜像内（引擎自己的字面量）/ 含空白（字距拆开的地图
   标签）/ 全大写 ASCII（大写标签）。三条都不满足就不走归一化，原样返回。 */
static int norm_allowed(const WCHAR *s) {
    int has_space=0,letters=0,lower=0;
    for(const WCHAR *p=s;*p;++p) {
        WCHAR c=*p;
        if(c==0x20||c==0x09||c==0x0a||c==0x0d||c==0xa0||c==0x3000) { has_space=1; continue; }
        if(c>='A'&&c<='Z') { ++letters; continue; }
        if(c>='a'&&c<='z') { ++letters; ++lower; continue; }
    }
    if(has_space) return 1;
    if(letters && !lower) return 1;
    return in_image(s);
}
static int parse_addr_key(const WCHAR *key,uint32_t *rva) {
    if(key[0]!='@'||key[1]!='@'||key[2]!='R'||key[3]!='V'||key[4]!='A'||key[5]!=':') return 0;
    uint32_t v=0;int n=0;
    for(const WCHAR *p=key+6;*p;++p,++n) {
        WCHAR c=*p;uint32_t d;
        if(c>='0'&&c<='9') d=(uint32_t)(c-'0');
        else if(c>='A'&&c<='F') d=(uint32_t)(c-'A'+10);
        else if(c>='a'&&c<='f') d=(uint32_t)(c-'a'+10);
        else return 0;
        if(n>=8) return 0;
        v=(v<<4)|d;
    }
    if(!n) return 0;
    *rva=v;
    return 1;
}
static int addr_push(uint32_t rva,const WCHAR *value) {
    if(addr_count==addr_cap) {
        uint32_t cap=addr_cap?addr_cap*2u:32u;
        AddrEntry *grown=addr_table
            ? (AddrEntry *)HeapReAlloc(GetProcessHeap(),0,addr_table,(SIZE_T)cap*sizeof(AddrEntry))
            : (AddrEntry *)HeapAlloc(GetProcessHeap(),0,(SIZE_T)cap*sizeof(AddrEntry));
        if(!grown) return 0;
        addr_table=grown;addr_cap=cap;
    }
    uint32_t i=addr_count++;
    while(i>0&&addr_table[i-1].rva>rva) { addr_table[i]=addr_table[i-1]; --i; }
    addr_table[i].rva=rva;addr_table[i].value=value;
    return 1;
}
static const WCHAR *addr_lookup(uint32_t rva) {
    uint32_t lo=0,hi=addr_count;
    while(lo<hi) {
        uint32_t mid=lo+((hi-lo)>>1);
        if(addr_table[mid].rva==rva) return addr_table[mid].value;
        if(addr_table[mid].rva<rva) lo=mid+1u; else hi=mid;
    }
    return NULL;
}
static int parse_skip_key(const WCHAR *key,uint32_t *rva) {
    if(key[0]!='@'||key[1]!='@'||key[2]!='S'||key[3]!='K'||key[4]!='I'||key[5]!='P'||key[6]!=':') return 0;
    uint32_t v=0;int n=0;
    for(const WCHAR *p=key+7;*p;++p,++n) {
        WCHAR c=*p;uint32_t d;
        if(c>='0'&&c<='9') d=(uint32_t)(c-'0');
        else if(c>='A'&&c<='F') d=(uint32_t)(c-'A'+10);
        else if(c>='a'&&c<='f') d=(uint32_t)(c-'a'+10);
        else return 0;
        if(n>=8) return 0;
        v=(v<<4)|d;
    }
    if(!n) return 0;
    *rva=v;
    return 1;
}
static int skip_lookup(uint32_t rva) {
    uint32_t lo=0,hi=skip_count;
    while(lo<hi) {
        uint32_t mid=lo+((hi-lo)>>1);
        if(skip_table[mid]==rva) return 1;
        if(skip_table[mid]<rva) lo=mid+1u; else hi=mid;
    }
    return 0;
}
static int skip_push(uint32_t rva) {
    if(skip_lookup(rva)) return 1;
    if(skip_count==skip_cap) {
        uint32_t cap=skip_cap?skip_cap*2u:16u;
        uint32_t *grown=skip_table
            ? (uint32_t *)HeapReAlloc(GetProcessHeap(),0,skip_table,(SIZE_T)cap*sizeof(uint32_t))
            : (uint32_t *)HeapAlloc(GetProcessHeap(),0,(SIZE_T)cap*sizeof(uint32_t));
        if(!grown) return 0;
        skip_table=grown;skip_cap=cap;
    }
    uint32_t i=skip_count++;
    while(i>0&&skip_table[i-1]>rva) { skip_table[i]=skip_table[i-1]; --i; }
    skip_table[i]=rva;
    return 1;
}
static void log_addr_hit(uint32_t rva,const WCHAR *value) {
    if(InterlockedIncrement(&addr_logged)>40) return;
    char msg[96],*p=msg,*end=msg+sizeof(msg)-3;
    const char *head="ADDR override: rva=";
    while(*head&&p<end)*p++=*head++;
    append_hex(&p,end,(unsigned long)rva);
    const char *tail=" out=";
    while(*tail&&p<end)*p++=*tail++;
    int zh=0;
    if(value) for(const WCHAR *s=value;*s;++s) if(*s>=0x2e80){zh=1;break;}
    *p++=zh?'z':'e';*p++=zh?'h':'n';
    *p++='\r';*p++='\n';*p=0;
    log_line(msg);
}
static void log_norm_block(const WCHAR *source) {
    if(InterlockedIncrement(&blocked_logged)>120) return;
    char msg[160],*p=msg,*end=msg+sizeof(msg)-3;
    const char *head="NORM blocked (kept verbatim): src=\"";
    while(*head&&p<end)*p++=*head++;
    for(const WCHAR *s=source;*s&&p<end;++s) *p++=(*s>=32&&*s<127)?(char)*s:'?';
    *p++='"';*p++='\r';*p++='\n';*p=0;
    log_line(msg);
}
/* ---------- 诊断用 trace（默认关闭，只在 mod\\logs\\trace.on 存在时开启） ----------
   用途：判断某个窗口「根本没向引擎请求文本」（=列表数据为空，与汉化无关）还是
   「请求了却没画出来」（=绘制/字体层）。开启后记录去重后的源串：它在主模块镜像
   内就记 RVA（可直接对回字面量），堆上的运行期串记 heap；同时记命中方式与输出
   语言。上限 100000 条（去重后计数），避免日志失控；trace.on 不存在时一次文件探测即永久关闭。 */
static LONG trace_state=-1;         /* -1 未探测，0 关闭，1 开启 */
static LONG passthru_state=-1;      /* 同上：logs\passthru.on 存在时一律返回原文 */
static LONG trace_lines;
static uint32_t *trace_seen;
static const uint32_t trace_seen_mask=262143u;   /* 2^18-1：容量必须远大于条数上限，否则线性探测会填满死循环 */
static int trace_enabled(void) {
    if(trace_state>=0) return (int)trace_state;
    WCHAR path[MAX_PATH];
    path_for(path,L"\\logs\\trace.on");
    HANDLE h=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    int on=0;
    if(h!=INVALID_HANDLE_VALUE) { CloseHandle(h); on=1; }
    if(on) {
        trace_seen=(uint32_t *)HeapAlloc(GetProcessHeap(),HEAP_ZERO_MEMORY,(trace_seen_mask+1u)*sizeof(uint32_t));
        if(!trace_seen) on=0;
        else log_line("TRACE enabled: mod\\logs\\trace.on found; cap 100000 distinct lookups\r\n");
    }
    trace_state=on;
    return on;
}
/* 诊断开关：mod\logs\passthru.on 存在时 translate() 一律返回原文（界面等于英文版），
   用来 A/B 判断某个窗口的异常到底来自翻译本身，还是字体/布局/引擎。
   与 trace 一样只探测一次，不分配内存。 */
static int passthru_on(void) {
    if(passthru_state>=0) return (int)passthru_state;
    WCHAR path[MAX_PATH];
    path_for(path,L"\\logs\\passthru.on");
    HANDLE h=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    int on=0;
    if(h!=INVALID_HANDLE_VALUE) { CloseHandle(h); on=1; }
    if(on) log_line("PASSTHRU enabled: mod\\logs\\passthru.on found; all lookups return the original text\r\n");
    passthru_state=on;
    return on;
}
static void trace_lookup(const WCHAR *source,const WCHAR *out,const char *how) {
    if(!trace_enabled()) return;
    uint32_t h=hash_string(source)|1u;
    uint32_t slot=h&trace_seen_mask;
    while(trace_seen[slot] && trace_seen[slot]!=h) slot=(slot+1u)&trace_seen_mask;
    if(trace_seen[slot]==h) return;
    trace_seen[slot]=h;
    LONG tn=InterlockedIncrement(&trace_lines);
    if(tn==100001L) log_line("TRACE cap reached (100000 distinct lookups); further lookups are not logged\r\n");
    if(tn>100000L) return;
    char msg[200],*p=msg,*end=msg+sizeof(msg)-3;
    const char *head="TRACE ";
    while(*head&&p<end)*p++=*head++;
    ULONG_PTR off=(ULONG_PTR)(image_base?(ULONG_PTR)source-(ULONG_PTR)image_base:0);
    if(image_base&&image_size&&off<image_size) {
        const char *k="rva=";while(*k&&p<end)*p++=*k++;
        append_hex(&p,end,(unsigned long)off);
    } else {
        const char *k="heap";while(*k&&p<end)*p++=*k++;
    }
    *p++=' ';
    while(*how&&p<end)*p++=*how++;
    *p++=' ';
    int zh=0;
    if(out) for(const WCHAR *s=out;*s;++s) if(*s>=0x2e80){zh=1;break;}
    *p++=zh?'z':'e';*p++=zh?'h':'n';
    const char *q=" \"";while(*q&&p<end)*p++=*q++;
    int n=0;
    for(const WCHAR *s=source;*s&&n<44&&p<end;++s,++n) *p++=(*s>=32&&*s<127)?(char)*s:'?';
    *p++='"';*p++='\r';*p++='\n';*p=0;
    log_line(msg);
}
/* ---------- 组合行（引擎先把 %d 拼进串里，再来查表） ----------
   trace 里能直接看到运行期串 "Assigned Air Directives 31 (15) / MAX 32"、
   "Auto  ( mission 169 / escort 224 )"：数字已经格式化进字符串，整串再送进来，
   所以任何带 %d 的词典键都不可能精确命中。这里按模式取数、用中文模板重排。 */
typedef struct {const WCHAR *pat;const WCHAR *zh;} FmtRule;
static const FmtRule fmt_rules[]={
    {L"Assigned Air Directives %d (%d) / MAX %d",L"已分配空中指令 %d (%d) / 上限 %d"},
    {L"Auto ( mission %d / escort %d )",L"自动（任务 %d / 护航 %d）"},
};
static int fmt_match(const WCHAR *s,const WCHAR *p,int *vals,int maxv,int *nvals) {
    int n=0;
    while(*p) {
        if(p[0]=='%'&&p[1]=='d') {
            int v=0,neg=0,digits=0;
            p+=2;
            while(*s==' ') ++s;
            if(*s=='-') { neg=1;++s; } else if(*s=='+') ++s;
            while(*s>='0'&&*s<='9') { v=v*10+(*s-'0'); ++s; ++digits; }
            if(!digits||n>=maxv) return 0;
            vals[n++]=neg?-v:v;
            continue;
        }
        if(*p==' ') {                     /* 模板里一个空格 = 源串里一个或多个 */
            if(*s!=' ') return 0;
            while(*s==' ') ++s;
            while(*p==' ') ++p;
            continue;
        }
        if(*s!=*p) return 0;
        ++s;++p;
    }
    if(*s) return 0;
    *nvals=n;
    return 1;
}
static const WCHAR *fmt_apply(const WCHAR *zh,const int *vals,int nvals) {
    static WCHAR ring[4][160];
    static LONG slot;
    WCHAR *out=ring[(unsigned)InterlockedIncrement(&slot)&3u];
    WCHAR *o=out,*end=out+158;
    const WCHAR *p=zh;
    int i=0;
    while(*p&&o<end) {
        if(p[0]=='%'&&p[1]=='d') {
            WCHAR tmp[12]; int len=0;
            int v=(i<nvals)?vals[i++]:0;
            unsigned a;
            if(v<0) { *o++='-'; a=(unsigned)(-(v+1))+1u; } else a=(unsigned)v;
            do { tmp[len++]=(WCHAR)('0'+(a%10u)); a/=10u; } while(a&&len<11);
            while(len) *o++=tmp[--len];
            p+=2;
            continue;
        }
        *o++=*p++;
    }
    *o=0;
    return out;
}
static const WCHAR *fmt_translate(const WCHAR *source) {
    for(unsigned r=0;r<sizeof(fmt_rules)/sizeof(fmt_rules[0]);++r) {
        int vals[4],n=0;
        if(fmt_match(source,fmt_rules[r].pat,vals,4,&n)) return fmt_apply(fmt_rules[r].zh,vals,n);
    }
    return NULL;
}
static const WCHAR *translate(const WCHAR *source) {
    if(!source || !table) return source;
    if(passthru_on()) return source;
    if(skip_count && image_base && image_size) {
        ULONG_PTR soff=(ULONG_PTR)source-(ULONG_PTR)image_base;
        if(soff<image_size && skip_lookup((uint32_t)soff)) { trace_lookup(source,source,"skip"); return source; }
    }
    if(addr_count && image_base && image_size) {
        ULONG_PTR off=(ULONG_PTR)source-(ULONG_PTR)image_base;
        if(off<image_size) {
            const WCHAR *hit=addr_lookup((uint32_t)off);
            if(hit) { log_addr_hit((uint32_t)off,hit); trace_lookup(source,hit,"addr"); return hit; }
        }
    }
    WCHAR norm[256];
    int have_norm=normalize_key(source,norm,256);
    uint32_t hash=hash_string(source),i=hash&table_mask;
    const WCHAR *value=NULL;
    int exact_hit=0;
    while(table[i].key) {
        if(table[i].hash==hash && equal_string(source,table[i].key)) { value=table[i].value; exact_hit=1; break; }
        i=(i+1)&table_mask;
    }
    if(!value && norm_table && have_norm) {
        if(norm_allowed(source)) value=norm_lookup(norm);
        else {
            const WCHAR *would=norm_lookup(norm);
            if(would && !equal_string(would,source)) log_norm_block(source);
        }
    }
    /* 组合行：数字已拼进串里，词典精确键命中不了，按模式重排。 */
    if(!value) {
        const WCHAR *built=fmt_translate(source);
        if(built) { trace_lookup(source,built,"fmt"); return built; }
    }
    /* 探针：命中与未命中都记录源串、命中方式与来源栈。 */
    if(have_norm) probe_map_label(norm,source,exact_hit,value);
    trace_lookup(source,value?value:source,value?(exact_hit?"exact":"norm"):"none");
    if(value) {
        if(InterlockedIncrement(&hits)==1)log_line("first translation lookup succeeded\r\n");
        return value;
    }
    return source;
}
static const WCHAR *__attribute__((thiscall)) lookup_hook(void *self,const WCHAR *source,int flag) {
    /* 记录「谁调用了格式化函数」：EBP 链只走一层，不依赖游戏镜像的 unwind 信息。 */
    void *ebp=__builtin_frame_address(0);
    if(ebp) {
        unsigned long *frame=(unsigned long *)ebp;
        if(!g_ret_into_formatter) g_ret_into_formatter=frame[1];
        void *caller=(void *)frame[0];
        if(!g_ret_formatter_caller && caller) g_ret_formatter_caller=((unsigned long *)caller)[1];
    }
    return translate(original_lookup(self,source,flag));
}
static int expected_call(BYTE *site,BYTE *target) {
    return site[0]==0xe8 && site+5+(int32_t)u32(site+1)==target;
}
static int text_section(BYTE *base,BYTE **text,DWORD *size);
static int patch_sites(BYTE **sites,int count,BYTE *target,BYTE *replacement);

/* The name table is generated offline from scenario Units/OBs and all four
   language dictionaries. A missing or invalid table only disables crests. */
static int load_crest_map(void) {
    WCHAR path[MAX_PATH]; DWORD read=0;
    path_for(path,L"\\payload\\crest_names.bin");
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if(file==INVALID_HANDLE_VALUE) { log_line("crest map: unavailable; crest hook disabled\r\n"); return 0; }
    DWORD size=GetFileSize(file,NULL);
    if(size<12 || size>16u*1024u*1024u) { CloseHandle(file); log_line("crest map: invalid size; crest hook disabled\r\n"); return 0; }
    BYTE *data=HeapAlloc(GetProcessHeap(),0,size);
    if(!data) { CloseHandle(file); return 0; }
    int ok=ReadFile(file,data,size,&read,NULL)&&read==size;
    CloseHandle(file);
    if(!ok || data[0]!='W'||data[1]!='2'||data[2]!='C'||data[3]!='N'||data[4]!='C'||data[5]!='R'||data[6]!='1'||data[7]!=0) goto bad;
    crest_count=u32(data+8);
    if(!crest_count || crest_count>50000u) goto bad;
    uint32_t capacity=1; while(capacity<crest_count*2u) capacity<<=1;
    crest_mask=capacity-1;
    crest_table=HeapAlloc(GetProcessHeap(),HEAP_ZERO_MEMORY,capacity*sizeof(Entry));
    BYTE *pool2=HeapAlloc(GetProcessHeap(),0,size+crest_count*4u);
    if(!crest_table || !pool2) { if(pool2)HeapFree(GetProcessHeap(),0,pool2); goto bad; }
    DWORD offset=12,used=0;
    for(uint32_t i=0;i<crest_count;++i) {
        if(offset>size-8) { HeapFree(GetProcessHeap(),0,pool2); goto bad; }
        uint32_t a=u32(data+offset),b=u32(data+offset+4); offset+=8;
        if(!a||!b||a>512u||b>512u||(a+b)*2u>size-offset) { HeapFree(GetProcessHeap(),0,pool2); goto bad; }
        WCHAR *key=(WCHAR *)(pool2+used); copy_bytes(key,data+offset,a*2u); key[a]=0; used+=(a+1)*2u; offset+=a*2u;
        WCHAR *value=(WCHAR *)(pool2+used); copy_bytes(value,data+offset,b*2u); value[b]=0; used+=(b+1)*2u; offset+=b*2u;
        uint32_t hash=hash_string(key),index=hash&crest_mask;
        while(crest_table[index].key) index=(index+1)&crest_mask;
        crest_table[index].key=key; crest_table[index].value=value; crest_table[index].hash=hash;
    }
    if(offset!=size) { HeapFree(GetProcessHeap(),0,pool2); goto bad; }
    HeapFree(GetProcessHeap(),0,data);
    return 1;
bad:
    if(crest_table) { HeapFree(GetProcessHeap(),0,crest_table); crest_table=NULL; }
    crest_count=0; HeapFree(GetProcessHeap(),0,data);
    log_line("crest map: invalid; crest hook disabled\r\n");
    return 0;
}

static const WCHAR *crest_lookup(const WCHAR *stem) {
    if(!crest_table || !stem) return NULL;
    uint32_t hash=hash_string(stem),index=hash&crest_mask;
    while(crest_table[index].key) {
        if(crest_table[index].hash==hash && equal_string(crest_table[index].key,stem)) return crest_table[index].value;
        index=(index+1)&crest_mask;
    }
    return NULL;
}

static const WCHAR *restore_crest(const WCHAR *path,WCHAR *buf,int cap) {
    static const WCHAR prefix[]=L"//Sym//";
    if(!path || !crest_table) return path;
    for(int i=0;i<7;++i) if(!path[i] || path[i]!=prefix[i]) return path;
    int len=lstrlenW(path);
    if(len<12 || len>=cap) return path;
    int start=7;
    while(start<len && path[start]!='/') ++start;
    if(start==7 || start>=len-5) return path;
    while(start<len && path[start]=='/') ++start;
    int end=len-4;
    if(end<=start) return path;
    WCHAR stem[512]; int n=end-start;
    if(n<=0 || n>=512) return path;
    for(int i=0;i<n;++i) stem[i]=path[start+i];
    stem[n]=0;
    const WCHAR *english=crest_lookup(stem);
    if(!english) return path;
    int english_len=lstrlenW(english);
    if(start+english_len+(len-end)>=cap) return path;
    int out=0;
    for(int i=0;i<start;++i) buf[out++]=path[i];
    for(int i=0;english[i];++i) buf[out++]=english[i];
    for(int i=len-4;i<len;++i) buf[out++]=path[i];
    buf[out]=0;
    InterlockedIncrement(&crest_fixes);
    return buf;
}

static int __cdecl crest_thunk(const WCHAR *path,void *surface,unsigned color,int a,int b,int c) {
    WCHAR buf[512];
    return original_crest(restore_crest(path,buf,512),surface,color,a,b,c);
}

/* This RVA is the uniquely verified caller of the loader for the two //Sym//
   format strings. Patch only after checking its call target and .text bounds. */
static int install_crest(BYTE *base) {
    BYTE *text=NULL; DWORD size=0;
    if(!text_section(base,&text,&size)) return 0;
    BYTE *site=base+0x3ef56e, *target=base+0x44dc30;
    if(site<text || site+5>text+size || !expected_call(site,target)) {
        log_line("crest hook: verified call site mismatch; hook disabled\r\n"); return 0;
    }
    BYTE *one[1]={site};
    original_crest=(CrestLoad)target;
    if(!patch_sites(one,1,target,(BYTE *)crest_thunk)) {
        log_line("crest hook: single-site patch rejected\r\n"); return 0;
    }
    log_line("READY: single crest call site hooked\r\n");
    return 1;
}

static DWORD WINAPI crest_worker(void *unused) {
    (void)unused;
    if(load_crest_map()) install_crest((BYTE *)GetModuleHandleW(NULL));
    return 0;
}

/* ---------- PE 段定位 ---------- */
static int text_section(BYTE *base,BYTE **text,DWORD *size) {
    IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER*)base;
    if(dos->e_magic!=IMAGE_DOS_SIGNATURE) return 0;
    IMAGE_NT_HEADERS *nt=(IMAGE_NT_HEADERS*)(base+dos->e_lfanew);
    if(nt->Signature!=IMAGE_NT_SIGNATURE) return 0;
    if(nt->FileHeader.Machine!=IMAGE_FILE_MACHINE_I386) return 0;
    IMAGE_SECTION_HEADER *sec=IMAGE_FIRST_SECTION(nt);
    for(int i=0;i<nt->FileHeader.NumberOfSections;++i) {
        if(sec[i].Name[0]=='.'&&sec[i].Name[1]=='t'&&sec[i].Name[2]=='e'&&sec[i].Name[3]=='x'&&sec[i].Name[4]=='t') {
            DWORD vs=sec[i].Misc.VirtualSize;
            if(sec[i].SizeOfRawData>vs) vs=sec[i].SizeOfRawData;
            if(vs<64) return 0;
            *text=base+sec[i].VirtualAddress;
            *size=vs;
            return 1;
        }
    }
    return 0;
}

/* ---------- 特征码扫描 ---------- */
static BYTE *find_signature(BYTE *text,DWORD size) {
    DWORD len=sizeof(lookup_sig);
    if(size<len) return NULL;
    DWORD last=size-len;
    for(DWORD i=0;i<=last;++i) {
        if(text[i]!=lookup_sig[0]) continue;
        DWORD j=1;
        while(j<len && text[i+j]==lookup_sig[j]) ++j;
        if(j==len) return text+i;
    }
    return NULL;
}

static int count_calls(BYTE *text,DWORD size,BYTE *target,BYTE **sites,int max) {
    int found=0;
    for(DWORD i=0;i+5<=size;++i) {
        if(text[i]!=0xe8) continue;
        int32_t rel=(int32_t)u32(text+i+1);
        if(text+i+5+rel!=target) continue;
        if(found<max) sites[found]=text+i;
        ++found;
    }
    return found;
}

static char *append_uint(char *p,unsigned long v) {
    char tmp[16];int n=0;
    if(!v) { *p++='0'; return p; }
    while(v && n<16) { tmp[n++]=(char)('0'+(v%10)); v/=10; }
    while(n) *p++=tmp[--n];
    return p;
}

/* ---------- 改写调用点（挂起其它线程；任一校验失败即整体放弃） ---------- */
static int patch_sites(BYTE **sites,int count,BYTE *target,BYTE *replacement) {
    for(int i=0;i<count;++i) if(!expected_call(sites[i],target)) return 0;
    HANDLE handles[256];DWORD held=0,suspended=0;
    HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);
    if(snap==INVALID_HANDLE_VALUE) return 0;
    THREADENTRY32 te;te.dwSize=sizeof(te);
    int more=Thread32First(snap,&te);
    DWORD pid=GetCurrentProcessId(),tid=GetCurrentThreadId();
    while(more) {
        if(te.th32OwnerProcessID==pid && te.th32ThreadID!=tid) {
            if(held==256) {more=0;break;}
            HANDLE t=OpenThread(THREAD_SUSPEND_RESUME,FALSE,te.th32ThreadID);
            if(!t) {more=0;break;}
            handles[held++]=t;
        }
        more=Thread32Next(snap,&te);
    }
    CloseHandle(snap);
    for(;suspended<held;++suspended) if(SuspendThread(handles[suspended])==(DWORD)-1) break;
    int ok=(suspended==held);
    int done=0;
    if(ok) {
        for(int i=0;i<count;++i) {
            DWORD old;
            if(!VirtualProtect(sites[i],5,PAGE_EXECUTE_READWRITE,&old)) {ok=0;break;}
            if(!expected_call(sites[i],target)) {ok=0;DWORD ignored;VirtualProtect(sites[i],5,old,&ignored);break;}
            int32_t delta=(int32_t)(replacement-(sites[i]+5));
            copy_bytes(sites[i]+1,&delta,4);
            FlushInstructionCache(GetCurrentProcess(),sites[i],5);
            DWORD ignored2;VirtualProtect(sites[i],5,old,&ignored2);
            ++done;
        }
    }
    while(suspended) ResumeThread(handles[--suspended]);
    for(DWORD i=0;i<held;++i) CloseHandle(handles[i]);
    return ok && done==count;
}

/* 纯逻辑版本：可在离线测试里对合成 .text 直接调用 */
static int install_at(BYTE *text,DWORD size) {
    for(int attempt=0;attempt<=sig_tries;++attempt) {
        /* 同一段函数头可能在 .text 里出现多次（栈帧相同的其它函数）。
           取"被 E8 调用点引用最多"的候选，而不是盲取第一个命中。 */
        BYTE *target=NULL;
        BYTE *best_sites[16];
        int found=0;
        for(int k=0;k<16;++k) best_sites[k]=NULL;
        DWORD offset=0;
        while(offset+sizeof(lookup_sig)<=size) {
            BYTE *hit=find_signature(text+offset,size-offset);
            if(!hit) break;
            BYTE *sites[16];
            int n=count_calls(text,size,hit,sites,16);
            if(n>found) {
                found=n;
                target=hit;
                for(int k=0;k<16;++k) best_sites[k]=(k<n)?sites[k]:NULL;
            }
            offset=(DWORD)(hit-text)+1;
        }
        if(target&&found>0) {
            if(found>16) found=16;
            original_lookup=(Lookup)target;
            if(patch_sites(best_sites,found,target,(BYTE *)lookup_hook)) {
                char msg[128];char *p=msg;
                const char *head="READY: hooked ";
                while(*head) *p++=*head++;
                p=append_uint(p,(unsigned long)found);
                const char *mid=" call site(s); lookup at text+0x";
                while(*mid) *p++=*mid++;
                p=append_uint(p,(unsigned long)((DWORD)(target-text)));
                const char *end="\r\n";
                while(*end) *p++=*end++;
                *p=0;
                log_line(msg);
                return 1;
            }
            log_line("FAILED: call sites found but patch rejected\r\n");
            return 0;
        }
        if(attempt<sig_tries) Sleep(100);
    }
    log_line("FAILED: localization lookup not found in .text (build changed)\r\n");
    return 0;
}

static int install_calls(BYTE *base) {
    BYTE *text=NULL;DWORD size=0;
    if(!text_section(base,&text,&size)) {log_line("FAILED: PE .text not readable\r\n");return 0;}
    return install_at(text,size);
}

__declspec(dllexport) DWORD WINAPI Wite2CN_Initialize(void *unused) {
    (void)unused;
    if(InterlockedCompareExchange(&initialized,1,0))return 2;
    DWORD n=GetModuleFileNameW(own_module,root,MAX_PATH);
    if(n==0 || n>=MAX_PATH-40)return 0;
    while(n && root[n-1]!=L'\\')--n;
    if(!n)return 0;root[n-1]=0;
    resolve_image();
    if(!load_map()) {log_line("FAILED: translation package invalid\r\n");return 0;}
    BYTE *base=(BYTE *)GetModuleHandleW(NULL);
    if(!base || !install_calls(base)) return 0;
    /* The optional crest hook runs off the launcher's initialization path. */
    CreateThread(NULL,0,crest_worker,NULL,0,NULL);
    return 1;
}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID reserved) {
    (void)reserved;
    if(reason==DLL_PROCESS_ATTACH) {own_module=instance;DisableThreadLibraryCalls(instance);}
    return TRUE;
}

#ifdef W2CN_TEST
/* 离线测试：只操作合成的内存镜像，不加载、不启动任何游戏可执行文件。 */
static const WCHAR *__attribute__((thiscall)) fake_lookup(void *self,const WCHAR *s,int flag) {
    if(self!=(void *)(UINT_PTR)0x12345678 || flag!=7)ExitProcess(80);
    return s;
}
static void report(HANDLE out,const char *m) { DWORD wrote; WriteFile(out,m,(DWORD)lstrlenA(m),&wrote,NULL); }
int main(void) {
    own_module=GetModuleHandleW(NULL);
    resolve_image();
    DWORD n=GetModuleFileNameW(own_module,root,MAX_PATH);
    while(n && root[n-1]!=L'\\')--n;
    if(!n)return 81;
    root[n-1]=0;
    sig_tries=0;
    HANDLE out=GetStdHandle(STD_OUTPUT_HANDLE);
    static const WCHAR sample[]=L"Game Options";
    DWORD image_size=0x100000;
    BYTE *image=(BYTE *)VirtualAlloc(NULL,image_size,MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);
    if(!image)return 85;
    BYTE *target=image+0x80000;
    copy_bytes(target,lookup_sig,sizeof(lookup_sig));
    const BYTE body[]={0x81,0xc4,0xfc,0x0a,0,0,0x8b,0x44,0x24,0x04,0xc2,0x08,0x00};
    copy_bytes(target+sizeof(lookup_sig),body,sizeof(body));
    DWORD offsets[]={0x10000,0x20000};
    for(int i=0;i<2;++i) {
        BYTE *start=image+offsets[i];
        start[0]=0x6a;start[1]=0x07;                       /* push 7            */
        start[2]=0x68;                                      /* push L"Game..."   */
        uint32_t text=(uint32_t)(UINT_PTR)sample;copy_bytes(start+3,&text,4);
        start[7]=0xb9;                                      /* mov ecx,this      */
        uint32_t object=0x12345678;copy_bytes(start+8,&object,4);
        BYTE *site=start+12;                                /* call lookup; ret  */
        site[0]=0xe8;
        int32_t rel=(int32_t)(target-(site+5));
        copy_bytes(site+1,&rel,4);
        site[5]=0xc3;
    }
    /* 诱饵：在真函数之前放一份同样的函数头，但没有任何调用点指向它 */
    BYTE *decoy=image+0x1000;
    copy_bytes(decoy,lookup_sig,sizeof(lookup_sig));
    BYTE *copy2=(BYTE *)VirtualAlloc(NULL,image_size,MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);
    if(!copy2)return 86;
    copy_bytes(copy2,image,image_size);
    copy2[0x80000]=0x90;
    if(install_at(copy2,image_size)) {report(out,"FAIL: accepted image without signature\r\n");return 87;}
    VirtualFree(copy2,0,MEM_RELEASE);
    if(!install_at(image,image_size)) {report(out,"FAIL: signature present but not hooked\r\n");return 88;}
    typedef const WCHAR *(*Thunk)(void);
    for(int round=0;round<5000;++round) for(int j=0;j<2;++j) {
        Thunk call=(Thunk)(image+offsets[j]);
        const WCHAR *value=call();
        if(!value||!value[0]) {report(out,"FAIL: trampoline returned null\r\n");return 89;}
        if(!equal_string(value,sample)) {report(out,"FAIL: trampoline changed text\r\n");return 91;}
    }
    static const WCHAR localized[]=L"1st 装甲师";
    static const WCHAR original[]=L"1st Panzer Division";
    static const WCHAR crest_path[]=L"//Sym//GE//1st 装甲师.tga";
    static const WCHAR non_crest[]=L"//Tiles//CLEAR//CLEAR_001.tga";
    static const WCHAR unknown_crest[]=L"//Sym//GE//unknown.tga";
    Entry test_entries[2]={{0}};
    uint32_t test_hash=hash_string(localized),test_slot=test_hash&1u;
    test_entries[test_slot].key=localized;test_entries[test_slot].value=original;test_entries[test_slot].hash=test_hash;
    crest_table=test_entries;crest_mask=1;
    WCHAR rewritten[512];
    const WCHAR *restored=restore_crest(crest_path,rewritten,512);
    if(!equal_string(restored,L"//Sym//GE//1st Panzer Division.tga")) {report(out,"FAIL: crest path was not restored\r\n");return 93;}
    if(restore_crest(non_crest,rewritten,512)!=non_crest) {report(out,"FAIL: non-crest path was changed\r\n");return 94;}
    restored=restore_crest(unknown_crest,rewritten,512);
    if(!equal_string(restored,unknown_crest)) {report(out,"FAIL: unknown crest path was changed\r\n");return 95;}
    /* 地图标签键归一化：精确表未命中时，大小写/空白变体必须接回同一译文；
       无关文本一个字都不能改。 */
    static const WCHAR spaced_city[]=L"M o s c o w";
    static const WCHAR upper_city[]=L"MOSCOW";
    static const WCHAR padded_city[]=L"  M O S C O W  ";
    static const WCHAR city_zh[]=L"莫斯科";
    static const WCHAR unrelated[]=L"Unrelated Label";
    Entry exact[4]={{0}};
    uint32_t exact_hash=hash_string(spaced_city),exact_slot=exact_hash&3u;
    exact[exact_slot].key=spaced_city;exact[exact_slot].value=city_zh;exact[exact_slot].hash=exact_hash;
    table=exact;table_mask=3;entry_count=1;
    if(!build_norm_index()) {report(out,"FAIL: normalized index was not built\r\n");return 96;}
    if(translate(upper_city)!=city_zh) {report(out,"FAIL: uppercase map label was not normalized\r\n");return 97;}
    if(translate(padded_city)!=city_zh) {report(out,"FAIL: padded map label was not normalized\r\n");return 98;}
    if(translate(unrelated)!=unrelated) {report(out,"FAIL: unrelated text was rewritten by the normalized index\r\n");return 99;}
    /* 地址覆盖：同一条字面量在引擎里可能有两种角色。用两个不同位置的同一个
       "CITY" 验证——登记过的地址返回该地址的译文，堆上的副本照旧走词典。 */
    static const WCHAR pin_city[]=L"CITY";
    static const WCHAR ui_city[]=L"城市";
    Entry pinned[4]={{0}};
    uint32_t pin_hash=hash_string(pin_city),pin_slot=pin_hash&3u;
    pinned[pin_slot].key=pin_city;pinned[pin_slot].value=pin_city;pinned[pin_slot].hash=pin_hash;
    table=pinned;table_mask=3;entry_count=1;
    uint32_t pin_rva=(uint32_t)((ULONG_PTR)pin_city-(ULONG_PTR)image_base);
    if(!addr_push(pin_rva,ui_city)) {report(out,"FAIL: address table allocation\r\n");return 100;}
    if(translate(pin_city)!=ui_city) {report(out,"FAIL: address override was not applied\r\n");return 101;}
    WCHAR *heap_city=(WCHAR *)HeapAlloc(GetProcessHeap(),0,8*sizeof(WCHAR));
    if(!heap_city)return 102;
    for(int k=0;k<5;++k) heap_city[k]=pin_city[k];
    if(translate(heap_city)!=pin_city) {report(out,"FAIL: heap copy of a pinned literal must use the dictionary\r\n");return 103;}
    HeapFree(GetProcessHeap(),0,heap_city);
    if(addr_table) HeapFree(GetProcessHeap(),0,addr_table);
    addr_table=NULL;addr_count=0;addr_cap=0;
    /* 地址跳过：美术路径片段（'-red' 拼进 //Gui//frame%s.tga）在登记地址必须原样
       返回；同一文本的堆副本仍按词典翻译（别处也许真是可译文字）。 */
    static const WCHAR art_frag[]=L"-red";
    static const WCHAR frag_zh[]=L"红";
    Entry frag_table[4]={{0}};
    uint32_t frag_hash=hash_string(art_frag),frag_slot=frag_hash&3u;
    frag_table[frag_slot].key=art_frag;frag_table[frag_slot].value=frag_zh;frag_table[frag_slot].hash=frag_hash;
    table=frag_table;table_mask=3;entry_count=1;
    uint32_t frag_rva=(uint32_t)((ULONG_PTR)art_frag-(ULONG_PTR)image_base);
    if(!skip_push(frag_rva)) {report(out,"FAIL: skip table allocation\r\n");return 108;}
    if(translate(art_frag)!=art_frag) {report(out,"FAIL: art path fragment was translated at its registered address\r\n");return 109;}
    WCHAR *heap_frag=(WCHAR *)HeapAlloc(GetProcessHeap(),0,8*sizeof(WCHAR));
    if(!heap_frag)return 110;
    for(int k=0;k<5;++k) heap_frag[k]=art_frag[k];
    if(translate(heap_frag)!=frag_zh) {report(out,"FAIL: heap copy of a skipped fragment must still be translated\r\n");return 111;}
    HeapFree(GetProcessHeap(),0,heap_frag);
    if(skip_count!=1) {report(out,"FAIL: skip table must hold exactly one entry\r\n");return 112;}
    if(skip_table) HeapFree(GetProcessHeap(),0,skip_table);
    skip_table=NULL;skip_count=0;skip_cap=0;
    /* 检索输入：小写、无空白、堆缓冲的英文必须原样返回，不能被归一化索引吃掉。 */
    static const WCHAR guard_key[]=L"Guard";
    static const WCHAR guard_zh[]=L"近卫";
    static const WCHAR typed_text[]=L"guard";
    Entry guard_table[4]={{0}};
    uint32_t guard_hash=hash_string(guard_key),guard_slot=guard_hash&3u;
    guard_table[guard_slot].key=guard_key;guard_table[guard_slot].value=guard_zh;guard_table[guard_slot].hash=guard_hash;
    table=guard_table;table_mask=3;entry_count=1;
    if(!build_norm_index()) {report(out,"FAIL: guard index was not built\r\n");return 104;}
    WCHAR *typed=(WCHAR *)HeapAlloc(GetProcessHeap(),0,8*sizeof(WCHAR));
    if(!typed)return 105;
    for(int k=0;k<6;++k) typed[k]=typed_text[k];
    if(translate(typed)!=typed) {report(out,"FAIL: typed lowercase text was translated by the normalized index\r\n");return 106;}
    if(translate(guard_key)!=guard_zh) {report(out,"FAIL: exact key stopped being translated\r\n");return 107;}
    HeapFree(GetProcessHeap(),0,typed);
    table=NULL;
    /* 组合行：数字先拼进串里，词典键永远命中不了，只能按模式重排。 */
    const WCHAR *fo=fmt_translate(L"Auto  ( mission 169 / escort 224 )");
    int got=0;
    if(fo) for(const WCHAR *s=fo;*s;++s) if(s[0]=='1'&&s[1]=='6'&&s[2]=='9') got=1;
    if(!fo||!got||fo[0]!=0x81EA) {report(out,"FAIL: combined Auto line was not rewritten with its numbers\r\n");return 113;}
    const WCHAR *fa=fmt_translate(L"Assigned Air Directives 31 (15) / MAX 32");
    got=0;
    if(fa) for(const WCHAR *s=fa;*s;++s) if(s[0]=='3'&&s[1]=='1') got=1;
    if(!fa||!got) {report(out,"FAIL: Assigned Air Directives line was not rewritten\r\n");return 114;}
    if(fmt_translate(L"Auto ( mission x / escort 1 )")) {report(out,"FAIL: malformed combined line matched\r\n");return 115;}
    if(install_at(image,image_size)) {report(out,"FAIL: double hook accepted\r\n");return 90;}
    if(decoy[0]!=lookup_sig[0]||decoy[9]!=lookup_sig[9]) {report(out,"FAIL: decoy signature was modified\r\n");return 92;}
    VirtualFree(image,0,MEM_RELEASE);
    report(out,"PASS: decoy skipped; 2 text call sites; 10000 thiscall round-trips; crest path restored; map-label variants normalized; unrelated paths unchanged\r\n");
    return 0;
}
#endif
