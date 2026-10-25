/* WitE2 1.05.02: intercept only the two calls into the engine's own
   localization lookup. No string scanning, game-object writes or disk patches.
   This DLL must be loaded only in the private runtime by the companion launcher. */
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
static int install_calls(BYTE *base) {
    static const BYTE sig[]={0x8b,0x54,0x24,0x04,0x81,0xec,0xfc,0x0a,0x00,0x00};
    BYTE *target=base+0x456ef0,*a=base+0x43a36f,*b=base+0x43a861;
    for(int i=0;i<10;++i) if(target[i]!=sig[i]) return 0;
    if(!expected_call(a,target)||!expected_call(b,target)) return 0;
    original_lookup=(Lookup)target;
    /* Each patched location is one CALL instruction. Suspended instruction
       pointers can be at the CALL or its target, never inside its displacement.
       Resolve thread handles before suspension to avoid process-heap deadlocks. */
    HANDLE handles[256];DWORD count=0,suspended=0,pid=GetCurrentProcessId(),tid=GetCurrentThreadId();
    HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);
    if(snap==INVALID_HANDLE_VALUE)return 0;
    THREADENTRY32 te;te.dwSize=sizeof(te);int ok=Thread32First(snap,&te);
    while(ok) {
        if(te.th32OwnerProcessID==pid && te.th32ThreadID!=tid) {
            if(count==256) {ok=0;break;}
            HANDLE t=OpenThread(THREAD_SUSPEND_RESUME,FALSE,te.th32ThreadID);
            if(!t) {ok=0;break;}
            handles[count++]=t;
        }
        if(!Thread32Next(snap,&te)) {ok=1;break;}
    }
    CloseHandle(snap);
    if(ok)for(;suspended<count;++suspended)if(SuspendThread(handles[suspended])==(DWORD)-1){ok=0;break;}
    DWORD old;
    if(ok && expected_call(a,target) && expected_call(b,target) && VirtualProtect(base+0x43a000,0x1000,PAGE_EXECUTE_READWRITE,&old)) {
        int32_t da=(int32_t)((BYTE *)lookup_hook-(a+5)),db=(int32_t)((BYTE *)lookup_hook-(b+5));
        copy_bytes(a+1,&da,4);copy_bytes(b+1,&db,4);
        FlushInstructionCache(GetCurrentProcess(),base+0x43a000,0x1000);
        DWORD ignored;VirtualProtect(base+0x43a000,0x1000,old,&ignored);
        ok=1;
    } else ok=0;
    while(suspended)ResumeThread(handles[--suspended]);
    for(DWORD i=0;i<count;++i)CloseHandle(handles[i]);
    return ok;
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
    if(!base || !install_calls(base)) {log_line("FAILED: unsupported executable or call sites\r\n");return 0;}
    log_line("READY: native localization calls connected; no game data altered\r\n");return 1;
}
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID reserved) {
    (void)reserved;
    if(reason==DLL_PROCESS_ATTACH) {own_module=instance;DisableThreadLibraryCalls(instance);}
    return TRUE;
}

#ifdef W2CN_TEST
/* Standalone ABI/loader tests; this program does not launch the game. */
static const WCHAR *__attribute__((thiscall)) fake_lookup(void *self,const WCHAR *s,int flag) {
    if(self!=(void *)0x12345678 || flag!=7)ExitProcess(80);
    return s;
}
int main(void) {
    own_module=GetModuleHandleW(NULL);
    DWORD n=GetModuleFileNameW(own_module,root,MAX_PATH);while(n&&root[n-1]!=L'\\')--n;root[n-1]=0;
    if(!load_map()) {
        char message[1024];DWORD wrote;
        int len=WideCharToMultiByte(CP_UTF8,0,root,-1,message,1000,NULL,NULL);
        if(len>0)WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),message,len-1,&wrote,NULL);
        return 80+map_error;
    }
    original_lookup=fake_lookup;
    const WCHAR *s=L"__W2CN_UNKNOWN_9912__";
    Lookup hook=(Lookup)lookup_hook;
    for(int i=0;i<100000;++i) {
        if(hook((void *)0x12345678,s,7)!=s)return 82;
        const WCHAR *r=hook((void *)0x12345678,L"Game Options",7);
        if(equal_string(r,L"Game Options")||!r[0])return 83;
        if(hook((void *)0x12345678,NULL,7)!=NULL)return 84;
    }
    /* Exercise the actual two-CALL patcher against a synthetic engine image.
       This checks x86 relative displacement, stack cleanup, return values and
       mismatch rejection, while never running a game executable. */
    BYTE *image=VirtualAlloc(NULL,0x460000,MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);
    if(!image)return 85;
    BYTE *target=image+0x456ef0;
    const BYTE fake[]={0x8b,0x54,0x24,0x04,0x81,0xec,0xfc,0x0a,0,0,0x81,0xc4,0xfc,0x0a,0,0,0x8b,0x44,0x24,0x04,0xc2,0x08,0x00};
    copy_bytes(target,fake,sizeof(fake));
    DWORD offsets[]={0x43a36f,0x43a861};
    for(int i=0;i<2;++i) {
        BYTE *site=image+offsets[i],*start=site-12;
        start[0]=0x6a;start[1]=7;start[2]=0x68;
        uint32_t text=(uint32_t)L"Game Options";copy_bytes(start+3,&text,4);
        start[7]=0xb9;uint32_t object=0x12345678;copy_bytes(start+8,&object,4);
        site[0]=0xe8;int32_t delta=(int32_t)(target-(site+5));copy_bytes(site+1,&delta,4);site[5]=0xc3;
    }
    if(!install_calls(image))return 86;
    typedef const WCHAR *(*Thunk)(void);
    for(int i=0;i<10000;++i)for(int j=0;j<2;++j) {
        Thunk call=(Thunk)(image+offsets[j]-12);
        const WCHAR *value=call();
        if(equal_string(value,L"Game Options")||!value[0])return 87;
    }
    if(install_calls(image))return 88; // already-patched image must be rejected
    VirtualFree(image,0,MEM_RELEASE);
    HANDLE out=GetStdHandle(STD_OUTPUT_HANDLE);DWORD done;
    const char *msg="PASS: 300000 x86 thiscall calls; 20000 calls through both patched sites; mismatch rejection; Unicode, null and unknown fallback.\r\n";
    WriteFile(out,msg,(DWORD)lstrlenA(msg),&done,NULL);return 0;
}
#endif
