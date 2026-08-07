"""Fenêtre principale — multi-registres, combine, jurisprudence, postlink."""

from __future__ import annotations

import os
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .runner import (
    DEFAULT_OUT,
    ROOT,
    attach_styles_cmdline,
    build_request,
    master_styles_path,
    postlink_cmdline,
    resolve_python,
    to_pdf_cmdline,
)


class NotionExportApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Éditions Particulières — Notion → Word / HTML")
        self.minsize(800, 780)
        self.geometry("900x860")
        self.configure(bg="#f3f1ec")

        self._proc: subprocess.Popen[str] | None = None
        self._log_q: queue.Queue[str | None] = queue.Queue()
        self._running = False
        self._cancel = threading.Event()

        self._setup_style()
        self._build()
        self._sync_options()
        self.after(80, self._drain_log)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 16), background="#f3f1ec")
        style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground="#5a564e", background="#f3f1ec")
        style.configure("Card.TLabelframe", background="#faf9f6")
        style.configure("Card.TLabelframe.Label", font=("Segoe UI Semibold", 10), background="#faf9f6")
        style.configure("TLabel", background="#faf9f6")
        style.configure("TCheckbutton", background="#faf9f6")
        style.configure("TRadiobutton", background="#faf9f6")
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 5))
        style.configure("Root.TFrame", background="#f3f1ec")
        style.configure("Hint.TLabel", font=("Segoe UI", 8), foreground="#6a665e", background="#faf9f6")

        # Couleurs bouton Générer (tk.Button — ttk ignore souvent le fond sous Windows)
        self._run_bg_ready = "#2f7d4a"  # vert
        self._run_bg_busy = "#6b1e2a"  # bordeaux
        self._run_fg = "#ffffff"

    def _build(self) -> None:
        root = ttk.Frame(self, style="Root.TFrame", padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(root, text="Éditions Particulières", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(
            root,
            text="Word : export .docx · PDF : post-traitement Word (pywin32) · HTML : en attente",
            style="Sub.TLabel",
        ).pack(anchor=tk.W, pady=(0, 10))

        # —— Source : soit registres entiers, soit fiches (exclusif) ——
        src = ttk.LabelFrame(root, text="Source", style="Card.TLabelframe", padding=12)
        src.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.source_mode = tk.StringVar(value="registres")
        mode_row = ttk.Frame(src)
        mode_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(mode_row, text="Mode :").pack(side=tk.LEFT)
        ttk.Radiobutton(
            mode_row,
            text="Registre(s) entier(s)",
            value="registres",
            variable=self.source_mode,
            command=self._sync_options,
        ).pack(side=tk.LEFT, padx=(8, 16))
        ttk.Radiobutton(
            mode_row,
            text="Fiche(s) choisie(s)",
            value="pages",
            variable=self.source_mode,
            command=self._sync_options,
        ).pack(side=tk.LEFT)
        ttk.Label(
            src,
            text="Choisissez l’un ou l’autre : tout un registre, ou seulement certaines pages.",
            style="Hint.TLabel",
            wraplength=820,
        ).pack(anchor=tk.W, pady=(0, 8))

        # Bloc registres
        self.regs_box = ttk.LabelFrame(
            src, text="Registre(s) — toutes les fiches de chaque base cochée", style="Card.TLabelframe", padding=8
        )
        self.regs_box.pack(fill=tk.X, pady=(0, 8))
        reg_row = ttk.Frame(self.regs_box)
        reg_row.pack(fill=tk.X)
        self.var_manuel = tk.BooleanVar(value=True)
        self.var_fiches = tk.BooleanVar(value=False)
        self.var_methodo = tk.BooleanVar(value=False)
        self.var_formule = tk.BooleanVar(value=False)
        self.var_index = tk.BooleanVar(value=False)
        self.var_arrets = tk.BooleanVar(value=False)
        self._reg_checks: list[ttk.Checkbutton] = []
        for text, var in (
            ("Manuel", self.var_manuel),
            ("Fiches", self.var_fiches),
            ("Méthode", self.var_methodo),
            ("Formule", self.var_formule),
            ("Glossaire", self.var_index),
            ("Jurisprudence", self.var_arrets),
        ):
            cb = ttk.Checkbutton(reg_row, text=text, variable=var, command=self._sync_options)
            cb.pack(side=tk.LEFT, padx=(0, 14))
            self._reg_checks.append(cb)

        ttk.Label(
            self.regs_box, text="Autre(s) — URL/id de base(s) hors registre (une par ligne)"
        ).pack(anchor=tk.W, pady=(8, 0))
        self.autres_text = tk.Text(
            self.regs_box,
            height=2,
            wrap=tk.WORD,
            font=("Consolas", 10),
            relief=tk.SOLID,
            borderwidth=1,
        )
        self.autres_text.pack(fill=tk.X, pady=(2, 0))
        self.autres_text.bind("<<Modified>>", self._on_autres_modified)

        # Bloc fiches (listes toujours visibles — pas besoin de cocher un registre)
        self.fiches_box = ttk.LabelFrame(
            src,
            text="Fiche(s) — multi-sélection (Ctrl/Maj) dans un ou plusieurs onglets",
            style="Card.TLabelframe",
            padding=8,
        )
        self.fiches_box.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            self.fiches_box,
            text="Actualiser un onglet pour charger sa liste. "
            "Saisie libre = URL / id / fragment en complément.",
            style="Hint.TLabel",
            wraplength=820,
        ).pack(anchor=tk.W)

        self._fiche_notebook = ttk.Notebook(self.fiches_box)
        self._fiche_notebook.pack(fill=tk.BOTH, expand=True, pady=(4, 4))
        self._fiche_tabs: dict[str, dict] = {}
        from packages.ep_core.registers import REGISTRE_LABELS as REGISTRE_LABELS

        for key in ("manuel", "fiches", "methodo", "formule", "index", "arrets"):
            meta = self._make_fiche_tab(key, REGISTRE_LABELS[key])
            self._fiche_tabs[key] = meta
            self._fiche_notebook.add(meta["frame"], text=REGISTRE_LABELS[key])
            meta["tab_id"] = True

        ttk.Label(self.fiches_box, text="Saisie libre (optionnel, une par ligne)").pack(
            anchor=tk.W
        )
        self.pages_text = tk.Text(
            self.fiches_box,
            height=2,
            wrap=tk.WORD,
            font=("Consolas", 10),
            relief=tk.SOLID,
            borderwidth=1,
        )
        self.pages_text.pack(fill=tk.X, pady=(2, 0))
        self.pages_text.bind("<<Modified>>", self._on_pages_modified)

        # —— Options ——
        opt = ttk.LabelFrame(root, text="Options de sortie", style="Card.TLabelframe", padding=12)
        opt.pack(fill=tk.X, pady=(0, 8))

        row1 = ttk.Frame(opt)
        row1.pack(fill=tk.X)
        self.combine = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            row1, text="Combiner → 1 fichier", variable=self.combine, command=self._sync_options
        ).pack(side=tk.LEFT)
        ttk.Label(row1, text="Nom").pack(side=tk.LEFT, padx=(12, 4))
        self.name = tk.StringVar()
        self.name_entry = ttk.Entry(row1, textvariable=self.name, width=28)
        self.name_entry.pack(side=tk.LEFT)
        ttk.Label(row1, text="Limite").pack(side=tk.LEFT, padx=(16, 4))
        self.limit = tk.StringVar()
        ttk.Entry(row1, textvariable=self.limit, width=6).pack(side=tk.LEFT)

        self.juri_box = ttk.LabelFrame(
            opt, text="Recueil de jurisprudence", style="Card.TLabelframe", padding=8
        )
        self.juri_box.pack(fill=tk.X, pady=(10, 0))
        self.arrets_refresh = tk.BooleanVar(value=True)
        self.arrets_fmt = tk.StringVar(value="a4")
        self.cb_arrets_refresh = ttk.Checkbutton(
            self.juri_box,
            text="Mise à jour BdD (Notion → CSV)",
            variable=self.arrets_refresh,
        )
        self.cb_arrets_refresh.pack(anchor=tk.W)
        fmt_row = ttk.Frame(self.juri_box)
        fmt_row.pack(anchor=tk.W, pady=(4, 0))
        self.rb_arrets_a4 = ttk.Radiobutton(
            fmt_row,
            text="Impression A4",
            value="a4",
            variable=self.arrets_fmt,
            command=self._sync_options,
        )
        self.rb_arrets_a4.pack(side=tk.LEFT, padx=(0, 16))
        self.rb_arrets_a5 = ttk.Radiobutton(
            fmt_row,
            text="Impression A5",
            value="a5",
            variable=self.arrets_fmt,
            command=self._sync_options,
        )
        self.rb_arrets_a5.pack(side=tk.LEFT)
        ttk.Label(
            self.juri_box,
            text="A4/A5 : uniquement si Jurisprudence est la seule source.",
            style="Hint.TLabel",
        ).pack(anchor=tk.W, pady=(4, 0))

        fmt_out = ttk.Frame(opt)
        fmt_out.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(fmt_out, text="Format").pack(side=tk.LEFT)
        self.out_format = tk.StringVar(value="docx")
        ttk.Radiobutton(
            fmt_out, text="Word (.docx)", value="docx", variable=self.out_format, command=self._sync_options
        ).pack(side=tk.LEFT, padx=(12, 8))
        ttk.Radiobutton(
            fmt_out, text="HTML (site)", value="html", variable=self.out_format, command=self._sync_options
        ).pack(side=tk.LEFT, padx=(8, 0))

        pdf_row = ttk.Frame(opt)
        pdf_row.pack(fill=tk.X, pady=(6, 0))
        self.also_pdf = tk.BooleanVar(value=False)
        self.cb_also_pdf = ttk.Checkbutton(
            pdf_row,
            text="Générer aussi PDF (post-traitement Word)",
            variable=self.also_pdf,
            command=self._sync_options,
        )
        self.cb_also_pdf.pack(side=tk.LEFT)

        self.site_tpl_row = ttk.Frame(opt)
        self.site_tpl_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(self.site_tpl_row, text="Gabarits site").pack(side=tk.LEFT)
        from .runner import default_site_templates

        self.site_templates = tk.StringVar(value=str(default_site_templates()))
        self.site_tpl_entry = ttk.Entry(
            self.site_tpl_row, textvariable=self.site_templates
        )
        self.site_tpl_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        ttk.Button(
            self.site_tpl_row, text="…", width=3, command=self._browse_site_templates
        ).pack(side=tk.LEFT)

        self.fmt_hint = ttk.Label(opt, text="", style="Hint.TLabel", wraplength=820)
        self.fmt_hint.pack(anchor=tk.W, pady=(2, 0))

        out_row = ttk.Frame(opt)
        out_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(out_row, text="Dossier de sortie").pack(side=tk.LEFT)
        self.out = tk.StringVar(value=str(DEFAULT_OUT))
        ttk.Entry(out_row, textvariable=self.out).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=8
        )
        ttk.Button(out_row, text="…", width=3, command=self._browse_out).pack(side=tk.LEFT)

        # —— Actions ——
        actions = ttk.Frame(root, style="Root.TFrame")
        actions.pack(fill=tk.X, pady=(0, 8))
        self.btn_run = tk.Button(
            actions,
            text="Générer",
            font=("Segoe UI Semibold", 11),
            command=self._on_run,
            bg=self._run_bg_ready,
            fg=self._run_fg,
            activebackground="#26683c",
            activeforeground=self._run_fg,
            disabledforeground="#f0e6e8",
            relief=tk.FLAT,
            padx=16,
            pady=7,
            cursor="hand2",
            borderwidth=0,
            highlightthickness=0,
        )
        self.btn_run.pack(side=tk.LEFT)
        self.btn_stop = ttk.Button(
            actions, text="Arrêter", command=self._on_stop, state=tk.DISABLED
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Ouvrir le dossier", command=self._open_out).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        self.status = ttk.Label(actions, text="Prêt", style="Sub.TLabel")
        self.status.pack(side=tk.RIGHT)

        # —— Liens / styles ——
        link_box = ttk.LabelFrame(
            root, text="Après génération (optionnel)", style="Card.TLabelframe", padding=10
        )
        link_box.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(
            link_box,
            text="Postlink : réécrit les liens entre fiches déjà exportées (Notion → fichier Word local), "
            "via output/manifest.json. Un passage après tous les registres suffit.",
            style="Hint.TLabel",
            wraplength=820,
        ).pack(anchor=tk.W)
        ttk.Label(
            link_box,
            text="Attacher styles : rattache les .docx existants au modèle Editions_Particulieres.dotx "
            "(mise à jour auto des styles à l'ouverture dans Word).",
            style="Hint.TLabel",
            wraplength=820,
        ).pack(anchor=tk.W, pady=(2, 6))
        ttk.Label(
            link_box,
            text="Convertir en PDF : transforme les .docx déjà exportés en .pdf via Microsoft Word (pywin32).",
            style="Hint.TLabel",
            wraplength=820,
        ).pack(anchor=tk.W, pady=(2, 6))
        link_row = ttk.Frame(link_box)
        link_row.pack(fill=tk.X)
        self.btn_postlink = ttk.Button(link_row, text="Postlink", command=self._on_postlink)
        self.btn_postlink.pack(side=tk.LEFT)
        self.btn_attach = ttk.Button(
            link_row, text="Attacher styles", command=self._on_attach
        )
        self.btn_attach.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_pdf = ttk.Button(
            link_row, text="Convertir en PDF", command=self._on_pdf
        )
        self.btn_pdf.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(link_row, text="Ouvrir master styles", command=self._open_master).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        # —— Journal ——
        log_box = ttk.LabelFrame(root, text="Journal", style="Card.TLabelframe", padding=8)
        log_box.pack(fill=tk.BOTH, expand=True)
        self.log = tk.Text(
            log_box,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1f1c",
            fg="#e8e6df",
            insertbackground="#e8e6df",
            relief=tk.FLAT,
            state=tk.DISABLED,
        )
        scroll = ttk.Scrollbar(log_box, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _clear_fiche_selection(self) -> None:
        """Désélectionne toutes les fiches (onglets + saisie libre)."""
        for meta in self._fiche_tabs.values():
            lb: tk.Listbox = meta["listbox"]
            lb.selection_clear(0, tk.END)
        self.pages_text.delete("1.0", tk.END)
        self._sync_options()

    def _make_fiche_tab(self, registre: str, title: str) -> dict:
        frame = ttk.Frame(self._fiche_notebook, padding=4)
        top = ttk.Frame(frame)
        top.pack(fill=tk.X)
        btn = ttk.Button(
            top, text="Actualiser la liste", command=lambda r=registre: self._refresh_fiches(r)
        )
        btn.pack(side=tk.LEFT)
        ttk.Label(top, text="Filtrer").pack(side=tk.LEFT, padx=(12, 4))
        filter_var = tk.StringVar()
        filter_entry = ttk.Entry(top, textvariable=filter_var, width=28)
        filter_entry.pack(side=tk.LEFT)
        filter_var.trace_add(
            "write",
            lambda *_a, r=registre: self._apply_fiche_filter(r),
        )
        ttk.Button(
            top,
            text="Effacer toute la sélection",
            command=self._clear_fiche_selection,
        ).pack(side=tk.LEFT, padx=(8, 0))
        status = ttk.Label(top, text="—", style="Hint.TLabel")
        status.pack(side=tk.LEFT, padx=(8, 0))

        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        lb = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            font=("Segoe UI", 9),
            height=6,
            exportselection=False,
            activestyle="dotbox",
        )
        sb = ttk.Scrollbar(list_frame, command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        lb.bind("<<ListboxSelect>>", lambda _e: self._sync_options())

        meta = {
            "frame": frame,
            "listbox": lb,
            "status": status,
            "button": btn,
            "filter_var": filter_var,
            "filter_entry": filter_entry,
            "all_entries": [],  # liste complète après actualisation
            "entries": [],  # liste affichée (filtrée)
            "tab_id": True,
        }
        return meta

    def _on_autres_modified(self, _event=None) -> None:
        self.autres_text.edit_modified(False)
        self._sync_options()

    def _on_pages_modified(self, _event=None) -> None:
        self.pages_text.edit_modified(False)
        self._sync_options()

    def _selected_registres(self) -> list[str]:
        out: list[str] = []
        if self.var_manuel.get():
            out.append("manuel")
        if self.var_fiches.get():
            out.append("fiches")
        if self.var_methodo.get():
            out.append("methodo")
        if self.var_formule.get():
            out.append("formule")
        if self.var_index.get():
            out.append("index")
        if self.var_arrets.get():
            out.append("arrets")
        return out

    def _has_autres(self) -> bool:
        return any(
            ln.strip() and not ln.strip().startswith("#")
            for ln in self.autres_text.get("1.0", tk.END).splitlines()
        )

    def _has_free_pages(self) -> bool:
        from .runner import parse_lines

        return bool(parse_lines(self.pages_text.get("1.0", tk.END)))

    def _pages_by_registre(self) -> dict[str, list[str]]:
        """Ids sélectionnés dans chaque onglet fiches."""
        out: dict[str, list[str]] = {}
        for key, meta in self._fiche_tabs.items():
            lb: tk.Listbox = meta["listbox"]
            entries = meta.get("entries") or []
            ids: list[str] = []
            for idx in lb.curselection():
                if 0 <= idx < len(entries):
                    ids.append(entries[idx].id)
            if ids:
                out[key] = ids
        return out

    def _selected_page_ids(self) -> list[str]:
        """Ids listbox + saisie libre (ordre : onglets puis libre)."""
        from .runner import parse_lines

        ids: list[str] = []
        seen: set[str] = set()
        by_reg = self._pages_by_registre()
        for key in ("manuel", "fiches", "methodo", "formule", "index", "arrets"):
            for pid in by_reg.get(key, []):
                if pid not in seen:
                    seen.add(pid)
                    ids.append(pid)
        for line in parse_lines(self.pages_text.get("1.0", tk.END)):
            if line not in seen:
                seen.add(line)
                ids.append(line)
        return ids

    def _registres_for_pages_mode(self) -> list[str]:
        """Registres à interroger en mode fiches."""
        from packages.ep_core.registers import REGISTRE_ORDER

        keyed = list(self._pages_by_registre().keys())
        if keyed:
            return [r for r in REGISTRE_ORDER if r in keyed]
        # Saisie libre seule → chercher dans tous les registres connus
        if self._has_free_pages():
            return list(REGISTRE_ORDER)
        return []

    def _set_widget_tree_state(self, widget: tk.Misc, state: str) -> None:
        try:
            widget.configure(state=state)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_widget_tree_state(child, state)

    def _sync_options(self) -> None:
        mode = self.source_mode.get()
        pages_mode = mode == "pages"
        html_mode = self.out_format.get() == "html"

        # Activer / griser les deux blocs
        regs_state = tk.DISABLED if pages_mode else tk.NORMAL
        pages_state = tk.NORMAL if pages_mode else tk.DISABLED
        for cb in self._reg_checks:
            cb.configure(state=regs_state)
        self.autres_text.configure(state=regs_state)
        self._set_widget_tree_state(self.fiches_box, pages_state)

        if html_mode:
            self.var_arrets.set(False)
            for cb in self._reg_checks:
                if cb.cget("text") == "Jurisprudence":
                    cb.configure(state=tk.DISABLED)
        elif not pages_mode:
            for cb in self._reg_checks:
                cb.configure(state=tk.NORMAL)

        has_manuel = (
            self.var_manuel.get()
            if not pages_mode
            else "manuel" in self._registres_for_pages_mode()
        )
        site_tpl_state = (
            tk.NORMAL if html_mode and has_manuel and not self.combine.get() else tk.DISABLED
        )
        self._set_widget_tree_state(self.site_tpl_row, site_tpl_state)

        docx_only = tk.NORMAL if not html_mode else tk.DISABLED
        self.btn_postlink.configure(state=docx_only)
        self.btn_attach.configure(state=docx_only)
        self.btn_pdf.configure(state=docx_only)
        self.cb_also_pdf.configure(state=docx_only)
        if html_mode:
            self.also_pdf.set(False)

        if html_mode:
            if has_manuel and not self.combine.get():
                self.fmt_hint.configure(
                    text="HTML : disponible prochainement · export site manuel (sommaire + chapitres)."
                )
            else:
                self.fmt_hint.configure(
                    text="HTML : disponible prochainement · fichiers .html par slug."
                )
        elif self.also_pdf.get():
            self.fmt_hint.configure(
                text="PDF : conversion automatique après génération Word (Microsoft Word requis)."
            )
        else:
            self.fmt_hint.configure(text="")

        # Jurisprudence : MAJ CSV si arrets inclus ; A4/A5 seulement si arrets seul
        if pages_mode:
            regs = self._registres_for_pages_mode()
            has_juri = "arrets" in regs and not html_mode
            only_juri = regs == ["arrets"]
        else:
            regs = self._selected_registres()
            has_juri = "arrets" in regs and not html_mode
            only_juri = regs == ["arrets"] and not self._has_autres()

        self.cb_arrets_refresh.configure(
            state=tk.NORMAL if has_juri else tk.DISABLED
        )
        a5_state = tk.NORMAL if only_juri else tk.DISABLED
        self.rb_arrets_a4.configure(state=a5_state)
        self.rb_arrets_a5.configure(state=a5_state)
        if not only_juri:
            self.arrets_fmt.set("a4")

        self.name_entry.configure(
            state=tk.NORMAL if self.combine.get() else tk.DISABLED
        )

    def _browse_site_templates(self) -> None:
        path = filedialog.askdirectory(
            initialdir=self.site_templates.get() or str(Path.home()),
            title="Dossier des gabarits site (manuel-page.html)",
        )
        if path:
            self.site_templates.set(path)

    def _refresh_fiches(self, registre: str) -> None:
        if self._running:
            return
        if self.source_mode.get() != "pages":
            return
        meta = self._fiche_tabs[registre]
        meta["status"].configure(text="Chargement…")
        meta["button"].configure(state=tk.DISABLED)
        offline = True
        if registre == "arrets":
            # Respecte la case MAJ BdD même si d'autres registres sont aussi sélectionnés
            offline = not self.arrets_refresh.get()

        def worker() -> None:
            try:
                from .catalog import list_fiches

                entries = list_fiches(registre, offline_arrets=offline)
                self.after(
                    0,
                    lambda r=registre, ent=entries: self._apply_fiche_list(r, ent, None),
                )
            except Exception as e:
                err = str(e)
                self.after(
                    0,
                    lambda r=registre, msg=err: self._apply_fiche_list(r, [], msg),
                )

        threading.Thread(target=worker, daemon=True).start()

    def _apply_fiche_list(self, registre: str, entries: list, error: str | None) -> None:
        meta = self._fiche_tabs[registre]
        btn_state = tk.NORMAL if self.source_mode.get() == "pages" else tk.DISABLED
        meta["button"].configure(state=btn_state)
        meta["all_entries"] = list(entries or [])
        if error:
            meta["entries"] = []
            meta["listbox"].delete(0, tk.END)
            meta["status"].configure(text=f"Erreur : {error}")
            return
        self._apply_fiche_filter(registre)

    def _apply_fiche_filter(self, registre: str) -> None:
        """Filtre la listbox sur le texte saisi (libellé + id), sans recharger Notion."""
        meta = self._fiche_tabs.get(registre)
        if not meta:
            return
        all_entries = meta.get("all_entries") or []
        needle = (meta["filter_var"].get() or "").strip().casefold()
        if needle:
            visible = [
                e
                for e in all_entries
                if needle in (e.label or "").casefold()
                or needle in (e.id or "").casefold().replace("-", "")
            ]
        else:
            visible = list(all_entries)

        # Conserver la sélection si encore visible
        lb: tk.Listbox = meta["listbox"]
        prev = meta.get("entries") or []
        selected_ids = set()
        for idx in lb.curselection():
            if 0 <= idx < len(prev):
                selected_ids.add(prev[idx].id)

        lb.delete(0, tk.END)
        meta["entries"] = visible
        for e in visible:
            lb.insert(tk.END, e.label)
            if e.id in selected_ids:
                lb.selection_set(lb.size() - 1)

        total = len(all_entries)
        shown = len(visible)
        if needle:
            meta["status"].configure(
                text=f"{shown}/{total} fiche(s) — filtre « {meta['filter_var'].get().strip()} »"
            )
        else:
            meta["status"].configure(
                text=f"{total} fiche(s) — Ctrl/Maj pour multi-sélection"
                if total
                else "—"
            )
        self._sync_options()

    def _browse_out(self) -> None:
        path = filedialog.askdirectory(
            initialdir=self.out.get() or str(DEFAULT_OUT), title="Dossier de sortie"
        )
        if path:
            self.out.set(path)

    def _open_out(self) -> None:
        path = Path(self.out.get().strip() or DEFAULT_OUT)
        path.mkdir(parents=True, exist_ok=True)
        _os_start(path)

    def _open_master(self) -> None:
        path = master_styles_path()
        if not path.exists():
            messagebox.showwarning(
                "Master manquant",
                f"Introuvable :\n{path}\n\nModèle : extract/templates/Editions_Particulieres.dotx",
            )
            return
        # .dotx : le verbe par défaut Windows = « Nouveau » (crée un .docx).
        # Il faut le verbe « open » pour éditer le modèle lui-même.
        _os_start_template(path)

    def _append_log(self, text: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _drain_log(self) -> None:
        try:
            while True:
                item = self._log_q.get_nowait()
                if item is None:
                    self._set_running(False)
                    self.status.configure(text="Terminé")
                else:
                    self._append_log(item)
        except queue.Empty:
            pass
        self.after(80, self._drain_log)

    def _set_running(self, running: bool) -> None:
        self._running = running
        # Garder state=NORMAL : sous Windows, DISABLED grise le fond et masque les couleurs.
        if running:
            self.btn_run.configure(
                bg=self._run_bg_busy,
                activebackground=self._run_bg_busy,
                cursor="watch",
            )
        else:
            self.btn_run.configure(
                bg=self._run_bg_ready,
                activebackground="#26683c",
                cursor="hand2",
            )
        self.btn_stop.configure(state=tk.NORMAL if running else tk.DISABLED)

    def _on_run(self) -> None:
        if self._running:
            return

        pages_mode = self.source_mode.get() == "pages"
        pages_by_reg: dict[str, list[str]] = {}
        if pages_mode:
            pages_by_reg = self._pages_by_registre()
            free_pages = parse_lines_safe(self.pages_text.get("1.0", tk.END))
            if not pages_by_reg and not free_pages:
                messagebox.showwarning(
                    "Fiches",
                    "Sélectionnez au moins une fiche (liste ou saisie libre).",
                )
                return
            registres = self._registres_for_pages_mode()
            autres_text = ""
            pages_text = "\n".join(free_pages)
            has_juri = "arrets" in registres
            only_juri = registres == ["arrets"]
        else:
            registres = self._selected_registres()
            autres_text = self.autres_text.get("1.0", tk.END)
            pages_text = ""
            has_juri = "arrets" in registres
            only_juri = registres == ["arrets"] and not self._has_autres()

        req, err = build_request(
            registres=registres,
            autres_text=autres_text,
            pages_text=pages_text,
            combine=self.combine.get(),
            name=self.name.get(),
            limit=self.limit.get(),
            out=self.out.get(),
            arrets_refresh=self.arrets_refresh.get() if has_juri else True,
            arrets_a5=only_juri and self.arrets_fmt.get() == "a5",
            pages_by_registre=pages_by_reg if pages_mode else None,
            format=self.out_format.get(),
            site_templates=self.site_templates.get(),
            also_pdf=self.also_pdf.get() and self.out_format.get() != "html",
        )
        if err or req is None:
            messagebox.showwarning("Options", err or "Requête invalide")
            return

        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)
        self._cancel.clear()
        self._set_running(True)
        self.status.configure(text="En cours…")
        self._append_log(f"Master : {master_styles_path()}\n")
        self._append_log(f"Sortie : {req.out}\n\n")

        def worker() -> None:
            try:
                from .pipeline import run_pipeline

                def log(msg: str) -> None:
                    self._log_q.put(msg)

                req.log = log
                req.cancel = self._cancel.is_set
                code, paths = run_pipeline(req)
                if self._cancel.is_set():
                    self._log_q.put("\nAnnulé.\n")
                elif code == 0:
                    self._log_q.put(f"\nSuccès — {len(paths)} fichier(s).\n")
                else:
                    self._log_q.put(f"\nTerminé avec erreurs (code {code}).\n")
            except Exception as e:
                self._log_q.put(f"\nErreur : {e}\n")
            finally:
                self._log_q.put(None)

        threading.Thread(target=worker, daemon=True).start()

    def _on_postlink(self) -> None:
        if self._running:
            return
        self._run_cmd_async(postlink_cmdline(resolve_python(), Path(self.out.get().strip() or DEFAULT_OUT)), "Postlink")

    def _on_attach(self) -> None:
        if self._running:
            return
        master = master_styles_path()
        if not master.exists():
            messagebox.showwarning("Master manquant", str(master))
            return
        out = Path(self.out.get().strip() or DEFAULT_OUT)
        self._run_cmd_async(attach_styles_cmdline(resolve_python(), out), "Attacher styles")

    def _on_pdf(self) -> None:
        if self._running:
            return
        out = Path(self.out.get().strip() or DEFAULT_OUT)
        self._run_cmd_async(to_pdf_cmdline(resolve_python(), out), "Convertir en PDF")

    def _run_cmd_async(self, cmd: list[str], label: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)
        self._cancel.clear()
        self._set_running(True)
        self.status.configure(text=f"{label}…")
        self._append_log(f"→ {' '.join(cmd)}\n\n")

        def worker() -> None:
            try:
                code = self._run_cmd(cmd)
                if self._cancel.is_set():
                    self._log_q.put(f"\nAnnulé — {label}.\n")
                else:
                    self._log_q.put(
                        f"\n{'OK' if code == 0 else f'Échec (code {code})'} — {label}.\n"
                    )
            except Exception as e:
                self._log_q.put(f"\nErreur : {e}\n")
            finally:
                self._proc = None
                self._log_q.put(None)

        threading.Thread(target=worker, daemon=True).start()

    def _run_cmd(self, cmd: list[str]) -> int:
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")
        self._proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            if self._cancel.is_set():
                break
            self._log_q.put(line)
        return self._proc.wait()

    def _on_stop(self) -> None:
        self._cancel.set()
        proc = self._proc
        if proc and proc.poll() is None:
            proc.terminate()
        self._log_q.put("\nArrêt demandé…\n")


def parse_lines_safe(text: str) -> list[str]:
    from .runner import parse_lines

    return parse_lines(text)


def _os_start(path: Path) -> None:
    import subprocess as sp
    import sys

    try:
        if hasattr(os, "startfile"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            sp.run(["open", str(path)], check=False)
        else:
            sp.run(["xdg-open", str(path)], check=False)
    except OSError as e:
        messagebox.showerror("Erreur", str(e))


def _os_start_template(path: Path) -> None:
    """Ouvre un .dotx/.dotm pour édition (pas « Nouveau document » depuis le modèle)."""
    import subprocess as sp
    import sys

    path = Path(path).resolve()
    try:
        if sys.platform == "win32":
            # Documents.Open édite le .dotx ; le double-clic / startfile défaut = New → .docx
            try:
                import win32com.client  # type: ignore

                word = win32com.client.Dispatch("Word.Application")
                word.Visible = True
                word.Documents.Open(FileName=str(path))
                return
            except Exception:
                pass
            for candidate in (
                os.environ.get("OFFICE_PATH"),
                r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
                r"C:\Program Files\Microsoft Office\Office16\WINWORD.EXE",
            ):
                if candidate and Path(candidate).is_file():
                    # /f n'existe pas partout ; passer le chemin à Word ouvre le fichier
                    # (contrairement au verbe shell New des .dotx)
                    sp.Popen([candidate, str(path)], close_fds=True)
                    return
            try:
                os.startfile(str(path), "open")  # type: ignore[attr-defined]
                return
            except OSError:
                pass
            raise OSError(
                "Impossible d'ouvrir le .dotx pour édition "
                "(Word COM / WINWORD.EXE introuvables)."
            )
        if sys.platform == "darwin":
            sp.run(["open", str(path)], check=False)
        else:
            sp.run(["xdg-open", str(path)], check=False)
    except OSError as e:
        messagebox.showerror("Erreur", str(e))


def main() -> int:
    NotionExportApp().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
