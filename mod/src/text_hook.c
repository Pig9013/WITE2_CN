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
static void log_line(const char *s) {
    WCHAR path[MAX_PATH];DWORD count;
#ifdef W2CN_TEST
    path_for(path,L"\\logs\\native.offline-test.log");
#else
    path_for(path,L"\\logs\\native.log");
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
static const WCHAR *translate(const WCHAR *source) {
    if(!source || !table) return source;
    WCHAR norm[256];
    int have_norm=normalize_key(source,norm,256);
    uint32_t hash=hash_string(source),i=hash&table_mask;
    const WCHAR *value=NULL;
    int exact_hit=0;
    while(table[i].key) {
        if(table[i].hash==hash && equal_string(source,table[i].key)) { value=table[i].value; exact_hit=1; break; }
        i=(i+1)&table_mask;
    }
    if(!value && norm_table && have_norm) value=norm_lookup(norm);
    /* 探针：命中与未命中都记录源串、命中方式与来源栈。 */
    if(have_norm) probe_map_label(norm,source,exact_hit,value);
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
    table=NULL;
    if(install_at(image,image_size)) {report(out,"FAIL: double hook accepted\r\n");return 90;}
    if(decoy[0]!=lookup_sig[0]||decoy[9]!=lookup_sig[9]) {report(out,"FAIL: decoy signature was modified\r\n");return 92;}
    VirtualFree(image,0,MEM_RELEASE);
    report(out,"PASS: decoy skipped; 2 text call sites; 10000 thiscall round-trips; crest path restored; map-label variants normalized; unrelated paths unchanged\r\n");
    return 0;
}
#endif
