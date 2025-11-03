# Sistema de Gestão de Estoque e Serviços - Barbearia (OOP Refactor)
# Desenvolvido por João Vitor de Souza Casco
# Refatorado para POO em 30/10/2025
import sqlite3
from tkinter import *
from tkinter import ttk, messagebox
import tkinter as tk
from datetime import datetime, timedelta, date
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


class BarberShopApp:
    """Aplicação principal totalmente encapsulada em POO.
    Elimina variáveis globais, migra funções para métodos e constrói a UI no __init__.
    """

    def __init__(self):
        # Estado e configuração
        self.DB_NAME = 'estoque_barbearia.db'

        # Tipografia base
        self.FONT_BASE = ("Segoe UI", 12)
        self.FONT_TITLE = ("Segoe UI", 18, "bold")
        self.FONT_SUBTITLE = ("Segoe UI", 12)

        # Paleta Dark
        self.COLOR_BG = "#1F1F1F"
        self.COLOR_CARD = "#2C2C2C"
        self.COLOR_GOLD = "#DAA520"
        self.COLOR_GOLD_ACTIVE = "#E5B73B"
        self.COLOR_BLUE = "#3B82F6"
        self.COLOR_TEXT = "#FFFFFF"
        self.COLOR_TEXT_SECONDARY = "#B0B0B0"
        self.COLOR_ALERT = "#B91C1C"

        # Paleta Light
        self.LIGHT_BG = "#E8E8E8"
        self.LIGHT_CARD = "#F5F5F5"
        self.LIGHT_BUTTON = "#F2D27A"
        self.LIGHT_BUTTON_ACTIVE = "#EAC45E"
        self.LIGHT_TEXT = "#000000"

        # Inicialização da janela
        self.root = Tk()
        self.root.title("Gestão de Estoque - BARBEARIA")
        self.root.geometry("1280x800")
        self.root.configure(bg=self.COLOR_BG)

        # Banco e tema
        self.setup_db()
        self.apply_dark_theme()

        # Construção da UI
        self.build_top_bar()
        self.build_container()
        self.build_sidebar()
        self.build_notebook()
        self.build_tab_estoque()
        self.build_tab_servicos()
        # Removidas as abas superiores de Movimentações e Fechamento de Caixa
        self.build_status_bar()

        # Dados iniciais
        self._produtos_cache = []
        self.atualizar_listagem()
        self.atualizar_clock()

        # Atalhos
        self.root.bind('<Control-n>', lambda e: self.abrir_janela_cadastro())
        self.root.bind('<F5>', lambda e: self.atualizar_listagem())

    # ===== Banco de Dados =====
    def setup_db(self):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    quantidade REAL NOT NULL,
                    minimo INTEGER NOT NULL,
                    preco_custo REAL DEFAULT 0,
                    preco_venda REAL DEFAULT 0
                )
            ''')
            # Ajusta colunas se necessário
            try:
                cursor.execute("ALTER TABLE produtos ADD COLUMN preco_custo REAL DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE produtos ADD COLUMN preco_venda REAL DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INTEGER PRIMARY KEY,
                    produto_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL,
                    quantidade REAL NOT NULL,
                    preco_unitario REAL NOT NULL,
                    data_hora TEXT NOT NULL,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS servicos (
                    id INTEGER PRIMARY KEY,
                    servico TEXT NOT NULL,
                    valor REAL NOT NULL,
                    barbeiro TEXT NOT NULL,
                    data_hora TEXT NOT NULL
                )
            ''')
            conn.commit()

    def execute_query(self, query, params=()):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

    # ===== Tema e Estilo =====
    def apply_dark_theme(self):
        style = ttk.Style()
        try:
            style.theme_use('vista')
        except tk.TclError:
            style.theme_use('clam')

        style.configure('TNotebook', background=self.COLOR_BG)
        style.configure('TNotebook.Tab', padding=(14, 10), font=("Segoe UI", 12, "bold"),
                        background=self.COLOR_CARD, foreground=self.COLOR_TEXT_SECONDARY)
        style.map('TNotebook.Tab',
                  background=[('selected', self.COLOR_BG)],
                  foreground=[('selected', self.COLOR_GOLD)])

        # Treeview dark
        style.configure('Treeview',
                        background=self.COLOR_BG,
                        fieldbackground=self.COLOR_BG,
                        foreground=self.COLOR_TEXT,
                        rowheight=28,
                        font=("Segoe UI", 12, "bold"))
        style.configure('Treeview.Heading',
                        background=self.COLOR_GOLD,
                        foreground='#000000',
                        font=("Segoe UI", 12, "bold"))
        style.map('Treeview', background=[('selected', self.COLOR_BLUE)])

        # Variante clara para a aba de Estoque
        style.configure('Light.Treeview',
                        background='#FFFFFF',
                        fieldbackground='#FFFFFF',
                        foreground='#000000',
                        rowheight=28,
                        font=("Segoe UI", 12, "bold"))
        style.configure('Light.Treeview.Heading',
                        background=self.COLOR_GOLD,
                        foreground='#000000',
                        font=("Segoe UI", 12, "bold"))
        style.map('Light.Treeview', background=[('selected', '#BBD4F2')], foreground=[('selected', '#000000')])

        style.configure('Primary.TButton',
                        background=self.COLOR_GOLD,
                        foreground='#000000',
                        padding=10,
                        font=("Segoe UI", 12, "bold"))
        style.map('Primary.TButton', background=[('active', self.COLOR_GOLD_ACTIVE)])

        style.configure('Secondary.TButton',
                        background=self.COLOR_BLUE,
                        foreground='#FFFFFF',
                        padding=10,
                        font=("Segoe UI", 12, "bold"))
        style.map('Secondary.TButton', background=[('active', '#2563EB')])

    def estilizar_botao(self, botao, variante='primary'):
        if isinstance(botao, ttk.Button):
            botao.configure(style='Primary.TButton' if variante == 'primary' else 'Secondary.TButton', cursor='hand2')
        elif isinstance(botao, Button):
            if variante == 'primary':
                botao.configure(bg=self.COLOR_GOLD, fg='#000000', activebackground=self.COLOR_GOLD_ACTIVE,
                                relief='flat', bd=0, font=self.FONT_BASE, cursor='hand2')
            else:
                botao.configure(bg=self.COLOR_BLUE, fg='#FFFFFF', activebackground='#2563EB',
                                relief='flat', bd=0, font=self.FONT_BASE, cursor='hand2')

    # ===== Construção da UI =====
    def build_top_bar(self):
        self.top_bar = Frame(self.root, bg=self.COLOR_BG)
        self.top_bar.pack(fill='x', pady=10)
        self.logo_label = None
        try:
            import os
            logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
            if Image and ImageTk and os.path.exists(logo_path):
                img = Image.open(logo_path).resize((120, 120))
                logo_img = ImageTk.PhotoImage(img)
                self.logo_label = Label(self.top_bar, image=logo_img, bg=self.COLOR_BG)
                self.logo_label.image = logo_img
                self.logo_label.pack(pady=5)
        except Exception:
            pass
        Label(self.top_bar, text='Barbearia — Gestão', bg=self.COLOR_BG, fg=self.COLOR_GOLD, font=self.FONT_TITLE).pack()
        Label(self.top_bar, text='Estoque, Serviços e Caixa', bg=self.COLOR_BG, fg=self.COLOR_TEXT_SECONDARY, font=self.FONT_SUBTITLE).pack()

    def build_container(self):
        self.container = Frame(self.root, bg=self.COLOR_BG)
        self.container.pack(pady=10, padx=10, fill="both", expand=True)

    def build_sidebar(self):
        self.sidebar = Frame(self.container, bg=self.COLOR_BG)
        self.sidebar.pack(side="left", fill="y")
        Label(self.sidebar, text="Menu", bg=self.COLOR_BG, fg=self.COLOR_TEXT, font=("Segoe UI", 12, "bold")).pack(anchor='w', padx=10, pady=(0,8))
        self.criar_tile(self.sidebar, "Novo Produto", "➕", self.abrir_janela_cadastro)
        self.criar_tile(self.sidebar, "Entrada de Estoque", "⬆", lambda: self.abrir_janela_movimentacao("ENTRADA"))
        self.criar_tile(self.sidebar, "Saída de Estoque", "⬇", lambda: self.abrir_janela_movimentacao("SAÍDA"))
        self.criar_tile(self.sidebar, "Definir Preços", "💲", self.abrir_janela_precos)
        self.criar_tile(self.sidebar, "Fechamento de Caixa", "🧾", self.abrir_janela_fechamento_caixa)

    def build_notebook(self):
        self.notebook = ttk.Notebook(self.container)
        self.notebook.pack(side="left", padx=10, fill="both", expand=True)

    def add_tab_header(self, parent, titulo, subtitulo):
        hdr = Frame(parent, bg=self.COLOR_BG)
        hdr.pack(fill='x', pady=10)
        Label(hdr, text=titulo, bg=self.COLOR_BG, fg=self.COLOR_GOLD, font=self.FONT_TITLE).pack()
        Label(hdr, text=subtitulo, bg=self.COLOR_BG, fg=self.COLOR_TEXT_SECONDARY, font=self.FONT_SUBTITLE).pack()

    def criar_tile(self, parent, titulo, icone_texto, on_click):
        tile_bg = self.COLOR_CARD
        tile_bg_hover = '#3A3A3A'
        frame = Frame(parent, bg=tile_bg, bd=0, relief='flat')
        frame.pack(pady=6, padx=8, anchor='w', fill='x')
        frame.configure(width=220, height=80)
        frame.pack_propagate(False)

        icone = Label(frame, text=icone_texto, bg=tile_bg, fg=self.COLOR_GOLD, font=("Segoe UI", 18, "bold"))
        icone.pack(pady=(10,0))
        titulo_lbl = Label(frame, text=titulo, bg=tile_bg, fg=self.COLOR_TEXT, font=("Segoe UI", 12, "bold"))
        titulo_lbl.pack(pady=(2,10))

        def enter(_):
            frame.configure(bg=tile_bg_hover)
            icone.configure(bg=tile_bg_hover)
            titulo_lbl.configure(bg=tile_bg_hover)
        def leave(_):
            frame.configure(bg=tile_bg)
            icone.configure(bg=tile_bg)
            titulo_lbl.configure(bg=tile_bg)
        def click(_):
            if callable(on_click):
                on_click()
        for w in (frame, icone, titulo_lbl):
            w.bind('<Enter>', enter)
            w.bind('<Leave>', leave)
            w.bind('<Button-1>', click)
            w.configure(cursor='hand2')
        return frame

    # ===== Abas =====
    def build_tab_estoque(self):
        self.frame_tabela = Frame(self.notebook, bg=self.COLOR_BG)
        self.notebook.add(self.frame_tabela, text="Estoque")
        self.add_tab_header(self.frame_tabela, "Estoque 📦", "Produtos e quantidades em estoque")

        colunas = ('ID', 'Produto', 'Categoria', 'Qtd. Atual', 'Qtd. Mínima', 'Preço Custo', 'Preço Venda')
        self.tree = ttk.Treeview(self.frame_tabela, columns=colunas, show='headings', style='Light.Treeview')

        self.tree.column('ID', width=50, anchor=CENTER)
        self.tree.column('Produto', width=250, anchor=W)
        self.tree.column('Categoria', width=120, anchor=CENTER)
        self.tree.column('Qtd. Atual', width=100, anchor=CENTER)
        self.tree.column('Qtd. Mínima', width=100, anchor=CENTER)
        self.tree.column('Preço Custo', width=100, anchor=CENTER)
        self.tree.column('Preço Venda', width=100, anchor=CENTER)
        for col in colunas:
            self.tree.heading(col, text=col)

        # Tags
        self.tree.tag_configure('odd', background='#FFFFFF')
        self.tree.tag_configure('even', background='#F5F5F5')
        self.tree.tag_configure('alerta', background='#FFE4E6')

        # Frame para busca e botões
        frame_controles = Frame(self.frame_tabela, bg=self.COLOR_BG)
        frame_controles.pack(fill='x', pady=5)
        
        Label(frame_controles, text="Buscar Produto:", bg=self.COLOR_BG, fg=self.COLOR_TEXT).pack(side='left', padx=5)
        self.search_entry = Entry(frame_controles, bg='white', fg='black', insertbackground='black')
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', self.filtrar_produtos)
        
        # Botão de exclusão
        btn_excluir = ttk.Button(frame_controles, text="🗑️ Excluir Produto", command=self.excluir_produto_selecionado)
        self.estilizar_botao(btn_excluir, 'primary')  # Alterado para primary que usa fonte preta
        btn_excluir.pack(side='right', padx=10)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(self.frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def build_tab_servicos(self):
        self.tab_servico = Frame(self.notebook, bg=self.COLOR_BG)
        self.notebook.add(self.tab_servico, text="Serviços")
        self.add_tab_header(self.tab_servico, "Registrar Serviços 💈", "Escolha o barbeiro e o serviço")

        tabela_precos = {
            "BARBA": 30,
            "BIGODE": 10,
            "CORTE": 40,
            "CABELO E ALISAMENTO": 80,
            "CABELO E BARBA": 60,
            "LUZES": 150,
            "PLATINADO": 200,
            "SOBRANCELHA": 10
        }

        servicos_notebook = ttk.Notebook(self.tab_servico)
        servicos_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        tab_b1 = Frame(servicos_notebook, bg=self.COLOR_BG)
        tab_b2 = Frame(servicos_notebook, bg=self.COLOR_BG)
        servicos_notebook.add(tab_b1, text="Barbeiro 1")
        servicos_notebook.add(tab_b2, text="Barbeiro 2")

        def montar_form_servico(parent, barbeiro_nome):
            Label(parent, text="Serviço:", bg=self.COLOR_BG, fg=self.COLOR_TEXT, font=self.FONT_BASE).pack(pady=10)
            servico_var = StringVar(value=list(tabela_precos.keys())[0])
            servico_combo = ttk.Combobox(parent, values=list(tabela_precos.keys()), textvariable=servico_var, state="readonly")
            servico_combo.pack(pady=5)

            Label(parent, text="Valor (R$):", bg=self.COLOR_BG, fg=self.COLOR_TEXT, font=self.FONT_BASE).pack(pady=10)
            valor_var = StringVar()
            valor_entry = ttk.Entry(parent, textvariable=valor_var, state='readonly')
            valor_entry.pack(pady=5)

            def atualizar_valor(_):
                s = servico_var.get()
                if s in tabela_precos:
                    valor_var.set(str(tabela_precos[s]))
            atualizar_valor(None)
            servico_combo.bind("<<ComboboxSelected>>", atualizar_valor)

            def salvar_servico():
                if self.registrar_servico(servico_var.get().title(), valor_var.get(), barbeiro_nome):
                    messagebox.showinfo("Sucesso", "Serviço registrado com sucesso!")
            btn_salvar = ttk.Button(parent, text="💾 Salvar", command=salvar_servico)
            self.estilizar_botao(btn_salvar, 'primary')
            btn_salvar.pack(pady=12)

        montar_form_servico(tab_b1, "Barbeiro 1")
        montar_form_servico(tab_b2, "Barbeiro 2")

    def build_tab_movimentacoes(self):
        tab_mov = Frame(self.notebook, bg=self.COLOR_BG)
        self.notebook.add(tab_mov, text="Movimentações")
        self.add_tab_header(tab_mov, "Movimentações 🔄", "Entrada e saída de estoque")
        Label(tab_mov, text="Use os botões laterais para registrar movimentações.", bg=self.COLOR_BG, fg=self.COLOR_TEXT_SECONDARY, font=self.FONT_BASE).pack(pady=10)

    def build_tab_caixa_placeholder(self):
        tab_caixa = Frame(self.notebook, bg=self.COLOR_BG)
        self.notebook.add(tab_caixa, text="Fechamento de Caixa")
        self.add_tab_header(tab_caixa, "Fechamento de Caixa 🧾", "Relatórios por período")
        Label(tab_caixa, text="Use o botão lateral para abrir o fechamento de caixa.", bg=self.COLOR_BG, fg=self.COLOR_TEXT_SECONDARY, font=self.FONT_BASE).pack(pady=10)

    def build_status_bar(self):
        self.status_bar = Frame(self.root, bg=self.COLOR_BG)
        self.status_bar.pack(fill='x', padx=10, pady=10)
        self.status_label = Label(self.status_bar, text="", bg=self.COLOR_BG, fg=self.COLOR_TEXT_SECONDARY, font=self.FONT_BASE)
        self.status_label.pack()

    # ===== Lógica de Estoque =====
    def atualizar_listagem(self):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome, categoria, quantidade, minimo, preco_custo, preco_venda FROM produtos ORDER BY categoria, nome")
            self._produtos_cache = cursor.fetchall()
        self._insert_rows(self._produtos_cache)

    def _insert_rows(self, rows):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.tree.tag_configure('alerta', background='#ffcccc')
        self.tree.tag_configure('odd', background='#f0f0f0')
        self.tree.tag_configure('even', background='#ffffff')
        for idx, registro in enumerate(rows):
            (idp, nome, categoria, quantidade, minimo, preco_custo, preco_venda) = registro
            tags = []
            if quantidade < minimo:
                tags.append('alerta')
            tags.append('odd' if idx % 2 == 1 else 'even')
            display_nome = ("⚠️ " + str(nome)) if quantidade < minimo else str(nome)
            nome_up = display_nome.upper()
            categoria_up = str(categoria).upper()
            self.tree.insert('', 'end', values=(idp, nome_up, categoria_up, quantidade, minimo, preco_custo, preco_venda), tags=tuple(tags))

    def excluir_produto_selecionado(self):
        # Verificar se há um item selecionado
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione um produto para excluir.")
            return
        
        # Obter dados do produto selecionado
        item = self.tree.item(selecionado)
        valores = item['values']
        if not valores:
            return
            
        id_produto = valores[0]
        nome_produto = valores[1]
        quantidade = valores[3]
        
        # Verificar se o estoque está zerado
        if quantidade == 0:
            resposta = messagebox.askyesno("Confirmação", 
                f"O produto '{nome_produto}' está sem estoque, deseja excluir?")
        else:
            # Mensagem de confirmação padrão
            resposta = messagebox.askyesno("Confirmação", 
                f"Deseja excluir o produto '{nome_produto}'?\n\nQuantidade em estoque: {quantidade}")
        
        # Se confirmado, excluir o produto
        if resposta:
            try:
                with sqlite3.connect(self.DB_NAME) as conn:
                    cursor = conn.cursor()
                    # Excluir movimentações relacionadas ao produto
                    cursor.execute("DELETE FROM movimentacoes WHERE produto_id = ?", (id_produto,))
                    # Excluir o produto
                    cursor.execute("DELETE FROM produtos WHERE id = ?", (id_produto,))
                    conn.commit()
                    
                messagebox.showinfo("Sucesso", f"Produto '{nome_produto}' excluído com sucesso!")
                self.atualizar_listagem()
            except sqlite3.Error as e:
                messagebox.showerror("Erro", f"Erro ao excluir produto: {str(e)}")
    
    def adicionar_produto(self, nome, categoria, quantidade, minimo):
        if not nome or not categoria:
            messagebox.showerror("Erro de Validação", "Nome e categoria não podem estar vazios.")
            return
        try:
            if not all(c.isdigit() or c == '.' for c in quantidade.strip()):
                messagebox.showerror("Erro de Validação", "Quantidade deve conter apenas números e ponto decimal.")
                return
            if not all(c.isdigit() for c in minimo.strip()):
                messagebox.showerror("Erro de Validação", "Estoque mínimo deve conter apenas números inteiros.")
                return
            quantidade = float(quantidade)
            minimo = int(minimo)
            if quantidade < 0 or minimo < 0:
                messagebox.showerror("Erro de Validação", "Valores não podem ser negativos.")
                return
            self.execute_query(
                "INSERT INTO produtos (nome, categoria, quantidade, minimo, preco_custo, preco_venda) VALUES (?, ?, ?, ?, 0, 0)",
                (nome, categoria, quantidade, minimo)
            )
            messagebox.showinfo("Sucesso", f"Produto '{nome}' cadastrado com sucesso!")
            self.atualizar_listagem()
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Quantidade e Estoque Mínimo devem ser números válidos.")

    def abrir_janela_cadastro(self):
        janela_c = Toplevel(self.root)
        janela_c.title("Cadastrar Produto")
        janela_c.geometry("600x500")
        janela_c.configure(bg=self.LIGHT_BG)
        form = Frame(janela_c, bg=self.LIGHT_BG)
        form.pack(pady=10, padx=12, fill='both', expand=True)
        Label(form, text="Nome:", bg=self.LIGHT_BG, fg=self.LIGHT_TEXT).grid(row=0, column=0, sticky='e', padx=8, pady=10)
        nome_e = Entry(form, bg=self.LIGHT_CARD, fg=self.LIGHT_TEXT, insertbackground=self.LIGHT_TEXT)
        nome_e.grid(row=0, column=1, sticky='w', padx=8, pady=10)
        Label(form, text="Categoria:", bg=self.LIGHT_BG, fg=self.LIGHT_TEXT).grid(row=1, column=0, sticky='e', padx=8, pady=10)
        categoria_e = ttk.Combobox(form, values=["Pomada", "Shampoo", "Frigobar", "Outro Insumo"], state="readonly")
        categoria_e.grid(row=1, column=1, sticky='w', padx=8, pady=10)
        categoria_e.current(0)
        Label(form, text="Qtd. Inicial:", bg=self.LIGHT_BG, fg=self.LIGHT_TEXT).grid(row=2, column=0, sticky='e', padx=8, pady=10)
        qtd_e = Entry(form, bg=self.LIGHT_CARD, fg=self.LIGHT_TEXT, insertbackground=self.LIGHT_TEXT)
        qtd_e.insert(0, "0")
        qtd_e.grid(row=2, column=1, sticky='w', padx=8, pady=10)
        Label(form, text="Qtd. Mínima:", bg=self.LIGHT_BG, fg=self.LIGHT_TEXT).grid(row=3, column=0, sticky='e', padx=8, pady=10)
        min_e = Entry(form, bg=self.LIGHT_CARD, fg=self.LIGHT_TEXT, insertbackground=self.LIGHT_TEXT)
        min_e.insert(0, "0")
        min_e.grid(row=3, column=1, sticky='w', padx=8, pady=10)
        btn_cadastrar = Button(janela_c, text="➕ Cadastrar",
                               bg=self.LIGHT_BUTTON, fg=self.LIGHT_TEXT,
                               activebackground=self.LIGHT_BUTTON_ACTIVE,
                               command=lambda: self.adicionar_produto(nome_e.get(), categoria_e.get(), qtd_e.get(), min_e.get()))
        btn_cadastrar.pack(pady=10)

    def abrir_janela_precos(self):
        if not self.tree.selection():
            messagebox.showwarning("Atenção", "Selecione um produto na lista primeiro.")
            return
        item = self.tree.item(self.tree.focus())
        produto_id = item['values'][0]
        nome_produto = item['values'][1]
        preco_custo_atual = item['values'][5] if len(item['values']) > 5 else 0
        preco_venda_atual = item['values'][6] if len(item['values']) > 6 else 0
        janela_p = Toplevel(self.root)
        janela_p.title(f"Definir Preços: {nome_produto}")
        janela_p.geometry("600x420")
        janela_p.configure(bg=self.LIGHT_BG)
        Label(janela_p, text=f"Produto: {nome_produto}", bg=self.LIGHT_BG, fg=self.LIGHT_TEXT).pack(pady=12, padx=12)
        Label(janela_p, text="Preço de Custo (R$):", bg=self.LIGHT_BG, fg=self.LIGHT_TEXT).pack(pady=8, padx=12)
        e_custo = Entry(janela_p, bg=self.LIGHT_CARD, fg=self.LIGHT_TEXT, insertbackground=self.LIGHT_TEXT)
        e_custo.insert(0, str(preco_custo_atual))
        e_custo.pack(pady=4, padx=12, ipady=4)
        Label(janela_p, text="Preço de Venda (R$):", bg=self.LIGHT_BG, fg=self.LIGHT_TEXT).pack(pady=8, padx=12)
        e_venda = Entry(janela_p, bg=self.LIGHT_CARD, fg=self.LIGHT_TEXT, insertbackground=self.LIGHT_TEXT)
        e_venda.insert(0, str(preco_venda_atual))
        e_venda.pack(pady=4, padx=12, ipady=4)
        def salvar():
            try:
                custo = float(e_custo.get())
                venda = float(e_venda.get())
                self.execute_query("UPDATE produtos SET preco_custo=?, preco_venda=? WHERE id=?", (custo, venda, produto_id))
                messagebox.showinfo("Sucesso", "Preços atualizados!")
                self.atualizar_listagem()
                janela_p.destroy()
            except:
                messagebox.showerror("Erro", "Valores inválidos de preço.")
        btn_salvar_precos = Button(janela_p, text="Salvar",
                                   bg=self.LIGHT_BUTTON, fg=self.LIGHT_TEXT, activebackground=self.LIGHT_BUTTON_ACTIVE,
                                   command=salvar)
        btn_salvar_precos.pack(pady=14)

    def atualizar_estoque(self, produto_id, delta, tipo_mov=None):
        try:
            if not all(c.isdigit() or c == '.' or c == '-' for c in str(delta).strip()):
                messagebox.showerror("Erro de Validação", "Quantidade deve conter apenas números, ponto decimal ou sinal negativo.")
                return
            delta = float(delta)
            with sqlite3.connect(self.DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT quantidade, nome, preco_custo, preco_venda, minimo FROM produtos WHERE id=?", (produto_id,))
                resultado = cursor.fetchone()
            quantidade_atual, nome_produto, preco_custo_atual, preco_venda_atual, minimo_produto = resultado
            nova_quantidade = quantidade_atual + delta
            if nova_quantidade < 0:
                messagebox.showwarning("Atenção", "Operação cancelada: A quantidade não pode ser negativa!")
                return
            self.execute_query("UPDATE produtos SET quantidade = ? WHERE id = ?", (nova_quantidade, produto_id))
            messagebox.showinfo("Sucesso", f"Estoque atualizado. Nova quantidade: {nova_quantidade}")
            if nova_quantidade < minimo_produto:
                nome_produto = "⚠️ " + nome_produto
                messagebox.showwarning("⚠️ ALERTA - Estoque Baixo!",
                                       f"O produto {nome_produto} está com estoque ABAIXO do mínimo configurado!\n"
                                       f"Quantidade atual: {nova_quantidade}\n"
                                       f"Mínimo configurado: {minimo_produto}")
            if tipo_mov:
                preco_unit = preco_custo_atual if tipo_mov == "ENTRADA" else preco_venda_atual
                agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                tipo_norm = "ENTRADA" if tipo_mov == "ENTRADA" else "SAIDA"
                self.execute_query(
                    "INSERT INTO movimentacoes (produto_id, tipo, quantidade, preco_unitario, data_hora) VALUES (?, ?, ?, ?, ?)",
                    (produto_id, tipo_norm, abs(delta), preco_unit, agora)
                )
            self.atualizar_listagem()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao atualizar o estoque: {e}")

    def abrir_janela_movimentacao(self, tipo):
        if not self.tree.selection():
            messagebox.showwarning("Atenção", "Selecione um produto na lista primeiro.")
            return
        item_selecionado = self.tree.item(self.tree.focus())
        produto_id = item_selecionado['values'][0]
        nome_produto = item_selecionado['values'][1]
        janela_m = Toplevel(self.root)
        janela_m.title(f"{tipo} de Estoque: {nome_produto}")
        janela_m.geometry("700x520")
        janela_m.configure(bg=self.LIGHT_BG)
        delta_sinal = 1 if tipo == "ENTRADA" else -1
        form = Frame(janela_m, bg=self.LIGHT_BG)
        form.pack(pady=10, padx=12, fill='both', expand=True)
        Label(form, text=f"Produto:", bg=self.LIGHT_BG, fg=self.LIGHT_TEXT).grid(row=0, column=0, sticky='e', padx=8, pady=10)
        Label(form, text=f"{nome_produto}", bg=self.LIGHT_BG, fg=self.LIGHT_TEXT).grid(row=0, column=1, sticky='w', padx=8, pady=10)
        Label(form, text=f"Quantidade para {tipo}:", bg=self.LIGHT_BG, fg=self.LIGHT_TEXT).grid(row=1, column=0, sticky='e', padx=8, pady=10)
        qtd_m = Entry(form, bg=self.LIGHT_CARD, fg=self.LIGHT_TEXT, insertbackground=self.LIGHT_TEXT)
        qtd_m.insert(0, "1")
        qtd_m.grid(row=1, column=1, sticky='w', padx=8, pady=10)
        btn_confirmar = Button(janela_m, text=("⬆ ENTRADA" if tipo == "ENTRADA" else "⬇ SAÍDA"),
                               command=lambda: [
                                   self.atualizar_estoque(
                                       produto_id,
                                       float(qtd_m.get()) * delta_sinal,
                                       tipo_mov=("ENTRADA" if tipo == "ENTRADA" else "SAIDA")
                                   ),
                                   janela_m.destroy()
                               ])
        btn_confirmar.configure(bg=self.LIGHT_BUTTON, fg=self.LIGHT_TEXT, activebackground=self.LIGHT_BUTTON_ACTIVE)
        btn_confirmar.pack(pady=10)

    def filtrar_produtos(self, event=None):
        termo = self.search_entry.get().lower().strip()
        if not termo:
            # Campo vazio: reexibe todos
            self._insert_rows(self._produtos_cache)
            return
        filtrados = []
        for (idp, nome, categoria, quantidade, minimo, preco_custo, preco_venda) in self._produtos_cache:
            if termo in str(nome).lower():
                filtrados.append((idp, nome, categoria, quantidade, minimo, preco_custo, preco_venda))
        self._insert_rows(filtrados)

    # ===== Serviços =====
    def registrar_servico(self, servico, valor, barbeiro):
        try:
            valor_float = float(valor)
            if valor_float <= 0:
                messagebox.showerror("Erro", "O valor deve ser maior que zero.")
                return False
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_query(
                "INSERT INTO servicos (servico, valor, barbeiro, data_hora) VALUES (?, ?, ?, ?)",
                (servico, valor_float, barbeiro, agora)
            )
            return True
        except ValueError:
            messagebox.showerror("Erro", "Valor deve ser um número válido.")
            return False
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao registrar serviço: {e}")
            return False

    def calcular_resumo_servicos(self, periodo_inicio=None, periodo_fim=None):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            params = []
            filtro_data = ""
            if periodo_inicio and periodo_fim:
                filtro_data = " WHERE datetime(data_hora) BETWEEN datetime(?) AND datetime(?)"
                params.extend([periodo_inicio + " 00:00:00", periodo_fim + " 23:59:59"])
            cursor.execute(
                """
                SELECT servico,
                       COUNT(*) as quantidade,
                       SUM(valor) as total,
                       barbeiro,
                       COUNT(CASE WHEN barbeiro = barbeiro THEN 1 END) as qtd_barbeiro,
                       SUM(CASE WHEN barbeiro = barbeiro THEN valor ELSE 0 END) as total_barbeiro
                FROM servicos
                """ + filtro_data + """
                GROUP BY servico, barbeiro
                ORDER BY servico, barbeiro
                """,
                params
            )
            dados_servicos = cursor.fetchall()
            cursor.execute(
                """
                SELECT SUM(valor) as total_servicos
                FROM servicos
                """ + filtro_data,
                params
            )
            total_servicos = cursor.fetchone()[0] or 0
        return dados_servicos, total_servicos

    # ===== Fechamento de Caixa =====
    def calcular_resumo_caixa(self, periodo_inicio=None, periodo_fim=None, produto_id=None):
        with sqlite3.connect(self.DB_NAME) as conn:
            cursor = conn.cursor()
            params = []
            if periodo_inicio and periodo_fim:
                if produto_id:
                    cursor.execute(
                        """
                        SELECT p.id, p.nome,
                               SUM(CASE WHEN m.tipo='ENTRADA' THEN m.quantidade ELSE 0 END) AS qtd_entrada,
                               SUM(CASE WHEN m.tipo='SAIDA' THEN m.quantidade ELSE 0 END) AS qtd_saida,
                               SUM(CASE WHEN m.tipo='ENTRADA' THEN m.quantidade*m.preco_unitario ELSE 0 END) AS total_compra,
                               SUM(CASE WHEN m.tipo='SAIDA' THEN m.quantidade*m.preco_unitario ELSE 0 END) AS total_venda
                        FROM produtos p
                        LEFT JOIN movimentacoes m ON m.produto_id = p.id
                        WHERE p.id = ? AND datetime(m.data_hora) BETWEEN datetime(?) AND datetime(?)
                        GROUP BY p.id, p.nome
                        ORDER BY p.nome
                        """,
                        [produto_id, periodo_inicio + " 00:00:00", periodo_fim + " 23:59:59"]
                    )
                else:
                    cursor.execute(
                        """
                        SELECT p.id, p.nome,
                               SUM(CASE WHEN m.tipo='ENTRADA' THEN m.quantidade ELSE 0 END) AS qtd_entrada,
                               SUM(CASE WHEN m.tipo='SAIDA' THEN m.quantidade ELSE 0 END) AS qtd_saida,
                               SUM(CASE WHEN m.tipo='ENTRADA' THEN m.quantidade*m.preco_unitario ELSE 0 END) AS total_compra,
                               SUM(CASE WHEN m.tipo='SAIDA' THEN m.quantidade*m.preco_unitario ELSE 0 END) AS total_venda
                        FROM produtos p
                        LEFT JOIN movimentacoes m ON m.produto_id = p.id
                        WHERE datetime(m.data_hora) BETWEEN datetime(?) AND datetime(?)
                        GROUP BY p.id, p.nome
                        ORDER BY p.nome
                        """,
                        [periodo_inicio + " 00:00:00", periodo_fim + " 23:59:59"]
                    )
            else:
                cursor.execute(
                    """
                    SELECT p.id, p.nome,
                           SUM(CASE WHEN m.tipo='ENTRADA' THEN m.quantidade ELSE 0 END) AS qtd_entrada,
                           SUM(CASE WHEN m.tipo='SAIDA' THEN m.quantidade ELSE 0 END) AS qtd_saida,
                           SUM(CASE WHEN m.tipo='ENTRADA' THEN m.quantidade*m.preco_unitario ELSE 0 END) AS total_compra,
                           SUM(CASE WHEN m.tipo='SAIDA' THEN m.quantidade*m.preco_unitario ELSE 0 END) AS total_venda
                    FROM produtos p
                    LEFT JOIN movimentacoes m ON m.produto_id = p.id
                    GROUP BY p.id, p.nome
                    ORDER BY p.nome
                    """
                )
            dados = cursor.fetchall()
        return dados

    def abrir_janela_fechamento_caixa(self):
        janela_f = Toplevel(self.root)
        janela_f.title("Fechamento de Caixa")
        janela_f.geometry("900x600")
        janela_f.configure(bg=self.COLOR_BG)

        frame_style = {'bg': self.COLOR_BG, 'padx': 10, 'pady': 10}
        frame_filtros_rapidos = Frame(janela_f, **frame_style)
        frame_filtros_rapidos.pack(pady=5, fill="x")

        def aplicar_intervalo(inicio, fim):
            e_ini.delete(0, END); e_fim.delete(0, END)
            e_ini.insert(0, inicio); e_fim.insert(0, fim); carregar()

        def aplicar_filtro_hoje():
            hoje = date.today().strftime("%Y-%m-%d")
            aplicar_intervalo(hoje, hoje)
        def aplicar_filtro_ontem():
            ontem = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            aplicar_intervalo(ontem, ontem)
        def aplicar_filtro_mes_atual():
            hoje = date.today()
            primeiro_dia = date(hoje.year, hoje.month, 1).strftime("%Y-%m-%d")
            aplicar_intervalo(primeiro_dia, hoje.strftime("%Y-%m-%d"))
        def aplicar_filtro_mes_anterior():
            hoje = date.today()
            primeiro_dia_mes_anterior = date(hoje.year-1, 12, 1) if hoje.month == 1 else date(hoje.year, hoje.month-1, 1)
            ultimo_dia_mes_anterior = date(hoje.year-1, 12, 31) if hoje.month == 1 else (date(hoje.year, hoje.month, 1) - timedelta(days=1))
            aplicar_intervalo(primeiro_dia_mes_anterior.strftime("%Y-%m-%d"), ultimo_dia_mes_anterior.strftime("%Y-%m-%d"))
        def aplicar_filtro_ultimos_30_dias():
            hoje = date.today(); data_30 = (hoje - timedelta(days=30)).strftime("%Y-%m-%d")
            aplicar_intervalo(data_30, hoje.strftime("%Y-%m-%d"))

        Label(frame_filtros_rapidos, text="Filtros Rápidos:", bg=self.COLOR_BG, fg=self.COLOR_TEXT, font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=8)
        Button(frame_filtros_rapidos, text="Hoje 🗓", command=aplicar_filtro_hoje, bg='white', fg='black', activebackground='#E5E5E5').pack(side=LEFT, padx=6, pady=4)
        Button(frame_filtros_rapidos, text="Ontem 🗓", command=aplicar_filtro_ontem, bg='white', fg='black', activebackground='#E5E5E5').pack(side=LEFT, padx=6, pady=4)
        Button(frame_filtros_rapidos, text="Mês Atual 🗓", command=aplicar_filtro_mes_atual, bg='white', fg='black', activebackground='#E5E5E5').pack(side=LEFT, padx=6, pady=4)
        Button(frame_filtros_rapidos, text="Mês Anterior 🗓", command=aplicar_filtro_mes_anterior, bg='white', fg='black', activebackground='#E5E5E5').pack(side=LEFT, padx=6, pady=4)
        Button(frame_filtros_rapidos, text="Últimos 30 dias 🗓", command=aplicar_filtro_ultimos_30_dias, bg='white', fg='black', activebackground='#E5E5E5').pack(side=LEFT, padx=6, pady=4)

        frame_filtros = Frame(janela_f, **frame_style)
        frame_filtros.pack(pady=5, fill="x")
        Label(frame_filtros, text="Período:", bg=self.COLOR_BG, fg=self.COLOR_TEXT).pack(side=LEFT, padx=5)
        Label(frame_filtros, text="De:", bg=self.COLOR_BG, fg=self.COLOR_TEXT).pack(side=LEFT)
        e_ini = Entry(frame_filtros, width=10, bg='white', fg='black', insertbackground='black'); e_ini.pack(side=LEFT, padx=2)
        e_ini.insert(0, date.today().strftime("%Y-%m-%d"))
        Label(frame_filtros, text="Até:", bg=self.COLOR_BG, fg=self.COLOR_TEXT).pack(side=LEFT)
        e_fim = Entry(frame_filtros, width=10, bg='white', fg='black', insertbackground='black'); e_fim.pack(side=LEFT, padx=2)
        e_fim.insert(0, date.today().strftime("%Y-%m-%d"))

        frame_resultados = Frame(janela_f, **frame_style)
        frame_resultados.pack(pady=10, fill="both", expand=True)

        def carregar():
            for widget in frame_resultados.winfo_children():
                widget.destroy()
            data_ini = e_ini.get(); data_fim = e_fim.get()
            try:
                datetime.strptime(data_ini, "%Y-%m-%d"); datetime.strptime(data_fim, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Erro", "Formato de data inválido. Use AAAA-MM-DD"); return
            dados_produtos = self.calcular_resumo_caixa(data_ini, data_fim)
            dados_servicos, total_servicos = self.calcular_resumo_servicos(data_ini, data_fim)

            frame_produtos = LabelFrame(frame_resultados, text="Movimentação de Produtos", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 11, "bold"))
            frame_produtos.pack(fill="both", expand=True, padx=5, pady=5)
            cols_prod = ('Produto', 'Entradas', 'Saídas', 'Compras (R$)', 'Vendas (R$)', 'Lucro (R$)')
            tree_prod = ttk.Treeview(frame_produtos, columns=cols_prod, show='headings', height=8, style='Treeview')
            for col in cols_prod:
                tree_prod.heading(col, text=col); tree_prod.column(col, width=100, anchor=CENTER)
            tree_prod.column('Produto', width=200, anchor=W)
            total_compras = total_vendas = total_lucro = 0
            for item in dados_produtos:
                pid, nome, q_in, q_out, tot_comp, tot_vend = item
                lucro = tot_vend - tot_comp
                tree_prod.insert('', 'end', values=(nome, q_in, q_out, f"R$ {tot_comp:.2f}", f"R$ {tot_vend:.2f}", f"R$ {lucro:.2f}"))
                total_compras += tot_comp; total_vendas += tot_vend; total_lucro += lucro
            tree_prod.insert('', 'end', values=('TOTAL', '', '', f"R$ {total_compras:.2f}", f"R$ {total_vendas:.2f}", f"R$ {total_lucro:.2f}"))
            tree_prod.pack(fill="both", expand=True, padx=5, pady=5)

            frame_serv = LabelFrame(frame_resultados, text="Serviços Realizados", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 11, "bold"))
            frame_serv.pack(fill="both", expand=True, padx=5, pady=5)
            cols_serv = ('Serviço', 'Qtd', 'Total (R$)', 'Barbeiro', 'Qtd por Barbeiro', 'Total por Barbeiro (R$)')
            tree_serv = ttk.Treeview(frame_serv, columns=cols_serv, show='headings', height=8, style='Treeview')
            for col in cols_serv:
                tree_serv.heading(col, text=col); tree_serv.column(col, width=100, anchor=CENTER)
            tree_serv.column('Serviço', width=150, anchor=W); tree_serv.column('Barbeiro', width=100, anchor=W)
            for item in dados_servicos:
                servico, qtd, total, barbeiro, qtd_b, total_b = item
                tree_serv.insert('', 'end', values=(servico, qtd, f"R$ {total:.2f}", barbeiro, qtd_b, f"R$ {total_b:.2f}"))
            tree_serv.pack(fill="both", expand=True, padx=5, pady=5)

            frame_res = LabelFrame(frame_resultados, text="RESUMO DO PERÍODO", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 11, "bold"))
            frame_res.pack(fill="both", padx=5, pady=5)
            Label(frame_res, text=f"Total em Serviços: R$ {total_servicos:.2f}", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 10)).pack(anchor='w', padx=10, pady=2)
            Label(frame_res, text=f"Total em Produtos: R$ {total_lucro:.2f}", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 10)).pack(anchor='w', padx=10, pady=2)
            Label(frame_res, text=f"Total Geral: R$ {(total_servicos + total_lucro):.2f}", bg=self.COLOR_CARD, fg=self.COLOR_TEXT, font=("Segoe UI", 10, "bold")).pack(anchor='w', padx=10, pady=2)

        btn_carregar = Button(frame_filtros, text="Carregar 🔄", command=carregar, bg='white', fg='black', activebackground='#E5E5E5')
        btn_carregar.pack(side=LEFT, padx=10)
        carregar()

    # ===== Utilidades =====
    def confirm_and_run(self, prompt, action, *args, **kwargs):
        if messagebox.askyesno("Confirmação", prompt):
            return action(*args, **kwargs)
        return False

    def atualizar_clock(self):
        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.status_label.configure(text=f"Pronto • {agora}")
        self.root.after(1000, self.atualizar_clock)

    # ===== Execução =====
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = BarberShopApp()
    app.run()