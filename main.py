import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import yt_dlp

# ===== CONFIG =====
ffmpeg_path = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")
save_dir = "downloads"
os.makedirs(save_dir, exist_ok=True)
# ==================

def unique_filename(path):
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    while os.path.exists(new_path):
        new_path = f"{base} ({counter}){ext}"
        counter += 1
    return new_path

def get_video_info(url):
    try:
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info
    except Exception:
        return None

def get_resolutions(url):
    info = get_video_info(url)
    if not info:
        messagebox.showerror("Lỗi", "Không lấy được thông tin video")
        return [], "output"
    formats = info.get("formats", [])
    resolutions = []
    for f in formats:
        if f.get("vcodec") != "none":
            height = f.get("height")
            label = f"{f.get('format_id')} - {height}p ({f.get('ext')})"
            resolutions.append((f.get("format_id"), label))
    return resolutions, info.get("title", "output")

def update_status(msg):
    lbl_status.config(text=msg)
    root.update_idletasks()

def download_and_cut():
    url = entry_url.get().strip()
    start_time = entry_start.get().strip()
    end_time = entry_end.get().strip()
    mode = combo_mode.get()
    resolution = combo_res.get()

    if not url:
        messagebox.showerror("Lỗi", "Vui lòng nhập link YouTube!")
        return

    info = get_video_info(url)
    if not info:
        messagebox.showerror("Lỗi", "Không lấy được thông tin video!")
        return
    title = info.get("title", "output").replace(" ", "_")
    out_name = entry_name.get().strip() or title

    cut_file = None
    ytdlp_opts = {"outtmpl": os.path.join(save_dir, "temp.%(ext)s")}
    
    # Chọn chế độ
    if mode == "MP4 (Video + Audio)":
        cut_file = os.path.join(save_dir, f"{out_name}.mp4")
        if resolution:
            ytdlp_opts["format"] = f"{resolution.split()[0]}+bestaudio/best"
        else:
            ytdlp_opts["format"] = "bestvideo+bestaudio/best"
    elif mode == "MP3 (Audio only)":
        cut_file = os.path.join(save_dir, f"{out_name}.mp3")
        ytdlp_opts["format"] = "bestaudio"
    elif mode == "MP4 (No Audio)":
        cut_file = os.path.join(save_dir, f"{out_name}_mute.mp4")
        if resolution:
            ytdlp_opts["format"] = resolution.split()[0]
        else:
            ytdlp_opts["format"] = "bestvideo"
    else:
        messagebox.showerror("Lỗi", "Chưa chọn định dạng!")
        return

    cut_file = unique_filename(cut_file)

    try:
        update_status("📥 Đang tải video...")
        with yt_dlp.YoutubeDL(ytdlp_opts) as ydl:
            info_dict = ydl.extract_info(url)

        # Tìm file vừa tải
        temp_file = None
        for f in os.listdir(save_dir):
            if f.startswith("temp"):
                temp_file = os.path.join(save_dir, f)
                break
        if not temp_file:
            messagebox.showerror("Lỗi", "Không tìm thấy file tải về!")
            update_status("❌ Thất bại")
            return

        update_status("✂️ Đang xử lý video bằng ffmpeg...")
        if not start_time or not end_time:
            if mode == "MP3 (Audio only)":
                subprocess.run([ffmpeg_path, "-y", "-i", temp_file,
                                "-vn", "-ab", "192k", cut_file], check=True)
            else:
                cmd = [ffmpeg_path, "-y", "-i", temp_file,
                       "-c:v", "copy", "-c:a", "aac"]
                if mode == "MP4 (No Audio)":
                    cmd += ["-an"]
                cmd.append(cut_file)
                subprocess.run(cmd, check=True)
        else:
            if mode == "MP3 (Audio only)":
                subprocess.run([ffmpeg_path, "-y", "-ss", start_time, "-to", end_time,
                                "-i", temp_file, "-vn", "-ab", "192k", cut_file], check=True)
            else:
                cmd = [ffmpeg_path, "-y", "-ss", start_time, "-to", end_time,
                       "-i", temp_file, "-c:v", "copy", "-c:a", "aac"]
                if mode == "MP4 (No Audio)":
                    cmd += ["-an"]
                cmd.append(cut_file)
                subprocess.run(cmd, check=True)

        if os.path.exists(temp_file):
            os.remove(temp_file)

        messagebox.showinfo("Thành công", f"✅ File đã lưu tại:\n{cut_file}")
        update_status("✔️ Hoàn tất!")

    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra:\n{e}")
        update_status("❌ Thất bại")

def fetch_resolutions():
    url = entry_url.get().strip()
    if not url:
        messagebox.showerror("Lỗi", "Vui lòng nhập link YouTube trước!")
        return
    res, title = get_resolutions(url)
    combo_res["values"] = [f"{fmt} {label}" for fmt, label in res]
    if res:
        combo_res.current(0)
    else:
        combo_res.set("")
    if not entry_name.get().strip():
        entry_name.insert(0, title.replace(" ", "_"))

# ===== GUI =====
root = tk.Tk()
root.title("🎬 YouTube Downloader & Cutter")
root.geometry("650x550")
root.resizable(False, False)

style = ttk.Style(root)
style.configure("TLabel", font=("Segoe UI", 11))
style.configure("TButton", font=("Segoe UI", 11), padding=5)
style.configure("TCombobox", font=("Segoe UI", 11))

frame_main = ttk.Frame(root, padding=15)
frame_main.pack(fill="both", expand=True)

ttk.Label(frame_main, text="🔗 Link YouTube:").pack(anchor="w", pady=5)
entry_url = ttk.Entry(frame_main, width=70)
entry_url.pack(fill="x", pady=5)

ttk.Label(frame_main, text="🎞️ Định dạng:").pack(anchor="w", pady=5)
combo_mode = ttk.Combobox(frame_main, values=[
    "MP4 (Video + Audio)",
    "MP3 (Audio only)",
    "MP4 (No Audio)"
], state="readonly")
combo_mode.pack(fill="x", pady=5)
combo_mode.current(0)

ttk.Label(frame_main, text="📺 Độ phân giải (cho MP4):").pack(anchor="w", pady=5)
frame_res = ttk.Frame(frame_main)
frame_res.pack(fill="x", pady=5)
combo_res = ttk.Combobox(frame_res, width=50, state="readonly")
combo_res.pack(side="left", fill="x", expand=True)
btn_res = ttk.Button(frame_res, text="🔄 Lấy danh sách", command=fetch_resolutions)
btn_res.pack(side="left", padx=5)

ttk.Label(frame_main, text="⏱️ Thời gian bắt đầu (hh:mm:ss hoặc mm:ss):").pack(anchor="w", pady=5)
entry_start = ttk.Entry(frame_main, width=20)
entry_start.pack(fill="x", pady=5)

ttk.Label(frame_main, text="⏱️ Thời gian kết thúc (hh:mm:ss hoặc mm:ss):").pack(anchor="w", pady=5)
entry_end = ttk.Entry(frame_main, width=20)
entry_end.pack(fill="x", pady=5)

ttk.Label(frame_main, text="💾 Tên file (tự động nếu bỏ trống):").pack(anchor="w", pady=5)
entry_name = ttk.Entry(frame_main, width=40)
entry_name.pack(fill="x", pady=5)

btn_download = ttk.Button(frame_main, text="📥 Tải & Cắt", command=download_and_cut)
btn_download.pack(pady=15)

lbl_status = ttk.Label(frame_main, text="Trạng thái: Chưa bắt đầu", foreground="blue")
lbl_status.pack(pady=5)

root.mainloop()
