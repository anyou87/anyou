# -*- coding: utf-8 -*-
"""连连看 - 50桌集成预测工具 手机版 (Kivy)

UI 层（Kivy）；预测逻辑在 core_logic.py（与桌面版完全一致）：
- 50桌策略投票 + 走势调权 + 连错分级决策（无观望）
- 庄闲多数列 + 与开奖对比变灰 + 平票绿色
- 待开行闪烁
"""
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

from core_logic import STRATEGY_LIST, run_strategy, Record, Predictor

# ==================== UI 常量 ====================
FONT = "msyh.ttc" if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "msyh.ttc")) else "Roboto"
COL_WIDTHS = [46, 52, 30, 52, 4] + [26]*50          # 55 列宽(dp)
HEADERS = ["开奖", "推荐", "对错", "多数", ""] + [f"{i+1}" for i in range(50)]
HEADER_H = 34
ROW_H = 30

# 颜色（RGBA 0-1）
C_RED     = (1, 0, 0, 1)
C_BLUE    = (0, 0, 1, 1)
C_GREEN   = (0.133, 0.667, 0.267, 1)
C_GRAY    = (0.533, 0.533, 0.533, 1)
C_BG_RED  = (1, 0.4, 0.4, 1)
C_BG_BLUE = (0.267, 0.533, 1, 1)
C_BG_GREEN= (0.133, 0.667, 0.267, 1)
C_SEP     = (0.847, 0.867, 0.894, 1)
C_PEND1   = (1, 0.949, 0.8, 1)
C_PEND2   = (1, 0.851, 0.541, 1)
C_HEADER  = (0.93, 0.94, 0.96, 1)
C_WHITE   = (1, 1, 1, 1)
C_BLACK   = (0, 0, 0, 1)
C_DARK    = (0.2, 0.2, 0.2, 1)

def make_cell(text, bg, fg, width, height, fs=11):
    b = Button(text=text, size_hint=(None, 1), width=width, height=height,
               background_normal='', background_down='', background_color=bg,
               color=fg, font_name=FONT, font_size=fs, padding=(0, 0),
               disabled=True, halign='center', valign='middle')
    return b

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.p = Predictor()
        self._flash_on = False
        self._pending_cells = []
        self._build_ui()
        self.refresh_table()
        Clock.schedule_interval(self._flash_pending, 0.9)

    # ---------- UI ----------
    def _build_ui(self):
        top = BoxLayout(size_hint_y=None, height=56, spacing=6, padding=[6, 6, 6, 6])
        btn_b = Button(text="庄 B", background_normal='', background_down='',
                       background_color=(1, 0.35, 0.35, 1), color=C_WHITE, font_name=FONT,
                       font_size=16)
        btn_p = Button(text="闲 P", background_normal='', background_down='',
                       background_color=(0.27, 0.53, 1, 1), color=C_WHITE, font_name=FONT,
                       font_size=16)
        btn_t = Button(text="和 T", background_normal='', background_down='',
                       background_color=C_BG_GREEN, color=C_WHITE, font_name=FONT,
                       font_size=16)
        btn_del = Button(text="删除", background_normal='', background_down='',
                         background_color=(0.85, 0.87, 0.9, 1), color=C_DARK, font_name=FONT,
                         font_size=13)
        btn_clr = Button(text="清空", background_normal='', background_down='',
                         background_color=(0.85, 0.87, 0.9, 1), color=C_DARK, font_name=FONT,
                         font_size=13)
        btn_b.bind(on_release=lambda w: self.add_record("B"))
        btn_p.bind(on_release=lambda w: self.add_record("P"))
        btn_t.bind(on_release=lambda w: self.add_record("T"))
        btn_del.bind(on_release=lambda w: self.del_last())
        btn_clr.bind(on_release=lambda w: self.clear_all())
        top.add_widget(btn_b); top.add_widget(btn_p); top.add_widget(btn_t)
        top.add_widget(btn_del); top.add_widget(btn_clr)
        self.add_widget(top)

        self.stats_label = Label(text="", size_hint_y=None, height=34, font_name=FONT,
                                 font_size=12, color=C_DARK, halign='left', valign='middle')
        self.stats_label.bind(size=lambda w, s: setattr(w, 'text_size', (w.width, None)))
        self.add_widget(self.stats_label)

        self.grid = GridLayout(cols=55, spacing=0, size_hint=(None, None),
                               width=sum(COL_WIDTHS))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll = ScrollView(do_scroll_x=True, do_scroll_y=True)
        scroll.add_widget(self.grid)
        self.scroll = scroll
        self.add_widget(scroll)

    # ---------- 渲染 ----------
    def refresh_table(self):
        rows, final_pred, final_tables = self.p.refresh()
        self._render(rows, final_pred, final_tables)

    def _render(self, rows, final_pred, final_tables):
        self.grid.clear_widgets()
        self._pending_cells = []
        tc = tv = 0
        mh = mt = 0
        # 表头
        for ci, htxt in enumerate(HEADERS):
            w = COL_WIDTHS[ci]
            if ci == 4:
                self.grid.add_widget(make_cell("", C_SEP, C_DARK, w, HEADER_H, fs=10))
            else:
                self.grid.add_widget(make_cell(htxt, C_HEADER, C_DARK, w, HEADER_H, fs=10))
        # 历史行
        for real, pred, tables, ce in rows:
            txt = {"B":"庄","P":"闲","T":"和"}[real]
            bg = C_BG_RED if real=="B" else (C_BG_BLUE if real=="P" else C_BG_GREEN)
            self.grid.add_widget(make_cell(txt, bg, C_WHITE, COL_WIDTHS[0], ROW_H, fs=12))
            if pred is None:
                self.grid.add_widget(make_cell("观望", (1,1,1,1), C_GRAY, COL_WIDTHS[1], ROW_H, fs=12))
            else:
                fg = C_RED if pred=="B" else C_BLUE
                self.grid.add_widget(make_cell("庄" if pred=="B" else "闲", (1,1,1,1), fg, COL_WIDTHS[1], ROW_H, fs=12))
            if pred is None or real=="T":
                self.grid.add_widget(make_cell("-", (1,1,1,1), C_GRAY, COL_WIDTHS[2], ROW_H, fs=12))
            else:
                if pred==real:
                    self.grid.add_widget(make_cell("√", (1,1,1,1), C_RED, COL_WIDTHS[2], ROW_H, fs=12)); tc+=1
                else:
                    self.grid.add_widget(make_cell("×", (1,1,1,1), C_BLACK, COL_WIDTHS[2], ROW_H, fs=12))
                tv+=1
            nb = sum(1 for t in tables if t == "B")
            np_ = sum(1 for t in tables if t == "P")
            if nb > np_: mtxt, mcol = "庄", C_RED
            elif np_ > nb: mtxt, mcol = "闲", C_BLUE
            else: mtxt, mcol = "平", C_GREEN
            if real in ("B","P") and mtxt in ("庄","闲"):
                if (mtxt == "庄" and real != "B") or (mtxt == "闲" and real != "P"):
                    mcol = C_GRAY
            if real in ("B","P") and mtxt in ("庄","闲"):
                mt += 1
                if (mtxt == "庄" and real == "B") or (mtxt == "闲" and real == "P"):
                    mh += 1
            self.grid.add_widget(make_cell(mtxt, (1,1,1,1), mcol, COL_WIDTHS[3], ROW_H, fs=12))
            self.grid.add_widget(make_cell("", C_SEP, C_DARK, COL_WIDTHS[4], ROW_H, fs=8))
            for col in range(50):
                tp = tables[col]
                if real=="T": tt="-"; tc2=C_GRAY
                elif tp==real: tt="√"; tc2=C_RED
                else: tt="×"; tc2=C_BLACK
                self.grid.add_widget(make_cell(tt, (1,1,1,1), tc2, COL_WIDTHS[5+col], ROW_H, fs=10))
        # 待开行
        self.grid.add_widget(make_cell("待开", C_PEND1, C_DARK, COL_WIDTHS[0], ROW_H, fs=12))
        if final_pred is None:
            self.grid.add_widget(make_cell("观望", C_PEND1, C_GRAY, COL_WIDTHS[1], ROW_H, fs=12))
        else:
            fg = C_RED if final_pred=="B" else C_BLUE
            self.grid.add_widget(make_cell("庄" if final_pred=="B" else "闲", C_PEND1, fg, COL_WIDTHS[1], ROW_H, fs=12))
        self.grid.add_widget(make_cell("-", C_PEND1, C_GRAY, COL_WIDTHS[2], ROW_H, fs=12))
        nb = sum(1 for t in final_tables if t == "B")
        np_ = sum(1 for t in final_tables if t == "P")
        if nb > np_: mtxt, mcol = "庄", C_RED
        elif np_ > nb: mtxt, mcol = "闲", C_BLUE
        else: mtxt, mcol = "平", C_GREEN
        self.grid.add_widget(make_cell(mtxt, C_PEND1, mcol, COL_WIDTHS[3], ROW_H, fs=12))
        self.grid.add_widget(make_cell("", C_SEP, C_DARK, COL_WIDTHS[4], ROW_H, fs=8))
        for col in range(50):
            tp = final_tables[col]
            fg = C_RED if tp=="B" else C_BLUE
            c = make_cell("庄" if tp=="B" else "闲", C_PEND1, fg, COL_WIDTHS[5+col], ROW_H, fs=10)
            self.grid.add_widget(c)
            self._pending_cells.append(c)
        # 统计栏
        if tv > 0:
            ms = f"{mh/mt*100:.1f}%" if mt>0 else "-"
            self.stats_label.text = (f"推荐投入胜率: {tc}/{tv} = {tc/tv*100:.1f}%"
                                     f" | 庄闲多数胜率: {mh}/{mt} = {ms} | 当前连错: {self.p.gerr}")
        else:
            self.stats_label.text = "输入开奖记录后开始统计"
        self.scroll.scroll_y = 0

    def _flash_pending(self, dt):
        if not self._pending_cells:
            return
        self._flash_on = not self._flash_on
        bg = C_PEND2 if self._flash_on else C_PEND1
        for i, c in enumerate(self._pending_cells):
            if i == 4:
                continue
            c.background_color = bg

    # ---------- 操作 ----------
    def add_record(self, txt):
        if txt in ("B","P","T"):
            self.p.add(txt)
            self.refresh_table()

    def del_last(self):
        self.p.del_last()
        self.refresh_table()

    def clear_all(self):
        self.p.clear()
        self.refresh_table()

class LianLianKanApp(App):
    def build(self):
        self.title = "连连看"
        return MainScreen()

if __name__ == "__main__":
    LianLianKanApp().run()
