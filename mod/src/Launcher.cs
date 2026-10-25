using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Win32;

internal static class Launcher
{
    static readonly string Root = Path.GetFullPath(AppDomain.CurrentDomain.BaseDirectory).TrimEnd('\\');
    static readonly string Runtime = Path.Combine(Root, "runtime");
    static readonly string Logs = Path.Combine(Root, "logs");
    static Dictionary<string, object> Package;
    static Action<string> Progress = s => {};
    const string Exe = "WarInTheEast2.exe";
    static readonly byte[] LookupSignature = {0x8b,0x54,0x24,0x04,0x81,0xec,0xfc,0x0a,0,0};

    [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint access, bool inherit, int id);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool ReadProcessMemory(IntPtr process, IntPtr address, byte[] buffer, UIntPtr size, out UIntPtr read);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool WriteProcessMemory(IntPtr process, IntPtr address, byte[] buffer, UIntPtr size, out UIntPtr written);
    [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr VirtualAllocEx(IntPtr process, IntPtr address, UIntPtr size, uint type, uint protect);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool VirtualFreeEx(IntPtr process, IntPtr address, UIntPtr size, uint type);
    [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr CreateRemoteThread(IntPtr process, IntPtr attrs, UIntPtr size, IntPtr start, IntPtr parameter, uint flags, out uint tid);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetExitCodeThread(IntPtr thread, out uint code);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)] static extern IntPtr GetModuleHandle(string name);
    [DllImport("kernel32.dll", CharSet=CharSet.Ansi, ExactSpelling=true)] static extern IntPtr GetProcAddress(IntPtr module, string name);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern IntPtr LoadLibraryEx(string path, IntPtr reserved, uint flags);
    [DllImport("kernel32.dll")] static extern bool FreeLibrary(IntPtr module);
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr window);

    static void Log(string message) {
        Directory.CreateDirectory(Logs);
        File.AppendAllText(Path.Combine(Logs,"launcher.log"),DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")+" "+message+Environment.NewLine,Encoding.UTF8);
    }
    static void Status(string message) {Log(message);Progress(message);}
    static Dictionary<string,object> Json(string path) {
        var serializer=new JavaScriptSerializer();serializer.MaxJsonLength=64*1024*1024;
        return serializer.Deserialize<Dictionary<string,object>>(File.ReadAllText(path,Encoding.UTF8));
    }
    static string Hash(string path) {
        using(var input=File.OpenRead(path))using(var sha=SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(input)).Replace("-","").ToLowerInvariant();
    }
    static bool Under(string path,string parent) {
        return Path.GetFullPath(path).StartsWith(Path.GetFullPath(parent).TrimEnd('\\')+"\\",StringComparison.OrdinalIgnoreCase);
    }
    static void NoLinks(string path) {
        for(var item=new DirectoryInfo(Path.GetFullPath(path));item!=null;item=item.Parent)
            if(item.Exists && (item.Attributes&FileAttributes.ReparsePoint)!=0)
                throw new IOException("目录含有文件链接，请将汉化包放到普通文件夹："+item.FullName);
    }
    static List<string> Files(string directory) {
        var result=new List<string>();var pending=new Stack<string>();pending.Push(directory);
        while(pending.Count>0) {
            string dir=pending.Pop();
            foreach(string path in Directory.GetFileSystemEntries(dir)) {
                var attr=File.GetAttributes(path);
                if((attr&FileAttributes.ReparsePoint)!=0)throw new IOException("目录中含有文件链接："+path);
                if((attr&FileAttributes.Directory)!=0)pending.Push(path);else result.Add(path);
            }
        }
        return result;
    }
    static string FindGame(string supplied) {
        if(!String.IsNullOrWhiteSpace(supplied))return Path.GetFullPath(supplied);
        string settings=Path.Combine(Root,"settings.json");
        if(File.Exists(settings)) {
            var obj=Json(settings);
            object configured;
            if(obj.TryGetValue("game_path",out configured) && configured is string && !String.IsNullOrWhiteSpace((string)configured)) {
                try {
                    string candidate=Path.GetFullPath((string)configured);
                    if(File.Exists(Path.Combine(candidate,Exe)))return candidate;
                    Log("settings game_path is stale, falling back to Steam discovery: "+candidate);
                } catch { Log("settings game_path is invalid, falling back to Steam discovery"); }
            }
        }
        var roots=new List<string>();
        using(var key=Registry.CurrentUser.OpenSubKey(@"Software\Valve\Steam"))
            if(key!=null && key.GetValue("SteamPath")!=null) roots.Add(key.GetValue("SteamPath").ToString().Replace('/','\\'));
        foreach(var steam in roots.ToArray()) {
            string file=Path.Combine(steam,@"steamapps\libraryfolders.vdf");
            if(!File.Exists(file))continue;
            foreach(System.Text.RegularExpressions.Match match in System.Text.RegularExpressions.Regex.Matches(File.ReadAllText(file),"\"path\"\\s+\"([^\"]+)\""))
                roots.Add(match.Groups[1].Value.Replace("\\\\","\\"));
        }
        foreach(string library in roots.Distinct(StringComparer.OrdinalIgnoreCase)) {
            string dir=Path.Combine(library,@"steamapps\common\Gary Grigsby's War in the East 2");
            if(File.Exists(Path.Combine(dir,Exe)))return Path.GetFullPath(dir);
            string manifest=Path.Combine(library,@"steamapps\appmanifest_1775550.acf");
            if(File.Exists(manifest)) {
                var match=System.Text.RegularExpressions.Regex.Match(File.ReadAllText(manifest),"\"installdir\"\\s+\"([^\"]+)\"");
                if(match.Success) {dir=Path.Combine(library,@"steamapps\common",match.Groups[1].Value);if(File.Exists(Path.Combine(dir,Exe)))return Path.GetFullPath(dir);}
            }
        }
        throw new IOException("没有找到游戏。请在 settings.json 的 game_path 中填写游戏文件夹。");
    }
    static void VerifyPayload() {
        var hashes=Json(Path.Combine(Root,@"payload\checksums.json"));
        foreach(var item in hashes) {
            string path=Path.GetFullPath(Path.Combine(Root,item.Key));
            if(!Under(path,Root)||!File.Exists(path)||Hash(path)!=(string)item.Value)
                throw new IOException("汉化包文件缺失或损坏："+item.Key);
        }
    }
    static void Prepare(string source) {
        NoLinks(Root);NoLinks(source);
        if(Under(source,Root)||Under(Root,source)||String.Equals(source,Root,StringComparison.OrdinalIgnoreCase))
            throw new IOException("汉化包必须放在原游戏文件夹以外。");
        if(!File.Exists(Path.Combine(source,Exe)))throw new IOException("游戏文件夹不正确："+source);
        if(Hash(Path.Combine(source,Exe))!=(string)Package["game_sha256"])
            throw new IOException("当前支持游戏版本 1.05.02；游戏已更新或文件不匹配，已停止启动。");
        if(Directory.Exists(Runtime)) {
            NoLinks(Runtime);
            string marker=Path.Combine(Runtime,"WitE2CN.runtime.json");
            if(!File.Exists(marker))throw new IOException("runtime 目录不是本启动器生成的，请将其移到别处后重试。");
            var state=Json(marker);
            // The runtime copy is self-contained; its original source path is
            // provenance only, not a requirement. A moved/copied mod on another
            // PC is valid if the game version hash matches.
            if((string)state["game_sha256"]!=(string)Package["game_sha256"])
                throw new IOException("运行目录属于其他游戏版本，请先保留其中存档，再将 runtime 移到别处。");
            Files(Runtime); // refuse a later junction inserted into the private tree
            if(Hash(Path.Combine(Runtime,Exe))!=(string)Package["game_sha256"])
                throw new IOException("运行目录中的游戏文件不匹配，请将 runtime 移到别处后重试。");
        } else {
            Status("首次准备中文版，正在复制本机游戏资源……");
            string staging=Path.Combine(Root,"runtime.building-"+Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(staging);
            var files=Files(source);
            var old=(Dictionary<string,object>)Package["old_generated_tables"];
            int count=0;
            foreach(string file in files) {
                string relative=file.Substring(source.TrimEnd('\\').Length+1);
                object oldHash;
                if(old.TryGetValue(relative.Replace('\\','/'),out oldHash)&&Hash(file)==(string)oldHash)continue;
                if(relative.Equals("engine.log",StringComparison.OrdinalIgnoreCase)||relative.Equals("engine-prev.log",StringComparison.OrdinalIgnoreCase))continue;
                if(relative.Equals(@"Dat\Save\wirgame.dat",StringComparison.OrdinalIgnoreCase)||relative.Equals(@"Dat\Save\wirpref.dat",StringComparison.OrdinalIgnoreCase))continue;
                string target=Path.GetFullPath(Path.Combine(staging,relative));
                if(!Under(target,staging))throw new IOException("资源路径越界。");
                Directory.CreateDirectory(Path.GetDirectoryName(target));File.Copy(file,target,false);
                if(++count%500==0)Progress("正在准备中文版："+count+" / "+files.Count);
            }
            var serializer=new JavaScriptSerializer();
            File.WriteAllText(Path.Combine(staging,"WitE2CN.runtime.json"),serializer.Serialize(new {source=source,game_sha256=(string)Package["game_sha256"]}),Encoding.UTF8);
            Directory.Move(staging,Runtime);
        }
        string overlay=Path.Combine(Root,@"payload\overlay");
        foreach(string file in Files(overlay)) {
            string target=Path.GetFullPath(Path.Combine(Runtime,file.Substring(overlay.Length+1)));
            if(!Under(target,Runtime))throw new IOException("汉化资源路径越界。");
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            if(!File.Exists(target)||Hash(file)!=Hash(target))File.Copy(file,target,true);
        }
        File.WriteAllText(Path.Combine(Runtime,"steam_appid.txt"),"1775550",Encoding.ASCII);
        Status("中文版资源准备完成；原游戏文件未写入。");
    }
    static Process ExistingPrivateGame() {
        foreach(var p in Process.GetProcessesByName("WarInTheEast2"))try {
            if(String.Equals(p.MainModule.FileName,Path.Combine(Runtime,Exe),StringComparison.OrdinalIgnoreCase))return p;
        }catch { }
        return null;
    }
    static uint RemoteCall(IntPtr process,IntPtr start,IntPtr argument) {
        uint tid;IntPtr thread=CreateRemoteThread(process,IntPtr.Zero,UIntPtr.Zero,start,argument,0,out tid);
        if(thread==IntPtr.Zero)throw new IOException("无法接入中文版进程，错误 "+Marshal.GetLastWin32Error());
        try {
            if(WaitForSingleObject(thread,30000)!=0)throw new IOException("中文版接入超时。");
            uint result;if(!GetExitCodeThread(thread,out result))throw new IOException("无法读取中文版接入结果。");
            return result;
        }finally {CloseHandle(thread);}
    }
    static void Connect(Process game) {
        IntPtr process=OpenProcess(0x43a,false,game.Id);
        if(process==IntPtr.Zero)throw new IOException("无法访问中文版进程，错误 "+Marshal.GetLastWin32Error());
        IntPtr remote=IntPtr.Zero;bool loaderFinished=false;
        try {
            Status("正在接入现有中文译文……");
            bool ready=false;
            for(int attempt=0;attempt<600;++attempt) {
                if(game.HasExited)throw new IOException("游戏在汉化接入前退出，退出码 "+game.ExitCode+"。详情见 runtime\\engine.log。");
                try {
                    game.Refresh();IntPtr baseAddress=game.MainModule.BaseAddress;
                    byte[] bytes=new byte[10];UIntPtr n;
                    if(ReadProcessMemory(process,IntPtr.Add(baseAddress,0x456ef0),bytes,(UIntPtr)10,out n)&&n.ToUInt32()==10&&bytes.SequenceEqual(LookupSignature)){ready=true;break;}
                }catch(System.ComponentModel.Win32Exception) { }
                Thread.Sleep(100);
            }
            if(!ready)throw new IOException("游戏文字接口未就绪，已停止接入。");
            string dll=Path.Combine(Root,"WitE2CN_Text.dll");
            byte[] name=Encoding.Unicode.GetBytes(dll+"\0");
            remote=VirtualAllocEx(process,IntPtr.Zero,(UIntPtr)name.Length,0x3000,4);
            if(remote==IntPtr.Zero)throw new IOException("无法为中文版接入分配空间。");
            UIntPtr written;
            if(!WriteProcessMemory(process,remote,name,(UIntPtr)name.Length,out written)||written.ToUInt32()!=name.Length)throw new IOException("无法载入汉化模块路径。");
            uint module=RemoteCall(process,GetProcAddress(GetModuleHandle("kernel32.dll"),"LoadLibraryW"),remote);
            loaderFinished=true;
            if(module==0)throw new IOException("游戏无法载入汉化模块。");
            IntPtr local=LoadLibraryEx(dll,IntPtr.Zero,1);
            if(local==IntPtr.Zero)throw new IOException("无法读取汉化模块入口。");
            long rva;
            try {
                IntPtr entry=GetProcAddress(local,"Wite2CN_Initialize");
                if(entry==IntPtr.Zero)entry=GetProcAddress(local,"Wite2CN_Initialize@4");
                if(entry==IntPtr.Zero)entry=GetProcAddress(local,"_Wite2CN_Initialize@4");
                if(entry==IntPtr.Zero)throw new IOException("汉化模块入口缺失。");rva=entry.ToInt64()-local.ToInt64();
            }
            finally {FreeLibrary(local);}
            uint initialized=RemoteCall(process,new IntPtr(unchecked((int)(module+(uint)rva))),IntPtr.Zero);
            if(initialized!=1&&initialized!=2)throw new IOException("文字接入检查未通过，详情见 logs\\native.log。");
            Status("中文已接入。存档位于 runtime\\Dat\\Save。");
        }finally {
            if(remote!=IntPtr.Zero&&loaderFinished)VirtualFreeEx(process,remote,UIntPtr.Zero,0x8000);
            CloseHandle(process);
        }
    }
    static int Run(string[] args) {
        try {
            if(args.Contains("--verify")) {VerifyPayload();Log("OFFLINE VERIFY PASS");return 0;}
            Package=Json(Path.Combine(Root,@"payload\package.json"));VerifyPayload();
            string supplied=null;for(int i=0;i+1<args.Length;++i)if(args[i]=="--game")supplied=args[i+1];
            var existing=ExistingPrivateGame();
            if(existing!=null) {if(args.Contains("--prepare"))throw new IOException("请先退出中文版再准备资源。");Connect(existing);SetForegroundWindow(existing.MainWindowHandle);return 0;}
            Prepare(FindGame(supplied));
            if(args.Contains("--prepare"))return 0;
            var start=new ProcessStartInfo(Path.Combine(Runtime,Exe));start.WorkingDirectory=Runtime;start.UseShellExecute=false;
            start.EnvironmentVariables["SteamAppId"]="1775550";start.EnvironmentVariables["SteamGameId"]="1775550";
            // Steam is never started or restarted by this launcher.
            Process game=Process.Start(start);
            try {Connect(game);}catch {
                // A failed handshake must never leave a misleading partial session.
                if(!game.HasExited)game.Kill();throw;
            }
            return 0;
        }catch(Exception error) {
            Log("FAILED "+error);
            if(!args.Contains("--prepare")&&!args.Contains("--verify"))MessageBox.Show(error.Message+"\n\n日志："+Path.Combine(Logs,"launcher.log"),"WitE2 中文版",MessageBoxButtons.OK,MessageBoxIcon.Error);
            return 1;
        }
    }
    [STAThread] static int Main(string[] args) {
        if(args.Contains("--prepare")||args.Contains("--verify"))return Run(args);
        Application.EnableVisualStyles();
        using(var mutex=new Mutex(false,"Local\\WitE2CN_"+Root.GetHashCode().ToString("X"))) {
            if(!mutex.WaitOne(0))return 0;
            try {
                using(var form=new Form()) {
                    form.Text="WitE2 中文版";form.Width=520;form.Height=160;form.StartPosition=FormStartPosition.CenterScreen;form.FormBorderStyle=FormBorderStyle.FixedDialog;form.MaximizeBox=false;
                    var label=new Label {Left=24,Top=32,Width=460,Height=60,Text="正在准备中文版……"};form.Controls.Add(label);
                    Progress=s=>{if(!form.IsDisposed&&form.IsHandleCreated)form.BeginInvoke(new Action(()=>label.Text=s));};
                    int result=1;bool running=true;
                    form.FormClosing+=(s,e)=>{if(running)e.Cancel=true;};
                    form.Shown+=(s,e)=>new Thread(()=> {result=Run(args);running=false;if(!form.IsDisposed)form.BeginInvoke(new Action(form.Close));}){IsBackground=true}.Start();
                    Application.Run(form);return result;
                }
            }finally {mutex.ReleaseMutex();}
        }
    }
}
