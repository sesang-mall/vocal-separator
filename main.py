import re
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
from pathlib import Path
import threading
import subprocess
from audio_processor import AudioProcessor

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

processor = AudioProcessor()

ACCENT       = "#4fc3f7"
SUCCESS      = "#2e7d32"
CARD_BG      = "#1e1e2e"
DROP_BG      = "#16213e"
DROP_HOVER   = "#1a2a4a"
LOG_BG       = "#0d0d0d"
LOG_FG       = "#90ee90"
GRAY         = "#6b7280"
BORDER       = "#2a2a3e"
BORDER_HOVER = "#4fc3f7"

STATUS_CFG = {
    "waiting":    ("⏸", GRAY,      "#1e1e2e"),
    "processing": ("🔄", ACCENT,    "#161e2e"),
    "done":       ("✅", "#4caf50", "#12201a"),
    "error":      ("❌", "#ef5350", "#201212"),
}


class QueueItem:
    _counter = 0

    def __init__(self, source: str, source_type: str, display_name: str):
        QueueItem._counter += 1
        self.id = QueueItem._counter
        self.source = source
        self.source_type = source_type   # 'file' | 'youtube'
        self.display_name = display_name
        self.status = "waiting"
        self.error = ""
        # UI refs
        self.row_frame: ctk.CTkFrame | None = None
        self.status_label: ctk.CTkLabel | None = None


class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.title("Vocal Separator")
        self.geometry("820x820")
        self.minsize(700, 680)
        self.configure(fg_color="#13131f")

        self.queue: list[QueueItem] = []
        self.busy = False

        self._build()

    # ─────────────────────────────────────────────────────────
    # Layout
    # ─────────────────────────────────────────────────────────
    def _build(self):
        self._header()
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(10, 0))
        self._queue_card(scroll)
        self._settings_row(scroll)
        self._start_button(scroll)
        self._overall_bar(scroll)
        self._current_bar(scroll)
        self._log_box(scroll)

    def _header(self):
        hdr = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="  🎵  Vocal Separator",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=ACCENT).pack(side="left", padx=16)
        ctk.CTkLabel(hdr, text="AI 기반 보컬 & 음원 분리 도구",
                     font=ctk.CTkFont(size=11), text_color=GRAY).pack(side="left")

    def _queue_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12)
        card.pack(fill="x", pady=(0, 10))

        # 카드 헤더
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(hdr, text="대기열",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self.queue_count_label = ctk.CTkLabel(hdr, text="(0개)",
                                              font=ctk.CTkFont(size=11), text_color=GRAY)
        self.queue_count_label.pack(side="left", padx=(6, 0))
        ctk.CTkButton(hdr, text="모두 제거", width=80, height=28,
                      fg_color="#3a1a1a", hover_color="#5a2a2a", text_color="#ef5350",
                      font=ctk.CTkFont(size=11),
                      command=self._clear_queue).pack(side="right")

        # 추가 버튼 행
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkButton(btn_row, text="+ 파일 추가", width=110, height=32,
                      fg_color="#1565c0", hover_color="#1976d2",
                      command=self._browse_files).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="+ URL 추가", width=110, height=32,
                      fg_color="#4a1a7a", hover_color="#6a2a9a",
                      command=self._show_url_dialog).pack(side="left")

        # 드롭 존
        self.drop_zone = ctk.CTkFrame(card, height=68, fg_color=DROP_BG,
                                      border_color=BORDER, border_width=2, corner_radius=10)
        self.drop_zone.pack(fill="x", padx=16, pady=(0, 10))
        self.drop_zone.pack_propagate(False)
        self.drop_label = ctk.CTkLabel(
            self.drop_zone,
            text="📂  여기에 파일을 드래그하세요  (여러 파일 동시 가능)",
            font=ctk.CTkFont(size=12), text_color=GRAY,
        )
        self.drop_label.pack(expand=True)
        for w in (self.drop_zone, self.drop_label):
            w.drop_target_register(DND_FILES)
            w.dnd_bind("<<Drop>>",      self._on_drop)
            w.dnd_bind("<<DragEnter>>", self._on_drag_enter)
            w.dnd_bind("<<DragLeave>>", self._on_drag_leave)

        # 대기열 목록
        self.queue_list = ctk.CTkScrollableFrame(
            card, height=170, fg_color="#13131f", corner_radius=8)
        self.queue_list.pack(fill="x", padx=16, pady=(0, 14))
        self.empty_label = ctk.CTkLabel(
            self.queue_list, text="대기열이 비어있습니다",
            font=ctk.CTkFont(size=11), text_color=GRAY)
        self.empty_label.pack(pady=24)

    def _settings_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)
        self._model_card(row)
        self._options_card(row)

    def _model_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(card, text="분리 방식",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(14, 10))
        self.model_var = tk.StringVar(value="fast")
        for val, icon, label, desc in [
            ("fast",    "⚡", "빠른 처리", "htdemucs  ·  5–10분"),
            ("quality", "⭐", "고품질",   "htdemucs_ft  ·  15–30분"),
        ]:
            r = ctk.CTkFrame(card, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=3)
            ctk.CTkRadioButton(r, text=f"{icon}  {label}", variable=self.model_var, value=val,
                               font=ctk.CTkFont(size=12),
                               radiobutton_width=16, radiobutton_height=16).pack(side="left")
            ctk.CTkLabel(r, text=desc, text_color=GRAY,
                         font=ctk.CTkFont(size=10)).pack(side="left", padx=(10, 0))
        ctk.CTkFrame(card, height=14, fg_color="transparent").pack()

    def _options_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12)
        card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(card, text="옵션",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(14, 10))
        self.open_var = tk.BooleanVar(value=True)
        self.midi_var = tk.BooleanVar(value=False)
        for var, text in [(self.open_var, "완료 후 결과 폴더 열기"),
                          (self.midi_var, "MIDI 자동 변환\n(vocals / bass / other)")]:
            ctk.CTkCheckBox(card, text=text, variable=var,
                            font=ctk.CTkFont(size=12),
                            checkbox_width=18, checkbox_height=18).pack(anchor="w", padx=16, pady=4)
        ctk.CTkFrame(card, height=10, fg_color="transparent").pack()

    def _start_button(self, parent):
        self.start_btn = ctk.CTkButton(
            parent, text="▶   대기열 시작", height=52,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=SUCCESS, hover_color="#388e3c",
            corner_radius=10, command=self._on_start,
        )
        self.start_btn.pack(fill="x", pady=(0, 8))

    def _overall_bar(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 3))
        self.overall_label = ctk.CTkLabel(
            row, text="",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT)
        self.overall_label.pack(side="left")
        self.overall_status = ctk.CTkLabel(
            row, text="",
            font=ctk.CTkFont(size=11), text_color=GRAY)
        self.overall_status.pack(side="left", padx=(8, 0))

        self.overall_bar = ctk.CTkProgressBar(
            parent, height=4, corner_radius=2,
            fg_color=CARD_BG, progress_color="#388e3c")
        self.overall_bar.pack(fill="x", pady=(0, 8))
        self.overall_bar.set(0)

    def _current_bar(self, parent):
        self.progress = ctk.CTkProgressBar(
            parent, height=8, corner_radius=4,
            fg_color=CARD_BG, progress_color=ACCENT)
        self.progress.pack(fill="x", pady=(0, 4))
        self.progress.set(0)

        stat_row = ctk.CTkFrame(parent, fg_color="transparent")
        stat_row.pack(fill="x", pady=(0, 6))
        self.pct_label = ctk.CTkLabel(
            stat_row, text="",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT)
        self.pct_label.pack(side="left")
        self.eta_label = ctk.CTkLabel(
            stat_row, text="",
            font=ctk.CTkFont(size=12), text_color=GRAY)
        self.eta_label.pack(side="right")

    def _log_box(self, parent):
        ctk.CTkLabel(parent, text="처리 로그",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=GRAY).pack(anchor="w")
        self.log = ctk.CTkTextbox(
            parent, height=180,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color=LOG_BG, text_color=LOG_FG,
            border_color=BORDER, border_width=1, corner_radius=8)
        self.log.pack(fill="both", expand=True, pady=(4, 20))

    # ─────────────────────────────────────────────────────────
    # 대기열 관리
    # ─────────────────────────────────────────────────────────
    def _add_to_queue(self, source: str, source_type: str, display_name: str):
        item = QueueItem(source, source_type, display_name)
        self.queue.append(item)
        self._render_item(item)
        self._refresh_count()

    def _render_item(self, item: QueueItem):
        self.empty_label.pack_forget()
        icon, color, bg = STATUS_CFG[item.status]

        frame = ctk.CTkFrame(self.queue_list, fg_color=bg, corner_radius=6, height=36)
        frame.pack(fill="x", pady=2)
        frame.pack_propagate(False)

        item.status_label = ctk.CTkLabel(
            frame, text=f"{icon}  {item.display_name}",
            font=ctk.CTkFont(size=11), text_color=color, anchor="w")
        item.status_label.pack(side="left", padx=10, fill="x", expand=True)

        def remove(i=item, f=frame):
            if i.status == "processing":
                return
            self.queue.remove(i)
            f.destroy()
            self._refresh_count()
            if not any(True for _ in self.queue):
                self.empty_label.pack(pady=24)

        ctk.CTkButton(frame, text="✕", width=28, height=22,
                      fg_color="#2a1a1a", hover_color="#4a2a2a", text_color="#ef5350",
                      font=ctk.CTkFont(size=10), command=remove).pack(side="right", padx=6)
        item.row_frame = frame

    def _set_item_status(self, item: QueueItem, status: str):
        item.status = status
        icon, color, bg = STATUS_CFG[status]
        if item.status_label:
            item.status_label.configure(
                text=f"{icon}  {item.display_name}", text_color=color)
        if item.row_frame:
            item.row_frame.configure(fg_color=bg)

    def _refresh_count(self):
        self.queue_count_label.configure(text=f"({len(self.queue)}개)")

    def _clear_queue(self):
        for item in [i for i in self.queue if i.status != "processing"]:
            self.queue.remove(item)
            if item.row_frame:
                item.row_frame.destroy()
        self._refresh_count()
        if not self.queue:
            self.empty_label.pack(pady=24)

    # ─────────────────────────────────────────────────────────
    # 파일 / URL 입력
    # ─────────────────────────────────────────────────────────
    def _browse_files(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("오디오 파일", "*.mp3 *.wav *.flac *.m4a"), ("전체 파일", "*.*")])
        for p in paths:
            self._add_to_queue(p, "file", Path(p).name)

    def _show_url_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("YouTube URL 추가")
        dlg.geometry("460x120")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(fg_color="#13131f")

        ctk.CTkLabel(dlg, text="YouTube URL",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(16, 6))
        entry = ctk.CTkEntry(dlg, placeholder_text="https://www.youtube.com/watch?v=...", height=36)
        entry.pack(fill="x", padx=16)

        def confirm():
            url = entry.get().strip()
            if url:
                short = url.split("v=")[-1][:11] if "v=" in url else url[-20:]
                self._add_to_queue(url, "youtube", f"YouTube · {short}")
            dlg.destroy()

        ctk.CTkButton(dlg, text="추가", height=34,
                      fg_color="#1565c0", hover_color="#1976d2",
                      command=confirm).pack(fill="x", padx=16, pady=(10, 0))
        entry.bind("<Return>", lambda e: confirm())
        entry.focus()

    def _on_drag_enter(self, event):
        self.drop_zone.configure(fg_color=DROP_HOVER, border_color=BORDER_HOVER)
        self.drop_label.configure(text="놓으면 대기열에 추가됩니다", text_color=ACCENT)

    def _on_drag_leave(self, event):
        self._reset_drop_zone()

    def _on_drop(self, event):
        self._reset_drop_zone()
        # tk.splitlist()는 TCL 리스트 파서 — {path with spaces} 와 path_no_spaces 를 모두 정확히 처리
        try:
            paths = self.tk.splitlist(event.data)
        except Exception:
            raw = event.data.strip()
            paths = re.findall(r'\{([^}]+)\}', raw) if '{' in raw else raw.split()
        for p in paths:
            p = p.strip()
            if p:
                self._add_to_queue(p, "file", Path(p).name)

    def _reset_drop_zone(self):
        self.drop_zone.configure(fg_color=DROP_BG, border_color=BORDER)
        self.drop_label.configure(
            text="📂  여기에 파일을 드래그하세요  (여러 파일 동시 가능)", text_color=GRAY)

    # ─────────────────────────────────────────────────────────
    # 진행률
    # ─────────────────────────────────────────────────────────
    _TQDM_RE = re.compile(r'(\d+)%\|.*?\|\s*\S+\s*\[[\d:]+<([\d:]+)')

    def _parse_tqdm(self, line: str):
        m = self._TQDM_RE.search(line)
        return (int(m.group(1)), m.group(2)) if m else (None, None)

    def _update_current(self, pct: int, remaining: str | None):
        self.progress.configure(mode="determinate")
        self.progress.set(pct / 100)
        self.pct_label.configure(text=f"{pct}%")
        self.eta_label.configure(
            text=(f"남은 시간  {remaining}" if remaining and remaining != "?" else
                  "완료!" if pct == 100 else ""))

    def _update_overall(self, done: int, total: int, current_name: str = ""):
        self.overall_bar.set(done / total)
        self.overall_label.configure(text=f"{done} / {total}")
        self.overall_status.configure(
            text=f"처리 중  ·  {current_name}" if current_name else "")

    # ─────────────────────────────────────────────────────────
    # 로그
    # ─────────────────────────────────────────────────────────
    def _emit(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    # ─────────────────────────────────────────────────────────
    # 처리 파이프라인
    # ─────────────────────────────────────────────────────────
    def _on_start(self):
        if self.busy:
            return
        waiting = [i for i in self.queue if i.status == "waiting"]
        if not waiting:
            self._emit("❌ 대기 중인 항목이 없습니다.")
            return

        self.busy = True
        self.start_btn.configure(state="disabled", text="⏳  처리 중...")
        threading.Thread(
            target=self._run_queue,
            args=(waiting, self.model_var.get(),
                  self.midi_var.get(), self.open_var.get()),
            daemon=True,
        ).start()

    def _run_queue(self, items: list[QueueItem], mode: str, auto_midi: bool, open_dir: bool):
        total = len(items)
        completed = 0

        for item in items:
            # UI: 현재 항목 처리 시작
            self.after(0, lambda i=item, c=completed, t=total, n=item.display_name: (
                self._set_item_status(i, "processing"),
                self._update_overall(c, t, n),
                self.progress.configure(mode="indeterminate"),
                self.progress.start(),
                self.pct_label.configure(text="준비 중..."),
                self.eta_label.configure(text=""),
            ))

            try:
                if item.source_type == "youtube":
                    self._emit(f"\n{'─'*50}")
                    self._emit(f"[다운로드] {item.display_name}")
                    audio_path = processor.download_from_youtube(item.source)
                    new_name = Path(audio_path).name
                    item.display_name = new_name
                    self._emit(f"[완료] {new_name}")
                else:
                    audio_path = item.source

                self._emit(f"\n{'─'*50}")
                self._emit(f"[{completed+1}/{total}] {Path(audio_path).name}")
                info = processor.get_audio_info(audio_path)
                self._emit(f"[정보] 길이={info['duration']}  SR={info['sample_rate']}Hz")

                model_name = "htdemucs" if mode == "fast" else "htdemucs_ft"
                self._emit(f"[분리] 모델: {model_name}")

                def on_line(line: str):
                    pct, remaining = self._parse_tqdm(line)
                    if pct is not None:
                        self.after(0, lambda p=pct, r=remaining: self._update_current(p, r))
                    else:
                        self._emit(f"  {line}")

                result_dir = processor.separate(audio_path, mode=mode, progress_callback=on_line)
                self._emit(f"[분리 완료] ✅  → {result_dir}")

                if auto_midi:
                    self._emit("[MIDI] 변환 시작...")
                    midi_files = processor.convert_to_midi(
                        result_dir, progress_callback=lambda m: self._emit(f"  {m}"))
                    self._emit(f"[MIDI 완료] ✅  {len(midi_files)}개 파일 생성")

                if open_dir:
                    subprocess.Popen(f'explorer "{result_dir}"')

                completed += 1
                self.after(0, lambda i=item: self._set_item_status(i, "done"))

            except Exception as e:
                item.error = str(e)
                self._emit(f"[오류] ❌ {e}")
                self.after(0, lambda i=item: self._set_item_status(i, "error"))
                completed += 1  # 오류도 진행으로 처리

        # 전체 완료
        done_count  = sum(1 for i in items if i.status == "done")
        error_count = sum(1 for i in items if i.status == "error")
        self._emit(f"\n{'═'*50}")
        self._emit(f"[완료] 전체 {total}개  ·  성공 {done_count}개  ·  오류 {error_count}개")
        self.after(0, lambda: self._finish(total, done_count, error_count))

    def _finish(self, total: int, done: int, error: int):
        self.busy = False
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(1)
        self.pct_label.configure(text="100%")
        self.eta_label.configure(text="완료!")
        self.overall_bar.set(1)
        self.overall_label.configure(text=f"{done} / {total}")
        self.overall_status.configure(
            text=f"모두 완료 ✅" if not error else f"완료  ·  오류 {error}개 ⚠️")
        self.start_btn.configure(state="normal", text="▶   대기열 시작")


if __name__ == "__main__":
    App().mainloop()
