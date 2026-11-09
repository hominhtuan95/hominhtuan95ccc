import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

user32 = ctypes.windll.user32
user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.EnumWindows.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
user32.IsWindow.argtypes = [ctypes.c_void_p]
user32.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t]
user32.MapVirtualKeyW.argtypes = [ctypes.c_uint, ctypes.c_uint]
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
WM_KEYDOWN, WM_KEYUP = 0x100, 0x101
VK_TAB, VK_SPACE, VK_F8 = 0x09, 0x20, 0x77


def windows():
    found = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_ssize_t)
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, len(buf))
            if buf.value and ('chien quoc' in buf.value.lower() or 'chiến quốc' in buf.value.lower()):
                found.append((int(hwnd), buf.value))
        return True
    cb = callback_type(callback)
    user32.EnumWindows(cb, 0)
    return found


def post_key(hwnd, vk):
    scan = user32.MapVirtualKeyW(vk, 0)
    down = 1 | (scan << 16)
    if vk in (VK_TAB,):
        down |= 1 << 24
    up = down | (1 << 30) | (1 << 31)
    user32.PostMessageW(hwnd, WM_KEYDOWN, vk, down)
    time.sleep(0.025)
    user32.PostMessageW(hwnd, WM_KEYUP, vk, up)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title('Autoskill Hominhtuan95')
        # ~5 x 5 cm at 96 DPI. Actual physical size depends on display scaling.
        self.root.geometry('240x240')
        self.root.minsize(220, 220)
        self.running = False
        self.closed = False
        self.hwnds = []
        self.hwnd = None
        self.vars = [tk.BooleanVar(value=True) for _ in range(7)]
        self.ms = [tk.StringVar(value=x) for x in ('5000', '300', '1000', '2000', '3000', '4000', '6000')]
        self.status = tk.StringVar(value='Dừng | F8 bật/tắt')
        ttk.Label(root, text='Autoskill Hominhtuan95', font=('Segoe UI', 10, 'bold')).pack(pady=(3, 0))
        top = ttk.Frame(root)
        top.pack(fill='x', padx=4)
        self.choice = ttk.Combobox(top, state='readonly', width=22)
        self.choice.pack(side='left', fill='x', expand=True)
        ttk.Button(top, text='↻', width=2, command=self.refresh).pack(side='left')
        panel = ttk.Frame(root)
        panel.pack(fill='both', expand=True, padx=6)
        labels = ('Tab', 'Space', 'Skill 1', 'Skill 2', 'Skill 3', 'Skill 4', 'Skill 5')
        for i, label in enumerate(labels):
            ttk.Checkbutton(panel, text=label, variable=self.vars[i], width=9).grid(row=i, column=0, sticky='w')
            ttk.Entry(panel, textvariable=self.ms[i], width=7).grid(row=i, column=1, sticky='e')
        panel.columnconfigure(1, weight=1)
        bottom = ttk.Frame(root)
        bottom.pack(fill='x', padx=4)
        ttk.Button(bottom, text='Chạy', command=self.start).pack(side='left', expand=True, fill='x')
        ttk.Button(bottom, text='Dừng', command=self.stop).pack(side='left', expand=True, fill='x')
        ttk.Label(root, textvariable=self.status, font=('Segoe UI', 8)).pack()
        self.refresh()
        threading.Thread(target=self.hotkey, daemon=True).start()
        root.protocol('WM_DELETE_WINDOW', self.close)

    def refresh(self):
        self.hwnds = windows()
        self.choice['values'] = [f'{h} | {title[:26]}' for h, title in self.hwnds]
        if self.hwnds:
            self.choice.current(0)
        else:
            self.choice.set('Không thấy cửa sổ game')

    def start(self):
        if self.running:
            return
        idx = self.choice.current()
        if idx < 0 or idx >= len(self.hwnds):
            messagebox.showwarning('Chưa chọn game', 'Mở game và nhấn nút làm mới ↻.')
            return
        
        try:
            delays = [int(x.get()) / 1000 for x in self.ms]
            if any(not 0.05 <= x <= 180 for x in delays):
                raise ValueError
        except ValueError:
            messagebox.showerror(
                'Sai thời gian',
                'Nhập thời gian 50-180000 ms.'
            )
            return

        self.hwnd = self.hwnds[idx][0]
        enabled = [v.get() for v in self.vars]
        self.running = True
        self.status.set(f'Đang chạy | HWND {self.hwnd}')
        threading.Thread(target=self.worker, args=(self.hwnd, delays, enabled), daemon=True).start()

    def worker(self, hwnd, delays, enabled):
        vks = [VK_TAB, VK_SPACE, 0x31, 0x32, 0x33, 0x34, 0x35]
        due = [time.monotonic() + i * 0.04 for i in range(7)]
        while self.running and not self.closed:
            if not user32.IsWindow(hwnd):
                self.running = False
                self.root.after(0, self.status.set, 'Cửa sổ game đã đóng')
                break
            now = time.monotonic()
            for i in range(7):
                if not self.running:
                    break
                if enabled[i] and now >= due[i]:
                    post_key(hwnd, vks[i])
                    due[i] = time.monotonic() + delays[i]
            time.sleep(0.015)

    def stop(self):
        self.running = False
        self.status.set('Dừng | F8 bật/tắt')

    def hotkey(self):
        previous = False
        while not self.closed:
            pressed = bool(user32.GetAsyncKeyState(VK_F8) & 0x8000)
            if pressed and not previous:
                self.root.after(0, self.stop if self.running else self.start)
            previous = pressed
            time.sleep(0.08)

    def close(self):
        self.closed = True
        self.running = False
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
