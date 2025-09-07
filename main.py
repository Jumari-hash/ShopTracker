#!/usr/bin/env python3
import requests
import time
import threading
from datetime import datetime, timedelta
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty
from kivymd.app import MDApp
from kivymd.uix.card import MDCard

API_URL = "https://gagstock.gleeze.com/grow-a-garden"
REFRESH = 2  # seconds

KV = '''
BoxLayout:
    orientation: "vertical"
    md_bg_color: 0.95, 0.95, 0.95, 1

    MDLabel:
        text: "🌱 Grow a Garden — Shop Tracker"
        halign: "center"
        font_style: "H5"
        size_hint_y: None
        height: self.texture_size[1] + dp(20)
        md_bg_color: 0.2, 0.6, 0.3, 1
        theme_text_color: "Custom"
        text_color: 1, 1, 1, 1

    ScrollView:
        MDBoxLayout:
            id: shop_list
            orientation: "vertical"
            adaptive_height: True
            spacing: dp(10)
            padding: dp(10)
'''

class ShopCard(MDCard):
    shop_name = StringProperty()
    countdown = StringProperty()
    items = ListProperty()

    def __init__(self, shop_name, countdown, items, **kwargs):
        super().__init__(**kwargs)
        self.shop_name = shop_name
        self.countdown = countdown
        self.items = items
        self.size_hint_y = None
        self.height = "200dp"
        self.orientation = "vertical"
        self.padding = 10
        self.md_bg_color = (1, 1, 1, 1)
        self.elevation = 8
        self.build_card()

    def build_card(self):
        from kivymd.uix.label import MDLabel
        from kivy.uix.gridlayout import GridLayout

        self.clear_widgets()

        # Shop name + countdown
        self.add_widget(MDLabel(
            text=f"[b]{self.shop_name}[/b]  |  {self.countdown}",
            markup=True,
            font_style="Subtitle1",
            halign="center",
            theme_text_color="Primary"
        ))

        grid = GridLayout(cols=2, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for emoji, name, qty in self.items:
            grid.add_widget(MDLabel(
                text=f"{emoji} {name}",
                halign="left",
                theme_text_color="Secondary"
            ))
            grid.add_widget(MDLabel(
                text=f"x{qty}",
                halign="right",
                theme_text_color="Secondary"
            ))

        self.add_widget(grid)


class ShopTrackerApp(MDApp):
    def build(self):
        self.title = "Grow a Garden — Shop Tracker"
        return Builder.load_string(KV)

    def on_start(self):
        self.shops = {}
        Clock.schedule_interval(lambda dt: self.update_data(), REFRESH)

    def parse_cd(self, cd_str):
        h = m = s = 0
        if 'h' in cd_str:
            h = int(cd_str.split('h')[0])
        if 'm' in cd_str:
            m = int(cd_str.split('h')[-1].split('m')[0])
        if 's' in cd_str:
            s = int(cd_str.split('m')[-1].replace('s', '').strip())
        return timedelta(hours=h, minutes=m, seconds=s)

    def format_td(self, td):
        total = int(td.total_seconds())
        if total < 0:
            return "00h 00m 00s"
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}h {m:02d}m {s:02d}s"

    def fetch_data(self):
        resp = requests.get(API_URL)
        resp.raise_for_status()
        return resp.json()

    def update_data(self):
        try:
            payload = self.fetch_data()
            data = payload.get("data", {})

            shop_list = self.root.ids.shop_list
            shop_list.clear_widgets()

            for key, display in [
                ("egg", "Egg Shop"),
                ("seed", "Seed Shop"),
                ("gear", "Gear Shop"),
                ("travelingmerchant", "Traveling Merchant")
            ]:
                if key in data:
                    section = data[key]
                    items = section.get("items", [])
                    cd_str = section.get("countdown") or section.get("appearIn") or ""
                    cd_td = self.parse_cd(cd_str)

                    if key not in self.shops or self.shops[key]["items"] != items:
                        self.shops[key] = {"items": items, "cd": cd_td}
                    else:
                        self.shops[key]["cd"] -= timedelta(seconds=REFRESH)

                    cd_text = self.format_td(self.shops[key]["cd"])

                    card_items = [
                        (i.get("emoji", ""), i.get("name"), i.get("quantity"))
                        for i in self.shops[key]["items"]
                    ]

                    shop_list.add_widget(ShopCard(display, cd_text, card_items))

        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    ShopTrackerApp().run()
