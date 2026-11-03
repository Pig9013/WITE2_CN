using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
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
    static readonly string Settings = Path.Combine(Root,"settings.json");
    static readonly string Local = Path.Combine(Root,"settings.local.json");
    static readonly byte[] LookupSignature = {0x8b,0x54,0x24,0x04,0x81,0xec,0xfc,0x0a,0,0};
    // 语言包：payload\variants\<code> 下各有一套词典与 overlay；简体直接用 payload\overlay。
    static string Variant = "zh-CN";
    static readonly string[][] Languages = {
        new[]{"zh-CN","简体中文（中国大陆）"},
        new[]{"zh-TW","繁體中文（台灣）"},
        new[]{"zh-HK","繁體中文（香港）"},
        new[]{"zh-MO","繁體中文（澳門）"},
    };

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
    static void Warn(string message) {
        try {MessageBox.Show(message,"WitE2 中文版（英文运行）",MessageBoxButtons.OK,MessageBoxIcon.Warning);} catch { }
    }
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
    static bool HasGame(string dir) {
        if(String.IsNullOrWhiteSpace(dir))return false;
        try { return File.Exists(Path.Combine(dir,Exe)); } catch { return false; }
    }
    static string Norm(string path) {
        if(String.IsNullOrWhiteSpace(path))return null;
        try { return Path.GetFullPath(path.Trim().Trim('"').Replace('/','\\')); } catch { return null; }
    }
    static string GameFromJson(string file) {
        if(!File.Exists(file))return null;
        try {
            var obj=Json(file);object value;
            if(obj.TryGetValue("game_path",out value) && value is string)return Norm((string)value);
        } catch(Exception error) { Log("读取 "+Path.GetFileName(file)+" 失败："+error.Message); }
        return null;
    }
    static void RememberGame(string game) {
        StoreLocal(Variant,game);
        Log("已记住游戏路径："+game);
    }
    static bool StanceAcknowledged=false;
    static void StoreLocal(string variant,string game) {
        try {
            var obj=new Dictionary<string,object>();
            try { if(File.Exists(Local))obj=Json(Local); } catch { obj=new Dictionary<string,object>(); }
            if(!String.IsNullOrWhiteSpace(game))obj["game_path"]=game;
            if(!String.IsNullOrWhiteSpace(variant))obj["variant"]=variant;
            if(StanceAcknowledged)obj["stance_seen"]=true;
            File.WriteAllText(Local,new JavaScriptSerializer().Serialize(obj),new UTF8Encoding(false));
        } catch(Exception error) { Log("写入 settings.local.json 失败："+error.Message); }
    }
    static bool StanceSeen() {
        if(!File.Exists(Local))return false;
        try {
            object value;
            if(Json(Local).TryGetValue("stance_seen",out value)) {
                if(value is bool)return (bool)value;
                if(value is string)return String.Equals((string)value,"true",StringComparison.OrdinalIgnoreCase);
            }
        } catch(Exception error) { Log("读取立场标记失败："+error.Message); }
        return false;
    }
    /* 作者立场提示：仅繁体版、仅首次启动显示一次；只有一个按钮，关闭即继续，不阻断启动。 */
    static void ShowStanceNotice() {
        using(var dialog=new Form()) {
            dialog.Text="MOD 作者立場";
            dialog.Width=480;dialog.Height=306;
            dialog.FormBorderStyle=FormBorderStyle.FixedDialog;
            dialog.MaximizeBox=false;dialog.MinimizeBox=false;
            dialog.StartPosition=FormStartPosition.CenterScreen;dialog.TopMost=true;
            var head=new Label {Left=24,Top=16,Width=420,Height=28,
                Text="MOD 作者立場（僅顯示一次）",
                Font=new System.Drawing.Font("Microsoft JhengHei UI",11f,System.Drawing.FontStyle.Bold)};
            dialog.Controls.Add(head);
            var body=new Label {Left=24,Top=54,Width=418,Height=142,
                Text="本漢化包由作者個人製作。\r\n\r\n作者立場：堅持一個中國原則，支持「一國兩制」方針。\r\n\r\n以上僅為作者個人立場，不代表遊戲開發商與發行商，也不影響漢化包的下載與使用。",
                Font=new System.Drawing.Font("Microsoft JhengHei UI",9.5f)};
            dialog.Controls.Add(body);
            var ok=new Button {Text="我已明確知曉 mod 作者立場",Left=120,Top=214,Width=240,Height=34,DialogResult=DialogResult.OK};
            dialog.AcceptButton=ok;dialog.CancelButton=ok;dialog.Controls.Add(ok);
            dialog.ShowDialog();
        }
    }
    static string LanguageLabel(string code) {
        foreach(var row in Languages)if(row[0]==code)return row[1];
        return code;
    }
    static string NormalizeVariant(string value) {
        if(String.IsNullOrWhiteSpace(value))return null;
        switch(value.Trim().ToLowerInvariant()) {
            case "cn":case "zh":case "zh-cn":case "sc":case "chs":case "简体":return "zh-CN";
            case "tw":case "zh-tw":case "tc":case "cht":case "繁体":case "繁體":return "zh-TW";
            case "hk":case "zh-hk":return "zh-HK";
            case "mo":case "zh-mo":case "macau":case "macao":return "zh-MO";
        }
        return null;
    }
    static string VariantArg(string[] args) {
        for(int i=0;i<args.Length;++i) {
            if(args[i]=="--variant"||args[i]=="--lang") {
                if(i+1<args.Length) {var code=NormalizeVariant(args[i+1]);if(code!=null)return code;}
            } else if(args[i].StartsWith("--variant=",StringComparison.Ordinal)||args[i].StartsWith("--lang=",StringComparison.Ordinal)) {
                var code=NormalizeVariant(args[i].Substring(args[i].IndexOf('=')+1));if(code!=null)return code;
            }
        }
        return null;
    }
    static string StoredVariant() {
        if(!File.Exists(Local))return null;
        try {
            object value;
            if(Json(Local).TryGetValue("variant",out value) && value is string)return NormalizeVariant((string)value);
        } catch(Exception error) { Log("读取 settings.local.json 失败："+error.Message); }
        return null;
    }
    static string VariantRoot { get { return Path.Combine(Root, @"payload\variants", Variant); } }
    /* 语言包按选择物化到 payload\translations.bin：文本钩子固定读这个路径，且只在注入时读一次。 */
    static void EnsureDictionary() {
        string source=Path.Combine(VariantRoot,"translations.bin");
        string active=Path.Combine(Root,@"payload\translations.bin");
        if(!File.Exists(source))throw new IOException("汉化包缺少语言包 "+Variant+"（"+LanguageLabel(Variant)+"）。\n请重新解压完整汉化包。");
        if(File.Exists(active)&&Hash(active)==Hash(source))return;
        string temp=active+".tmp";
        File.Copy(source,temp,true);
        if(File.Exists(active))File.Delete(active);
        File.Move(temp,active);
        Log("已启用语言包 "+Variant+"："+LanguageLabel(Variant));
    }

    static List<string> FixedDrives() {
        var result=new List<string>();
        try {
            foreach(var drive in DriveInfo.GetDrives())
                if(drive.DriveType==DriveType.Fixed && drive.IsReady)result.Add(drive.RootDirectory.FullName.TrimEnd('\\'));
        } catch {}
        return result;
    }
    static List<string> SteamRoots() {
        var roots=new List<string>();
        Action<string> add=path => {
            var value=Norm(path);
            if(value!=null && !roots.Contains(value,StringComparer.OrdinalIgnoreCase))roots.Add(value);
        };
        foreach(var hive in new RegistryKey[]{Registry.CurrentUser,Registry.LocalMachine})
            foreach(var sub in new[]{@"Software\Valve\Steam",@"Software\WOW6432Node\Valve\Steam"}) {
                try {
                    using(var key=hive.OpenSubKey(sub)) {
                        if(key==null)continue;
                        add(key.GetValue("SteamPath") as string);
                        add(key.GetValue("InstallPath") as string);
                        var steamExe=key.GetValue("SteamExe") as string;
                        if(!String.IsNullOrWhiteSpace(steamExe))add(Path.GetDirectoryName(steamExe));
                    }
                } catch {}
            }
        add(Environment.GetEnvironmentVariable("STEAM_PATH"));
        add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),"Steam"));
        add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),"Steam"));
        foreach(var drive in FixedDrives()) {
            add(Path.Combine(drive,"Steam"));
            add(Path.Combine(drive,"SteamLibrary"));
            add(Path.Combine(drive,@"Games\Steam"));
            add(Path.Combine(drive,@"Games\SteamLibrary"));
            add(Path.Combine(drive,@"Program Files (x86)\Steam"));
        }
        return roots;
    }
    static IEnumerable<string> LibraryPaths(string library) {
        string file=Path.Combine(library,@"steamapps\libraryfolders.vdf");
        if(File.Exists(file)) {
            string text=null;
            try { text=File.ReadAllText(file); } catch {}
            if(text!=null) {
                foreach(Match match in Regex.Matches(text,"\"path\"\\s+\"([^\"]+)\""))yield return match.Groups[1].Value.Replace("\\\\","\\");
                foreach(Match match in Regex.Matches(text,"\"\\d+\"\\s+\"([^\"]+)\""))
                    if(match.Groups[1].Value.IndexOf(':')>=0)yield return match.Groups[1].Value.Replace("\\\\","\\");
            }
        }
        string config=Path.Combine(library,@"config\config.vdf");
        if(File.Exists(config)) {
            string text=null;
            try { text=File.ReadAllText(config); } catch {}
            if(text!=null)
                foreach(Match match in Regex.Matches(text,"\"BaseInstallFolder_\\d+\"\\s+\"([^\"]+)\""))yield return match.Groups[1].Value.Replace("\\\\","\\");
        }
    }
    static List<string> Libraries(string steamRoot) {
        var result=new List<string>();var seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        if(Directory.Exists(steamRoot) && seen.Add(steamRoot))result.Add(steamRoot);
        for(int level=0;level<3;++level) {
            foreach(var library in result.ToArray()) {
                try {
                    foreach(var path in LibraryPaths(library)) {
                        var value=Norm(path);
                        if(value!=null && Directory.Exists(value) && seen.Add(value))result.Add(value);
                    }
                } catch {}
            }
        }
        return result;
    }
    static string GameIn(string library) {
        string common=Path.Combine(library,@"steamapps\common");
        string manifest=Path.Combine(library,@"steamapps\appmanifest_1775550.acf");
        if(File.Exists(manifest)) {
            try {
                var match=Regex.Match(File.ReadAllText(manifest),"\"installdir\"\\s+\"([^\"]+)\"");
                if(match.Success) {
                    string dir=Path.Combine(common,match.Groups[1].Value);
                    if(HasGame(dir))return Path.GetFullPath(dir);
                }
            } catch {}
        }
        string guess=Path.Combine(common,"Gary Grigsby's War in the East 2");
        if(HasGame(guess))return Path.GetFullPath(guess);
        try {
            foreach(string dir in Directory.GetDirectories(common))
                if(Path.GetFileName(dir).IndexOf("War in the East",StringComparison.OrdinalIgnoreCase)>=0 && HasGame(dir))return Path.GetFullPath(dir);
        } catch {}
        return null;
    }
    static string ScanDrives() {
        var skip=new HashSet<string>(StringComparer.OrdinalIgnoreCase) {
            "windows","$recycle.bin","system volume information","programdata","users","recovery",
            "perflogs","msocache","$windows.~bt","$windows.~ws","appdata","node_modules"
        };
        foreach(var root in FixedDrives()) {
            var pending=new Queue<KeyValuePair<string,int>>();
            pending.Enqueue(new KeyValuePair<string,int>(root,0));
            int visited=0;
            while(pending.Count>0 && visited<4000) {
                var item=pending.Dequeue();++visited;
                string[] subs;
                try { subs=Directory.GetDirectories(item.Key); } catch { continue; }
                foreach(var sub in subs) {
                    string name=Path.GetFileName(sub);
                    if(String.Equals(name,"steamapps",StringComparison.OrdinalIgnoreCase)) {
                        string hit=GameIn(Path.GetDirectoryName(sub));
                        if(hit!=null)return hit;
                        continue;
                    }
                    if(item.Value<2 && !skip.Contains(name))pending.Enqueue(new KeyValuePair<string,int>(sub,item.Value+1));
                }
            }
        }
        return null;
    }
    static string FindGame(string supplied,bool allowUi) {
        if(!String.IsNullOrWhiteSpace(supplied)) {
            var given=Norm(supplied);
            if(HasGame(given))return given;
            throw new IOException("--game 指定的文件夹里没有 "+Exe+"："+supplied);
        }
        var configured=GameFromJson(Settings);
        if(configured!=null) {
            if(HasGame(configured))return configured;
            Log("settings.json 里的 game_path 已失效："+configured);
        }
        var remembered=GameFromJson(Local);
        if(remembered!=null) {
            if(HasGame(remembered))return remembered;
            Log("settings.local.json 里的路径已失效："+remembered);
        }
        var environment=Norm(Environment.GetEnvironmentVariable("WITE2_GAME"));
        if(environment!=null) {
            if(HasGame(environment))return environment;
            Log("环境变量 WITE2_GAME 已失效："+environment);
        }
        Log("开始自动查找游戏……");
        foreach(var steam in SteamRoots()) {
            if(!Directory.Exists(steam))continue;
            Log("Steam 根目录："+steam);
            foreach(var library in Libraries(steam)) {
                var found=GameIn(library);
                if(found!=null) {RememberGame(found);return found;}
            }
        }
        Log("Steam 库中未找到，开始扫描本地硬盘……");
        var scanned=ScanDrives();
        if(scanned!=null) {RememberGame(scanned);return scanned;}
        if(allowUi) {
            Log("自动查找失败，等待用户选择游戏文件夹");
            string picked=null;
            var picker=new Thread(() => {
                try {
                    using(var dialog=new FolderBrowserDialog()) {
                        dialog.Description="没有自动找到《War in the East 2》。请选择游戏文件夹（里面有 WarInTheEast2.exe）。";
                        dialog.ShowNewFolderButton=false;
                        if(dialog.ShowDialog()==DialogResult.OK)picked=dialog.SelectedPath;
                    }
                } catch(Exception error) { Log("选择游戏目录失败："+error.Message); }
            });
            picker.SetApartmentState(ApartmentState.STA);
            picker.Start();
            picker.Join();
            var chosen=Norm(picked);
            if(chosen!=null) {
                if(HasGame(chosen)) {RememberGame(chosen);return chosen;}
                var nested=Norm(Path.Combine(chosen,"Gary Grigsby's War in the East 2"));
                if(HasGame(nested)) {RememberGame(nested);return nested;}
                throw new IOException("所选文件夹里没有 "+Exe+"。\n请选择 steamapps\\common\\Gary Grigsby's War in the East 2。");
            }
        }
        throw new IOException("没有找到游戏。\n\n已尝试：settings.json / settings.local.json 的 game_path、环境变量 WITE2_GAME、Steam 注册表、所有 Steam 库目录、各盘符常见位置。\n\n可以手动指定：\n1) 在 settings.json 里写 {\"game_path\":\"D:\\\\Steam\\\\steamapps\\\\common\\\\Gary Grigsby's War in the East 2\"}；\n2) 或设置环境变量 WITE2_GAME；\n3) 或带参数启动：WitE2CN.exe --game \"游戏文件夹\"。");
    }
    static void VerifyPayload() {
        var hashes=Json(Path.Combine(Root,@"payload\checksums.json"));
        foreach(var item in hashes) {
            string path=Path.GetFullPath(Path.Combine(Root,item.Key));
            if(!Under(path,Root)||!File.Exists(path)||Hash(path)!=(string)item.Value)
                throw new IOException("汉化包文件缺失或损坏："+item.Key);
        }
    }
    static string ModVersion() {
        try {
            var data=Json(Path.Combine(Root,@"payload\package.json"));
            object value;
            if(data.TryGetValue("mod_version",out value) && value!=null) return (string)value;
        } catch { }
        return "";
    }
    static string GameVersion(string exePath) {
        try {
            var info=FileVersionInfo.GetVersionInfo(exePath);
            if(info==null||info.FileVersion==null)return "未知";
            return info.FileVersion.Replace(", ",".");
        } catch { return "未知"; }
    }
    static List<string> CompatBuilds() {
        var result=new List<string>();
        try {
            string path=Path.Combine(Root,@"payload\compat.json");
            if(File.Exists(path)) {
                var data=Json(path);object builds;
                if(data.TryGetValue("builds",out builds) && builds is object[]) {
                    foreach(var item in (object[])builds) {
                        var row=item as Dictionary<string,object>;
                        if(row==null)continue;
                        object hash;
                        if(row.TryGetValue("sha256",out hash) && hash!=null) result.Add(((string)hash).ToLowerInvariant());
                    }
                }
            }
        } catch(Exception error) { Log("读取 compat.json 失败："+error.Message); }
        object primary;
        if(Package.TryGetValue("game_sha256",out primary) && primary!=null) result.Add(((string)primary).ToLowerInvariant());
        return result;
    }
    /* 版本变化时把私有副本增量同步到新版本，存档与日志原样保留。 */
    static void SyncRuntime(string source,string version,string hash) {
        var old=(Dictionary<string,object>)Package["old_generated_tables"];
        int copied=0,seen=0;
        foreach(string file in Files(source)) {
            string relative=file.Substring(source.TrimEnd('\\').Length+1);
            if(relative.StartsWith(@"Dat\Save\",StringComparison.OrdinalIgnoreCase))continue;
            if(relative.Equals("engine.log",StringComparison.OrdinalIgnoreCase)||relative.Equals("engine-prev.log",StringComparison.OrdinalIgnoreCase))continue;
            object oldHash;
            if(old.TryGetValue(relative.Replace('\\','/'),out oldHash)&&Hash(file)==(string)oldHash)continue;
            string target=Path.GetFullPath(Path.Combine(Runtime,relative));
            if(!Under(target,Runtime))throw new IOException("资源路径越界。");
            ++seen;
            if(File.Exists(target)&&Hash(target)==Hash(file))continue;
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            File.Copy(file,target,true);
            if(++copied%200==0)Progress("正在同步中文版资源："+copied+" / "+seen);
        }
        File.WriteAllText(Path.Combine(Runtime,"WitE2CN.runtime.json"),
            new JavaScriptSerializer().Serialize(new {source=source,game_sha256=hash,game_version=version}),Encoding.UTF8);
        Status("私有副本已同步到 "+version+"（更新 "+copied+" 个文件）。");
    }
    static bool SteamRunning() {
        try { return Process.GetProcessesByName("steam").Length > 0; } catch { return false; }
    }
    // 正版判定：游戏目录旁必须存在该 AppID 的 Steam 清单，且 Steam 客户端在运行。
    // 盗版/破解版通常替换主程序、且不在 Steam 库中，两项至少缺一。
    static bool LooksGenuine(string source,out string why) {
        string manifest=null;
        var dir=new DirectoryInfo(source);
        for(int i=0;i<4 && dir!=null;i++,dir=dir.Parent) {
            string cand=Path.Combine(dir.FullName,"steamapps","appmanifest_1775550.acf");
            if(File.Exists(cand)) {manifest=cand;break;}
            string alt=Path.Combine(dir.FullName,"appmanifest_1775550.acf");
            if(File.Exists(alt)) {manifest=alt;break;}
        }
        if(manifest==null) {why="未在游戏目录附近找到 Steam 清单 appmanifest_1775550.acf";return false;}
        if(!SteamRunning()) {why="Steam 客户端未运行";return false;}
        why="";
        return true;
    }
    static void Prepare(string source) {
        NoLinks(Root);NoLinks(source);
        if(Under(source,Root)||Under(Root,source)||String.Equals(source,Root,StringComparison.OrdinalIgnoreCase))
            throw new IOException("汉化包必须放在原游戏文件夹以外。");
        string exePath=Path.Combine(source,Exe);
        if(!File.Exists(exePath))throw new IOException("游戏文件夹不正确："+source);
        string hash=Hash(exePath);
        string version=GameVersion(exePath);
        bool verified=CompatBuilds().Contains(hash);
        if(verified) Log("游戏版本 "+version+"（已登记构建）。");
        else {
            Log("游戏版本 "+version+"（未登记构建 "+hash+"）。");
            // 正版校验：未经登记的主程序，必须能证明来自 Steam 正版安装。
            string why;
            if(!LooksGenuine(source,out why))
                throw new IOException("检测到未经官方渠道安装的游戏。\n\n"+
                    "本汉化包只支持通过 Steam 购买的正版游戏，不支持任何形式的盗版。\n\n"+
                    "判定依据："+why+"\n\n"+
                    "如果你确实拥有正版，请用 Steam 校验游戏文件完整性后重试；"+
                    "游戏刚更新时也可能出现此提示，请等待汉化包更新。");
            Log("主程序未登记，但 Steam 清单与客户端均在，按正版放行。");
            Status("游戏版本 "+version+" 尚未登记，尝试接入中文……");
        }
        if(Directory.Exists(Runtime)) {
            NoLinks(Runtime);
            string marker=Path.Combine(Runtime,"WitE2CN.runtime.json");
            if(!File.Exists(marker))throw new IOException("runtime 目录不是本启动器生成的，请将其移到别处后重试。");
            var state=Json(marker);
            Files(Runtime);
            object markerHash;
            state.TryGetValue("game_sha256",out markerHash);
            if(markerHash==null||!String.Equals((string)markerHash,hash,StringComparison.OrdinalIgnoreCase)) {
                Status("检测到游戏版本变化，正在同步私有副本（保留存档）……");
                SyncRuntime(source,version,hash);
            }
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
            File.WriteAllText(Path.Combine(staging,"WitE2CN.runtime.json"),
                new JavaScriptSerializer().Serialize(new {source=source,game_sha256=hash,game_version=version}),Encoding.UTF8);
            Directory.Move(staging,Runtime);
        }
        string overlay=Path.Combine(Root,@"payload\overlay");
        foreach(string file in Files(overlay)) {
            string target=Path.GetFullPath(Path.Combine(Runtime,file.Substring(overlay.Length+1)));
            if(!Under(target,Runtime))throw new IOException("汉化资源路径越界。");
            Directory.CreateDirectory(Path.GetDirectoryName(target));
            if(!File.Exists(target)||Hash(file)!=Hash(target))File.Copy(file,target,true);
        }
        if(Variant!="zh-CN") {
            string languageOverlay=Path.Combine(VariantRoot,"overlay");
            if(!Directory.Exists(languageOverlay))throw new IOException("语言包缺少 overlay 目录："+Variant);
            foreach(string file in Files(languageOverlay)) {
                string target=Path.GetFullPath(Path.Combine(Runtime,file.Substring(languageOverlay.Length+1)));
                if(!Under(target,Runtime))throw new IOException("汉化资源路径越界。");
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                if(!File.Exists(target)||Hash(file)!=Hash(target))File.Copy(file,target,true);
            }
        }
        EnsureDictionary();
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
    /* 读取本地 exe 的 .text 段位置（PE 头未加密，可离线解析）。 */
    static bool TextRange(string exePath,out uint rva,out uint size) {
        rva=0;size=0;
        byte[] data=File.ReadAllBytes(exePath);
        if(data.Length<0x40||data[0]!='M'||data[1]!='Z')return false;
        int pe=BitConverter.ToInt32(data,0x3C);
        if(pe<=0||pe+24>data.Length)return false;
        if(data[pe]!='P'||data[pe+1]!='E')return false;
        int sections=BitConverter.ToUInt16(data,pe+6);
        int optSize=BitConverter.ToUInt16(data,pe+20);
        int table=pe+24+optSize;
        for(int i=0;i<sections;++i) {
            int o=table+i*40;
            if(o+40>data.Length)return false;
            if(data[o]=='.'&&data[o+1]=='t'&&data[o+2]=='e'&&data[o+3]=='x'&&data[o+4]=='t') {
                size=BitConverter.ToUInt32(data,o+8);
                rva=BitConverter.ToUInt32(data,o+12);
                uint raw=BitConverter.ToUInt32(data,o+16);
                if(raw>size)size=raw;
                return size>64;
            }
        }
        return false;
    }
    /* 游戏 EXE 的代码段在磁盘上是加密的（SteamStub），必须等运行时解密后再挂钩。
       这里按特征码在远端内存里寻找，不再依赖固定地址。 */
    static IntPtr WaitForSignature(IntPtr process,IntPtr moduleBase,uint rva,uint size) {
        const int chunk=0x100000;
        byte[] buffer=new byte[chunk];
        var clock=Stopwatch.StartNew();
        while(clock.Elapsed.TotalSeconds<30) {
            uint done=0;
            while(done+(uint)LookupSignature.Length<=size) {
                uint remain=size-done;
                int want=(int)Math.Min((uint)chunk,remain);
                UIntPtr got;
                if(!ReadProcessMemory(process,new IntPtr(moduleBase.ToInt64()+rva+done),buffer,(UIntPtr)want,out got))break;
                int n=(int)got.ToUInt32();
                if(n<LookupSignature.Length)break;
                for(int i=0;i+LookupSignature.Length<=n;++i) {
                    if(buffer[i]!=LookupSignature[0])continue;
                    int j=1;
                    while(j<LookupSignature.Length&&buffer[i+j]==LookupSignature[j])++j;
                    if(j==LookupSignature.Length)return new IntPtr(moduleBase.ToInt64()+rva+done+i);
                }
                done+=(uint)(n-LookupSignature.Length+1);
                if(n<want)break;
            }
            Thread.Sleep(120);
        }
        return IntPtr.Zero;
    }
    static void Connect(Process game) {
        IntPtr process=OpenProcess(0x43a,false,game.Id);
        if(process==IntPtr.Zero)throw new IOException("无法访问中文版进程，错误 "+Marshal.GetLastWin32Error());
        IntPtr remote=IntPtr.Zero;bool loaderFinished=false;
        try {
            if(game.HasExited)throw new IOException("游戏在汉化接入前退出，退出码 "+game.ExitCode+"。详情见 runtime\\engine.log。");
            uint textRva,textSize;
            if(!TextRange(Path.Combine(Runtime,Exe),out textRva,out textSize))
                throw new IOException("无法解析游戏 PE 结构。");
            IntPtr moduleBase=game.MainModule.BaseAddress;
            Status("正在等待游戏完成代码解密……");
            IntPtr seed=WaitForSignature(process,moduleBase,textRva,textSize);
            if(seed==IntPtr.Zero)
                throw new IOException("未能在游戏内存中找到本地化查表函数，该构建可能已改动代码结构。");
            Log("文字接口特征码位于 RVA 0x"+(seed.ToInt64()-moduleBase.ToInt64()).ToString("X")+"。");
            Status("正在接入中文译文……");
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
            long rva2;
            try {
                IntPtr entry=GetProcAddress(local,"Wite2CN_Initialize");
                if(entry==IntPtr.Zero)entry=GetProcAddress(local,"Wite2CN_Initialize@4");
                if(entry==IntPtr.Zero)entry=GetProcAddress(local,"_Wite2CN_Initialize@4");
                if(entry==IntPtr.Zero)throw new IOException("汉化模块入口缺失。");rva2=entry.ToInt64()-local.ToInt64();
            }
            finally {FreeLibrary(local);}
            uint initialized=RemoteCall(process,new IntPtr(unchecked((int)(module+(uint)rva2))),IntPtr.Zero);
            if(initialized!=1&&initialized!=2)
                throw new IOException("文字钩子植入失败（该构建的调用点结构已变化），详见 logs\\native.log。");
            Status("中文已接入。存档位于 runtime\\Dat\\Save。");
        }finally {
            if(remote!=IntPtr.Zero&&loaderFinished)VirtualFreeEx(process,remote,UIntPtr.Zero,0x8000);
            CloseHandle(process);
        }
    }

    /* 离线自检：不启动游戏进程，只验证汉化包完整性与四个语言包能否正确物化。 */
    static void SelfTest() {
        var report=new List<string>();
        foreach(var row in Languages) {
            string dir=Path.Combine(Root,@"payload\variants",row[0]);
            string dict=Path.Combine(dir,"translations.bin");
            if(!File.Exists(dict))throw new IOException("缺少语言包："+row[0]);
            if(row[0]!="zh-CN") {
                string overlay=Path.Combine(dir,"overlay");
                if(!File.Exists(Path.Combine(overlay,@"Dat\Fonts\WitE2CN.ttf")))throw new IOException("语言包缺少字体："+row[0]);
                if(!Directory.Exists(Path.Combine(overlay,@"Dat\Info")))throw new IOException("语言包缺少 Info 表："+row[0]);
            }
            string saved=Variant;Variant=row[0];
            try {EnsureDictionary();} finally {Variant=saved;}
            string active=Path.Combine(Root,@"payload\translations.bin");
            if(Hash(active)!=Hash(dict))throw new IOException("语言包物化校验失败："+row[0]);
            report.Add(row[0]+" "+row[1]+" "+((new FileInfo(dict).Length+524288)/1048576)+" MB OK");
        }
        Variant="zh-CN";EnsureDictionary();
        foreach(string line in report)Log("SELFTEST "+line);
        Log("SELFTEST PASS");
        File.WriteAllText(Path.Combine(Logs,"selftest.txt"),String.Join("\r\n",report.ToArray()),Encoding.UTF8);
    }
    static int Run(string[] args) {
        try {
            if(args.Contains("--where")) {string located=FindGame(null,false);Log("GAME "+located);return 0;}
            if(args.Contains("--verify")) {VerifyPayload();Log("OFFLINE VERIFY PASS");return 0;}
            Package=Json(Path.Combine(Root,@"payload\package.json"));VerifyPayload();
            if(args.Contains("--selftest")) {SelfTest();return 0;}
            if(args.Contains("--prepare"))Variant=VariantArg(args)??StoredVariant()??"zh-CN";
            Log("汉化版本 "+ModVersion()+"；语言包 "+Variant+"（"+LanguageLabel(Variant)+"）；游戏版本见下一行。");
            string supplied=null;for(int i=0;i+1<args.Length;++i)if(args[i]=="--game")supplied=args[i+1];
            var existing=ExistingPrivateGame();
            if(existing!=null) {
                if(args.Contains("--prepare"))throw new IOException("请先退出中文版再准备资源。");
                try {Connect(existing);}
                catch(Exception error) {Log("HOOK FAILED "+error);Warn("中文界面未能接入："+error.Message+"\n\n游戏继续以英文运行，存档不受影响。\n详情见 logs\\launcher.log 与 logs\\native.log。");}
                SetForegroundWindow(existing.MainWindowHandle);return 0;
            }
            Prepare(FindGame(supplied,!args.Contains("--prepare")));
            if(args.Contains("--prepare"))return 0;
            var start=new ProcessStartInfo(Path.Combine(Runtime,Exe));start.WorkingDirectory=Runtime;start.UseShellExecute=false;
            start.EnvironmentVariables["SteamAppId"]="1775550";start.EnvironmentVariables["SteamGameId"]="1775550";
            // Steam is never started or restarted by this launcher.
            Process game=Process.Start(start);
            try {Connect(game);}
            catch(Exception error) {
                // 接入失败不终止游戏：英文照常可玩，补丁与存档不受影响。
                Log("HOOK FAILED "+error);
                Warn("中文界面未能接入："+error.Message+"\n\n游戏已按英文启动，存档不受影响。\n详情见 logs\\launcher.log 与 logs\\native.log。");
            }
            return 0;
        }catch(Exception error) {
            Log("FAILED "+error);
            if(!args.Contains("--prepare")&&!args.Contains("--verify")&&!args.Contains("--where"))MessageBox.Show(error.Message+"\n\n日志："+Path.Combine(Logs,"launcher.log"),"WitE2 中文版",MessageBoxButtons.OK,MessageBoxIcon.Error);
            return 1;
        }
    }
    static string PickLanguage(string[] args) {
        string chosen=null;
        using(var dialog=new Form()) {
            dialog.Text="选择语言 / 選擇語言";
            dialog.Width=470;dialog.Height=380;
            dialog.FormBorderStyle=FormBorderStyle.FixedDialog;
            dialog.MaximizeBox=false;dialog.MinimizeBox=false;
            dialog.StartPosition=FormStartPosition.CenterScreen;dialog.TopMost=true;
            dialog.Controls.Add(new Label {Left=22,Top=14,Width=420,Height=42,
                Text="请选择汉化包使用的语言版本：\r\n請選擇漢化包使用的語言版本："});
            var radios=new List<RadioButton>();
            int top=62;
            foreach(var row in Languages) {
                var radio=new RadioButton {Left=30,Top=top,Width=400,Height=26,Text=row[1],Tag=row[0]};
                if(row[0]=="zh-CN")radio.Checked=true;
                dialog.Controls.Add(radio);radios.Add(radio);top+=32;
            }
            var remember=new CheckBox {Left=30,Top=top+4,Width=400,Height=26,
                Text="记住本次选择（下次直接启动）",Checked=true};
            dialog.Controls.Add(remember);
            var ok=new Button {Text="确定",Left=252,Top=top+44,Width=86,Height=30,DialogResult=DialogResult.OK};
            var cancel=new Button {Text="取消",Left=348,Top=top+44,Width=86,Height=30,DialogResult=DialogResult.Cancel};
            dialog.AcceptButton=ok;dialog.CancelButton=cancel;
            dialog.Controls.Add(ok);dialog.Controls.Add(cancel);
            if(dialog.ShowDialog()!=DialogResult.OK)return null;
            foreach(var radio in radios)if(radio.Checked) {chosen=(string)radio.Tag;break;}
            if(chosen!=null&&remember.Checked)StoreLocal(chosen,GameFromJson(Local));
        }
        return chosen;
    }
    [STAThread] static int Main(string[] args) {
        if(args.Contains("--prepare")||args.Contains("--verify")||args.Contains("--where")||args.Contains("--selftest"))return Run(args);
        Application.EnableVisualStyles();
        if(args.Contains("--stance-preview")) {ShowStanceNotice();return 0;}
        string wanted=VariantArg(args)??StoredVariant();
        if(wanted!=null)Variant=wanted;
        else {
            string picked=PickLanguage(args);
            if(picked==null)return 0;
            Variant=picked;
        }
        if(Variant!="zh-CN" && !StanceSeen()) {
            ShowStanceNotice();
            StanceAcknowledged=true;
            StoreLocal(Variant,GameFromJson(Local));
        }
        using(var mutex=new Mutex(false,"Local\\WitE2CN_"+Root.GetHashCode().ToString("X"))) {
            if(!mutex.WaitOne(0))return 0;
            try {
                using(var form=new Form()) {
                    string modVersion=ModVersion();form.Text=(modVersion.Length==0?"WitE2 中文版":"WitE2 中文版 v"+modVersion)+" · "+LanguageLabel(Variant);form.Width=520;form.Height=230;form.StartPosition=FormStartPosition.CenterScreen;form.FormBorderStyle=FormBorderStyle.FixedDialog;form.MaximizeBox=false;
                    var label=new Label {Left=24,Top=28,Width=460,Height=56,Text="正在准备中文版……"};form.Controls.Add(label);
                    var credit=new Label {
                        Left=24,Top=110,Width=460,Height=72,
                        Text="中文汉化 Mod 制作人：Pig9013 · DeepSeek-V4.1-Flash1017\r\n仅供交流，严禁商用\r\n不含游戏本体，仅支持正版游戏",
                        ForeColor=System.Drawing.Color.DimGray,
                        Font=new System.Drawing.Font("Microsoft YaHei",8.5f)
                    };form.Controls.Add(credit);
                    // 作者立場陳述：僅繁體版顯示，簡體版不加。
                    if(Variant!="zh-CN") {
                        form.Height=268;
                        var stance=new Label {
                            Left=24,Top=186,Width=460,Height=44,
                            Text="作者立場：堅持一個中國原則，支持「一國兩制」方針。\r\n以上為作者個人立場，不代表遊戲開發商與發行商。",
                            ForeColor=System.Drawing.Color.FromArgb(96,96,96),
                            Font=new System.Drawing.Font("Microsoft JhengHei UI",9f)
                        };form.Controls.Add(stance);
                    }
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
