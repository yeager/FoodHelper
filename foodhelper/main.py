"""FoodHelper - Matdagbok med bilder för selektiva ätare."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

import json
import shutil
import sys
import os
from pathlib import Path
from datetime import datetime

from gi.repository import Gtk, Adw, Gio, GLib


APP_ID = "se.foodhelper.FoodHelper"
DATA_DIR = Path(GLib.get_user_data_dir()) / "foodhelper"
PHOTOS_DIR = DATA_DIR / "photos"
DATA_FILE = DATA_DIR / "matdagbok.json"


def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_data(entries):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


class MealRow(Gtk.ListBoxRow):
    """En rad i matdagboken som visar en maträtt."""

    def __init__(self, entry):
        super().__init__()
        self.entry = entry

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        self.set_child(box)

        # Miniatyrbild
        if entry.get("photo") and os.path.exists(entry["photo"]):
            picture = Gtk.Picture.new_for_filename(entry["photo"])
            picture.set_size_request(64, 64)
            picture.set_content_fit(Gtk.ContentFit.COVER)
            frame = Gtk.Frame()
            frame.set_child(picture)
            frame.set_size_request(64, 64)
            box.append(frame)
        else:
            icon = Gtk.Image.new_from_icon_name("image-missing")
            icon.set_pixel_size(64)
            box.append(icon)

        # Text
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        text_box.set_hexpand(True)

        name_label = Gtk.Label(label=entry.get("name", "Okänd maträtt"))
        name_label.set_xalign(0)
        name_label.add_css_class("heading")
        text_box.append(name_label)

        date_label = Gtk.Label(label=entry.get("date", ""))
        date_label.set_xalign(0)
        date_label.add_css_class("dim-label")
        text_box.append(date_label)

        if entry.get("notes"):
            note_label = Gtk.Label(label=entry["notes"])
            note_label.set_xalign(0)
            note_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
            note_label.add_css_class("dim-label")
            text_box.append(note_label)

        box.append(text_box)

        # Betyg
        rating = entry.get("rating", 3)
        rating_labels = ["😣", "😕", "😐", "🙂", "😋"]
        rating_label = Gtk.Label(label=rating_labels[min(rating, 4)])
        rating_label.set_valign(Gtk.Align.CENTER)
        rating_label.add_css_class("title-1")
        box.append(rating_label)


class AddMealDialog(Adw.Dialog):
    """Dialog för att lägga till en ny maträtt."""

    def __init__(self, parent_window):
        super().__init__()
        self.set_title("Ny maträtt")
        self.set_content_width(400)
        self.set_content_height(500)
        self.parent_window = parent_window
        self.photo_path = None

        toolbar_view = Adw.ToolbarView()
        self.set_child(toolbar_view)

        # Headerbar
        header = Adw.HeaderBar()
        header.set_show_start_title_buttons(False)
        header.set_show_end_title_buttons(False)

        cancel_btn = Gtk.Button(label="Avbryt")
        cancel_btn.connect("clicked", lambda _: self.close())
        header.pack_start(cancel_btn)

        save_btn = Gtk.Button(label="Spara")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        header.pack_end(save_btn)

        toolbar_view.add_top_bar(header)

        # Content
        clamp = Adw.Clamp()
        clamp.set_maximum_size(500)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(16)
        content.set_margin_end(16)
        clamp.set_child(content)
        toolbar_view.set_content(clamp)

        # Foto
        photo_group = Adw.PreferencesGroup(title="Foto")
        self.photo_button = Gtk.Button(label="Välj foto...")
        self.photo_button.set_icon_name("camera-photo-symbolic")
        self.photo_button.connect("clicked", self._on_pick_photo)
        photo_group.add(self.photo_button)

        self.photo_preview = Gtk.Picture()
        self.photo_preview.set_size_request(-1, 150)
        self.photo_preview.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.photo_preview.set_visible(False)
        photo_group.add(self.photo_preview)
        content.append(photo_group)

        # Namn
        name_group = Adw.PreferencesGroup(title="Maträtt")
        self.name_row = Adw.EntryRow(title="Namn på maträtten")
        name_group.add(self.name_row)
        content.append(name_group)

        # Betyg
        rating_group = Adw.PreferencesGroup(title="Betyg")
        rating_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        rating_box.set_margin_top(8)
        rating_box.set_margin_bottom(8)

        self.rating_label = Gtk.Label(label="😐 Okej")
        self.rating_label.add_css_class("title-2")
        rating_box.append(self.rating_label)

        self.rating_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 4, 1
        )
        self.rating_scale.set_value(2)
        self.rating_scale.set_draw_value(False)
        self.rating_scale.connect("value-changed", self._on_rating_changed)

        for i, mark in enumerate(["Usch", "Nej", "Okej", "Gott", "Älskar!"]):
            self.rating_scale.add_mark(i, Gtk.PositionType.BOTTOM, mark)

        rating_box.append(self.rating_scale)
        rating_group.add(rating_box)
        content.append(rating_group)

        # Anteckningar
        notes_group = Adw.PreferencesGroup(title="Anteckningar")
        notes_frame = Gtk.Frame()
        self.notes_view = Gtk.TextView()
        self.notes_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.notes_view.set_top_margin(8)
        self.notes_view.set_bottom_margin(8)
        self.notes_view.set_left_margin(8)
        self.notes_view.set_right_margin(8)
        self.notes_view.set_size_request(-1, 80)
        notes_frame.set_child(self.notes_view)
        notes_group.add(notes_frame)
        content.append(notes_group)

    def _on_rating_changed(self, scale):
        val = int(scale.get_value())
        labels = [
            "😣 Usch!",
            "😕 Gillade inte",
            "😐 Okej",
            "🙂 Gott!",
            "😋 Älskar det!",
        ]
        self.rating_label.set_label(labels[val])

    def _on_pick_photo(self, _button):
        dialog = Gtk.FileDialog()
        dialog.set_title("Välj ett foto")
        f = Gtk.FileFilter()
        f.set_name("Bilder")
        f.add_mime_type("image/jpeg")
        f.add_mime_type("image/png")
        f.add_mime_type("image/webp")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(f)
        dialog.set_filters(filters)
        dialog.open(self.parent_window, None, self._on_photo_picked)

    def _on_photo_picked(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.photo_path = file.get_path()
                self.photo_preview.set_filename(self.photo_path)
                self.photo_preview.set_visible(True)
                self.photo_button.set_label("Foto valt ✓")
        except GLib.Error:
            pass

    def _on_save(self, _button):
        name = self.name_row.get_text().strip()
        if not name:
            self.name_row.add_css_class("error")
            return

        # Kopiera foto
        saved_photo = ""
        if self.photo_path:
            ensure_dirs()
            ext = Path(self.photo_path).suffix
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            dest = PHOTOS_DIR / filename
            shutil.copy2(self.photo_path, dest)
            saved_photo = str(dest)

        # Hämta anteckningar
        buf = self.notes_view.get_buffer()
        start, end = buf.get_bounds()
        notes = buf.get_text(start, end, False)

        entry = {
            "name": name,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "photo": saved_photo,
            "rating": int(self.rating_scale.get_value()),
            "notes": notes,
        }

        entries = load_data()
        entries.insert(0, entry)
        save_data(entries)

        self.close()
        if hasattr(self.parent_window, "refresh_list"):
            self.parent_window.refresh_list()


class FoodHelperWindow(Adw.ApplicationWindow):
    """Huvudfönstret."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("FoodHelper - Matdagbok")
        self.set_default_size(420, 650)

        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        # Headerbar
        header = Adw.HeaderBar()
        add_btn = Gtk.Button(icon_name="list-add-symbolic")
        add_btn.set_tooltip_text("Lägg till maträtt")
        add_btn.add_css_class("suggested-action")
        add_btn.connect("clicked", self._on_add)
        header.pack_end(add_btn)
        toolbar_view.add_top_bar(header)

        # Content
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        toolbar_view.set_content(self.stack)

        # Tomvy
        empty = Adw.StatusPage()
        empty.set_icon_name("dish-symbolic")
        empty.set_title("Ingen mat ännu!")
        empty.set_description("Tryck + för att lägga till din första maträtt")
        self.stack.add_named(empty, "empty")

        # Lista
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.add_css_class("boxed-list")
        self.listbox.set_margin_top(16)
        self.listbox.set_margin_bottom(16)
        self.listbox.set_margin_start(16)
        self.listbox.set_margin_end(16)
        scrolled.set_child(self.listbox)
        self.stack.add_named(scrolled, "list")

        self.refresh_list()

    def refresh_list(self):
        # Rensa listan
        while True:
            row = self.listbox.get_row_at_index(0)
            if row is None:
                break
            self.listbox.remove(row)

        entries = load_data()
        if not entries:
            self.stack.set_visible_child_name("empty")
            return

        self.stack.set_visible_child_name("list")
        for entry in entries:
            self.listbox.append(MealRow(entry))

    def _on_add(self, _button):
        dialog = AddMealDialog(self)
        dialog.present(self)


class FoodHelperApp(Adw.Application):
    """Huvudapplikationen."""

    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        ensure_dirs()
        win = self.props.active_window
        if not win:
            win = FoodHelperWindow(application=self)
        win.present()


def main():
    app = FoodHelperApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    main()
