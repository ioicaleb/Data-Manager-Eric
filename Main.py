from DataCollection.DataCollector import collect_data
import flet as ft

def main(page: ft.Page):
    collect_data()
    return

ft.run(main)