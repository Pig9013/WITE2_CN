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
typedef struct { const WCHAR *key, *value; uint32_t hash; } Entry;
static HMODULE own_module;
static Entry *table;
static uint32_t table_mask, entry_count;
static BYTE *pool;
static Lookup original_lookup;
static LONG initialized;
static LONG hits;
static WCHAR root[MAX_PATH];
static int map_error;

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
    HeapFree(GetProcessHeap(),0,data);return 1;
bad:
    if(table) HeapFree(GetProcessHeap(),0,table);
    if(pool) HeapFree(GetProcessHeap(),0,pool);
    table=NULL;pool=NULL;HeapFree(GetProcessHeap(),0,data);return 0;
}
static const WCHAR *translate(const WCHAR *source) {
    if(!source || !table) return source;
    uint32_t hash=hash_string(source),i=hash&table_mask;
    while(table[i].key) {
        if(table[i].hash==hash && equal_string(source,table[i].key)) {
            if(InterlockedIncrement(&hits)==1)log_line("first translation lookup succeeded\r\n");
            return table[i].value;
        }
        i=(i+1)&table_mask;
    }
    return source;
}
static const WCHAR *__attribute__((thiscall)) lookup_hook(void *self,const WCHAR *source,int flag) {
    return translate(original_lookup(self,source,flag));
}
static int expected_call(BYTE *site,BYTE *target) {
    return site[0]==0xe8 && site+5+(int32_t)u32(site+1)==target;
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
static int patch_sites(BYTE **sites,int count,BYTE *target) {
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
            int32_t delta=(int32_t)((BYTE *)lookup_hook-(sites[i]+5));
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
            if(patch_sites(best_sites,found,target)) {
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
    if(install_at(image,image_size)) {report(out,"FAIL: double hook accepted\r\n");return 90;}
    if(decoy[0]!=lookup_sig[0]||decoy[9]!=lookup_sig[9]) {report(out,"FAIL: decoy signature was modified\r\n");return 92;}
    VirtualFree(image,0,MEM_RELEASE);
    report(out,"PASS: decoy skipped, 2 real call sites hooked, 10000 thiscall round-trips, rejects missing signature and double hook\r\n");
    return 0;
}
#endif
