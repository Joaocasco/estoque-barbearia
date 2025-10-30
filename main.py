# Sistema de Gestão de Estoque e Serviços - Barbearia
# Desenvolvido por João Vitor de Souza Casco
# Atualizado em 30/10/2025
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

# --- 1. Configuração e Funções do Banco de Dados SQLite ---
DB_NAME = 'estoque_barbearia.db'

def setup_db():
    """Cria a tabela de produtos se ela não existir."""
    with sqlite3.connect(DB_NAME) as conn:
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
        # Tenta adicionar colunas se a tabela já existir sem elas
        try:
            cursor.execute("ALTER TABLE produtos ADD COLUMN preco_custo REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE produtos ADD COLUMN preco_venda REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Cria tabela de movimentações
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
        
        # Cria tabela de serviços
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
    

def execute_query(query, params=()):
    """Função genérica para executar comandos SQL com contexto seguro."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

# --- 2. Funções de Manipulação de Estoque ---

def adicionar_produto(nome, categoria, quantidade, minimo):
    """Cadastra um novo produto."""
    # Validação robusta de entrada
    if not nome or not categoria:
        messagebox.showerror("Erro de Validação", "Nome e categoria não podem estar vazios.")
        return
        
    try:
        # Verifica se a string contém apenas dígitos e/ou um ponto decimal
        if not all(c.isdigit() or c == '.' for c in quantidade.strip()):
            messagebox.showerror("Erro de Validação", "Quantidade deve conter apenas números e ponto decimal.")
            return
            
        if not all(c.isdigit() for c in minimo.strip()):
            messagebox.showerror("Erro de Validação", "Estoque mínimo deve conter apenas números inteiros.")
            return
            
        quantidade = float(quantidade)
        minimo = int(minimo)
        
        if quantidade < 0:
            messagebox.showerror("Erro de Validação", "Quantidade não pode ser negativa.")
            return
            
        if minimo < 0:
            messagebox.showerror("Erro de Validação", "Estoque mínimo não pode ser negativo.")
            return
            
        execute_query(
            "INSERT INTO produtos (nome, categoria, quantidade, minimo, preco_custo, preco_venda) VALUES (?, ?, ?, ?, 0, 0)",
            (nome, categoria, quantidade, minimo)
        )
        messagebox.showinfo("Sucesso", f"Produto '{nome}' cadastrado com sucesso!")
        atualizar_listagem()
    except ValueError:
        messagebox.showerror("Erro de Entrada", "Quantidade e Estoque Mínimo devem ser números válidos.")

def atualizar_estoque(produto_id, delta, tipo_mov=None):
    """Aumenta ou diminui a quantidade de um produto, registrando movimentação com preço automático."""
    try:
        # Validação robusta da entrada
        if not all(c.isdigit() or c == '.' or c == '-' for c in str(delta).strip()):
            messagebox.showerror("Erro de Validação", "Quantidade deve conter apenas números, ponto decimal ou sinal negativo.")
            return
            
        delta = float(delta)
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT quantidade, nome, preco_custo, preco_venda, minimo FROM produtos WHERE id=?", (produto_id,))
            resultado = cursor.fetchone()
        quantidade_atual = resultado[0]
        nome_produto = resultado[1]
        preco_custo_atual = resultado[2]
        preco_venda_atual = resultado[3]
        minimo_produto = resultado[4]
        

        nova_quantidade = quantidade_atual + delta

        if nova_quantidade < 0:
            messagebox.showwarning("Atenção", "Operação cancelada: A quantidade não pode ser negativa!")
            return

        execute_query(
            "UPDATE produtos SET quantidade = ? WHERE id = ?",
            (nova_quantidade, produto_id)
        )

        messagebox.showinfo("Sucesso", f"Estoque atualizado. Nova quantidade: {nova_quantidade}")

        # Alerta baseado no mínimo do produto
        if nova_quantidade < minimo_produto:
            # Prefixa emoji no nome para feedback visual
            nome_produto = "⚠️ " + nome_produto
            # Melhor feedback visual com tags de alerta
            messagebox.showwarning("⚠️ ALERTA - Estoque Baixo!",
                                f"O produto {nome_produto} está com estoque ABAIXO do mínimo configurado!\n"
                                f"Quantidade atual: {nova_quantidade}\n"
                                f"Mínimo configurado: {minimo_produto}\n"
                                f"Recomenda-se repor o estoque urgentemente.")

        # registra movimentação se tipo informado
        if tipo_mov:
            preco_unit = preco_custo_atual if tipo_mov == "ENTRADA" else preco_venda_atual
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tipo_norm = "ENTRADA" if tipo_mov == "ENTRADA" else "SAIDA"
            execute_query(
                "INSERT INTO movimentacoes (produto_id, tipo, quantidade, preco_unitario, data_hora) VALUES (?, ?, ?, ?, ?)",
                (produto_id, tipo_norm, abs(delta), preco_unit, agora)
            )

        atualizar_listagem()

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao atualizar o estoque: {e}")

# --- Funções para Serviços ---

def registrar_servico(servico, valor, barbeiro):
    """Registra um novo serviço no banco de dados."""
    try:
        valor_float = float(valor)
        if valor_float <= 0:
            messagebox.showerror("Erro", "O valor deve ser maior que zero.")
            return False
        
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execute_query(
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

def abrir_janela_servico():
    # Seleciona a aba "Registrar Serviço" em vez de abrir Toplevel
    notebook.select(tab_servico)

def calcular_resumo_servicos(periodo_inicio=None, periodo_fim=None):
    """Retorna estatísticas dos serviços no período especificado."""
    with sqlite3.connect(DB_NAME) as conn:
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

# --- 3. Funções da Interface Gráfica (Tkinter) ---

def atualizar_listagem():
    """Limpa e preenche a Treeview com os dados atualizados do banco."""
    for i in tree.get_children():
        tree.delete(i)

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, categoria, quantidade, minimo, preco_custo, preco_venda FROM produtos ORDER BY categoria, nome")
        registros = cursor.fetchall()

    # Configurando as tags para melhor feedback visual
    tree.tag_configure('alerta', background='#ffcccc')  # Vermelho claro para alerta
    tree.tag_configure('odd', background='#f0f0f0')     # Cinza claro para linhas ímpares
    tree.tag_configure('even', background='#ffffff')    # Branco para linhas pares

    for idx, registro in enumerate(registros):
        (id, nome, categoria, quantidade, minimo, preco_custo, preco_venda) = registro
        tags = []
        # Usando o mínimo do produto para determinar o alerta
        if quantidade < minimo:
            tags.append('alerta')
        tags.append('odd' if idx % 2 == 1 else 'even')
        # Exibir texto em MAIÚSCULAS e negrito (negrito via estilo da Treeview)
        display_nome = ("⚠️ " + str(nome)) if quantidade < minimo else str(nome)
        nome_up = display_nome.upper()
        categoria_up = str(categoria).upper()
        tree.insert('', 'end', values=(id, nome_up, categoria_up, quantidade, minimo, preco_custo, preco_venda), tags=tuple(tags))

def abrir_janela_cadastro():
    """Abre a janela para cadastrar um novo produto."""
    janela_c = Toplevel(root)
    janela_c.title("Cadastrar Produto")
    janela_c.geometry("600x500")
    janela_c.configure(bg=LIGHT_BG)

    form = Frame(janela_c, bg=LIGHT_BG)
    form.pack(pady=10, padx=12, fill='both', expand=True)

    Label(form, text="Nome:", bg=LIGHT_BG, fg=LIGHT_TEXT).grid(row=0, column=0, sticky='e', padx=8, pady=10)
    nome_e = Entry(form, bg=LIGHT_CARD, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
    nome_e.grid(row=0, column=1, sticky='w', padx=8, pady=10)

    Label(form, text="Categoria:", bg=LIGHT_BG, fg=LIGHT_TEXT).grid(row=1, column=0, sticky='e', padx=8, pady=10)
    categoria_e = ttk.Combobox(form, values=["Pomada", "Shampoo", "Frigobar", "Outro Insumo"], state="readonly")
    categoria_e.grid(row=1, column=1, sticky='w', padx=8, pady=10)
    categoria_e.current(0)

    Label(form, text="Qtd. Inicial:", bg=LIGHT_BG, fg=LIGHT_TEXT).grid(row=2, column=0, sticky='e', padx=8, pady=10)
    qtd_e = Entry(form, bg=LIGHT_CARD, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
    qtd_e.insert(0, "0")
    qtd_e.grid(row=2, column=1, sticky='w', padx=8, pady=10)

    Label(form, text="Qtd. Mínima:", bg=LIGHT_BG, fg=LIGHT_TEXT).grid(row=3, column=0, sticky='e', padx=8, pady=10)
    min_e = Entry(form, bg=LIGHT_CARD, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
    min_e.insert(0, "0")
    min_e.grid(row=3, column=1, sticky='w', padx=8, pady=10)

    btn_cadastrar = Button(janela_c, text="➕ Cadastrar",
           bg=LIGHT_BUTTON, fg=LIGHT_TEXT,
           activebackground=LIGHT_BUTTON_ACTIVE,
           command=lambda: adicionar_produto(nome_e.get(), categoria_e.get(), qtd_e.get(), min_e.get()))
    btn_cadastrar.pack(pady=10)

def abrir_janela_precos():
    """Abre janela para definir preço de custo e venda do produto selecionado."""
    if not tree.selection():
        messagebox.showwarning("Atenção", "Selecione um produto na lista primeiro.")
        return

    item = tree.item(tree.focus())
    produto_id = item['values'][0]
    nome_produto = item['values'][1]
    preco_custo_atual = item['values'][5] if len(item['values']) > 5 else 0
    preco_venda_atual = item['values'][6] if len(item['values']) > 6 else 0

    janela_p = Toplevel(root)
    janela_p.title(f"Definir Preços: {nome_produto}")
    janela_p.geometry("600x420")
    janela_p.configure(bg=LIGHT_BG)

    Label(janela_p, text=f"Produto: {nome_produto}", bg=LIGHT_BG, fg=LIGHT_TEXT).pack(pady=12, padx=12)
    Label(janela_p, text="Preço de Custo (R$):", bg=LIGHT_BG, fg=LIGHT_TEXT).pack(pady=8, padx=12)
    e_custo = Entry(janela_p, bg=LIGHT_CARD, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
    e_custo.insert(0, str(preco_custo_atual))
    e_custo.pack(pady=4, padx=12, ipady=4)
    Label(janela_p, text="Preço de Venda (R$):", bg=LIGHT_BG, fg=LIGHT_TEXT).pack(pady=8, padx=12)
    e_venda = Entry(janela_p, bg=LIGHT_CARD, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
    e_venda.insert(0, str(preco_venda_atual))
    e_venda.pack(pady=4, padx=12, ipady=4)

    def salvar():
        try:
            custo = float(e_custo.get())
            venda = float(e_venda.get())
            execute_query("UPDATE produtos SET preco_custo=?, preco_venda=? WHERE id=?", (custo, venda, produto_id))
            messagebox.showinfo("Sucesso", "Preços atualizados!")
            atualizar_listagem()
            janela_p.destroy()
        except:
            messagebox.showerror("Erro", "Valores inválidos de preço.")

    btn_salvar_precos = Button(janela_p, text="Salvar",
           bg=LIGHT_BUTTON, fg=LIGHT_TEXT, activebackground=LIGHT_BUTTON_ACTIVE,
           command=salvar)
    btn_salvar_precos.pack(pady=14)

def abrir_janela_movimentacao(tipo):
    """Abre a janela para Entrada ou Saída de estoque."""
    if not tree.selection():
        messagebox.showwarning("Atenção", "Selecione um produto na lista primeiro.")
        return

    item_selecionado = tree.item(tree.focus())
    produto_id = item_selecionado['values'][0]
    nome_produto = item_selecionado['values'][1]

    janela_m = Toplevel(root)
    janela_m.title(f"{tipo} de Estoque: {nome_produto}")
    janela_m.geometry("700x520")
    janela_m.configure(bg=LIGHT_BG)

    delta_sinal = 1 if tipo == "ENTRADA" else -1

    form = Frame(janela_m, bg=LIGHT_BG)
    form.pack(pady=10, padx=12, fill='both', expand=True)

    Label(form, text=f"Produto:", bg=LIGHT_BG, fg=LIGHT_TEXT).grid(row=0, column=0, sticky='e', padx=8, pady=10)
    Label(form, text=f"{nome_produto}", bg=LIGHT_BG, fg=LIGHT_TEXT).grid(row=0, column=1, sticky='w', padx=8, pady=10)

    Label(form, text=f"Quantidade para {tipo}:", bg=LIGHT_BG, fg=LIGHT_TEXT).grid(row=1, column=0, sticky='e', padx=8, pady=10)
    qtd_m = Entry(form, bg=LIGHT_CARD, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
    qtd_m.insert(0, "1")
    qtd_m.grid(row=1, column=1, sticky='w', padx=8, pady=10)

    btn_confirmar = Button(janela_m, text=("⬆ ENTRADA" if tipo == "ENTRADA" else "⬇ SAÍDA"),
           command=lambda: [
               atualizar_estoque(
                   produto_id,
                   float(qtd_m.get()) * delta_sinal,
                   tipo_mov=("ENTRADA" if tipo == "ENTRADA" else "SAIDA")
               ),
               janela_m.destroy()
           ])
    btn_confirmar.configure(bg=LIGHT_BUTTON, fg=LIGHT_TEXT, activebackground=LIGHT_BUTTON_ACTIVE)
    btn_confirmar.pack(pady=10)

def calcular_resumo_caixa(periodo_inicio=None, periodo_fim=None, produto_id=None):
    """Retorna lista com (produto_id, nome, qtd_entrada, qtd_saida, total_compra, total_venda).
    Se produto_id for informado, retorna apenas para esse produto.
    """
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        params = []
        filtro_data = ""
        filtro_prod = ""
    if produto_id:
        filtro_prod = " WHERE p.id = ?"
        params.append(produto_id)
    if periodo_inicio and periodo_fim:
        if produto_id:
            filtro_data = " AND datetime(data_hora) BETWEEN datetime(?) AND datetime(?)"
        else:
            filtro_data = " WHERE datetime(data_hora) BETWEEN datetime(?) AND datetime(?)"
        params.extend([periodo_inicio + " 00:00:00", periodo_fim + " 23:59:59"])

        cursor.execute(
        """
        SELECT p.id, p.nome,
               SUM(CASE WHEN m.tipo='ENTRADA' THEN m.quantidade ELSE 0 END) AS qtd_entrada,
               SUM(CASE WHEN m.tipo='SAIDA' THEN m.quantidade ELSE 0 END) AS qtd_saida,
               SUM(CASE WHEN m.tipo='ENTRADA' THEN m.quantidade*m.preco_unitario ELSE 0 END) AS total_compra,
               SUM(CASE WHEN m.tipo='SAIDA' THEN m.quantidade*m.preco_unitario ELSE 0 END) AS total_venda
        FROM produtos p
        LEFT JOIN movimentacoes m ON m.produto_id = p.id
        WHERE 1=1
        """ + 
        (f" AND p.id = ?" if produto_id else "") +
        (f" AND datetime(m.data_hora) BETWEEN datetime(?) AND datetime(?)" if periodo_inicio and periodo_fim else "") +
        """
        GROUP BY p.id, p.nome
        ORDER BY p.nome
        """,
        params
    )
        dados = cursor.fetchall()
    return dados

def abrir_janela_fechamento_caixa():
    janela_f = Toplevel(root)
    janela_f.title("Fechamento de Caixa")
    janela_f.geometry("900x600")  # Aumentado para acomodar a nova tabela
    janela_f.configure(bg=COLOR_BG)

    # Usa o tema escuro global aplicado
    style_dark = ttk.Style()
    try:
        style_dark.theme_use('vista')
    except tk.TclError:
        style_dark.theme_use('clam')

    # Frames no tema escuro
    frame_style = {'bg': COLOR_BG, 'padx': 10, 'pady': 10}

    # Frame para filtros rápidos
    frame_filtros_rapidos = Frame(janela_f, **frame_style)
    frame_filtros_rapidos.pack(pady=5, fill="x")
    
    # Funções para os filtros rápidos
    def aplicar_filtro_hoje():
        hoje = date.today().strftime("%Y-%m-%d")
        e_ini.delete(0, END)
        e_fim.delete(0, END)
        e_ini.insert(0, hoje)
        e_fim.insert(0, hoje)
        carregar()
        
    def aplicar_filtro_ontem():
        ontem = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        e_ini.delete(0, END)
        e_fim.delete(0, END)
        e_ini.insert(0, ontem)
        e_fim.insert(0, ontem)
        carregar()
        
    def aplicar_filtro_mes_atual():
        hoje = date.today()
        primeiro_dia = date(hoje.year, hoje.month, 1).strftime("%Y-%m-%d")
        e_ini.delete(0, END)
        e_fim.delete(0, END)
        e_ini.insert(0, primeiro_dia)
        e_fim.insert(0, hoje.strftime("%Y-%m-%d"))
        carregar()
        
    def aplicar_filtro_mes_anterior():
        hoje = date.today()
        primeiro_dia_mes_anterior = date(hoje.year, hoje.month-1 if hoje.month > 1 else 12, 1)
        if hoje.month == 1:
            ultimo_dia_mes_anterior = date(hoje.year-1, 12, 31)
        else:
            ultimo_dia_mes_anterior = date(hoje.year, hoje.month, 1) - timedelta(days=1)
        
        e_ini.delete(0, END)
        e_fim.delete(0, END)
        e_ini.insert(0, primeiro_dia_mes_anterior.strftime("%Y-%m-%d"))
        e_fim.insert(0, ultimo_dia_mes_anterior.strftime("%Y-%m-%d"))
        carregar()
        
    def aplicar_filtro_ultimos_30_dias():
        hoje = date.today()
        data_30_dias_atras = (hoje - timedelta(days=30)).strftime("%Y-%m-%d")
        e_ini.delete(0, END)
        e_fim.delete(0, END)
        e_ini.insert(0, data_30_dias_atras)
        e_fim.insert(0, hoje.strftime("%Y-%m-%d"))
        carregar()
    
    # Botões de filtros rápidos
    Label(frame_filtros_rapidos, text="Filtros Rápidos:", bg=COLOR_BG, fg=COLOR_TEXT, font=("Segoe UI", 10, "bold")).pack(side=LEFT, padx=8)

    btn_hoje = Button(frame_filtros_rapidos, text="Hoje 🗓", command=aplicar_filtro_hoje, bg='white', fg='black', activebackground='#E5E5E5')
    btn_hoje.pack(side=LEFT, padx=6, pady=4)

    btn_ontem = Button(frame_filtros_rapidos, text="Ontem 🗓", command=aplicar_filtro_ontem, bg='white', fg='black', activebackground='#E5E5E5')
    btn_ontem.pack(side=LEFT, padx=6, pady=4)

    btn_mes_atual = Button(frame_filtros_rapidos, text="Mês Atual 🗓", command=aplicar_filtro_mes_atual, bg='white', fg='black', activebackground='#E5E5E5')
    btn_mes_atual.pack(side=LEFT, padx=6, pady=4)

    btn_mes_anterior = Button(frame_filtros_rapidos, text="Mês Anterior 🗓", command=aplicar_filtro_mes_anterior, bg='white', fg='black', activebackground='#E5E5E5')
    btn_mes_anterior.pack(side=LEFT, padx=6, pady=4)

    btn_30_dias = Button(frame_filtros_rapidos, text="Últimos 30 dias 🗓", command=aplicar_filtro_ultimos_30_dias, bg='white', fg='black', activebackground='#E5E5E5')
    btn_30_dias.pack(side=LEFT, padx=6, pady=4)
    
    # Frame para filtros personalizados
    frame_filtros = Frame(janela_f, **frame_style)
    frame_filtros.pack(pady=5, fill="x")
    
    Label(frame_filtros, text="Período:", bg=COLOR_BG, fg=COLOR_TEXT).pack(side=LEFT, padx=5)
    Label(frame_filtros, text="De:", bg=COLOR_BG, fg=COLOR_TEXT).pack(side=LEFT)
    e_ini = Entry(frame_filtros, width=10, bg='white', fg='black', insertbackground='black')
    e_ini.pack(side=LEFT, padx=2)
    e_ini.insert(0, date.today().strftime("%Y-%m-%d"))
    
    Label(frame_filtros, text="Até:", bg=COLOR_BG, fg=COLOR_TEXT).pack(side=LEFT)
    e_fim = Entry(frame_filtros, width=10, bg='white', fg='black', insertbackground='black')
    e_fim.pack(side=LEFT, padx=2)
    e_fim.insert(0, date.today().strftime("%Y-%m-%d"))
    
    # Frame para resultados
    frame_resultados = Frame(janela_f, **frame_style)
    frame_resultados.pack(pady=10, fill="both", expand=True)
    
    # Função para carregar os dados
    def carregar():
        # Limpa o frame de resultados
        for widget in frame_resultados.winfo_children():
            widget.destroy()
            
        data_ini = e_ini.get()
        data_fim = e_fim.get()
        
        # Verifica formato das datas
        try:
            datetime.strptime(data_ini, "%Y-%m-%d")
            datetime.strptime(data_fim, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido. Use AAAA-MM-DD")
            return
            
        # Carrega dados de produtos
        dados_produtos = calcular_resumo_caixa(data_ini, data_fim)
        
        # Carrega dados de serviços
        dados_servicos, total_servicos = calcular_resumo_servicos(data_ini, data_fim)
        
        # Cria frame para produtos
        frame_produtos = LabelFrame(frame_resultados, text="Movimentação de Produtos", bg=COLOR_CARD, fg=COLOR_TEXT, font=("Segoe UI", 11, "bold"))
        frame_produtos.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Cria tabela para produtos
        cols_produtos = ('Produto', 'Entradas', 'Saídas', 'Compras (R$)', 'Vendas (R$)', 'Lucro (R$)')
        tree_produtos = ttk.Treeview(frame_produtos, columns=cols_produtos, show='headings', height=8, style='Treeview')
        
        for col in cols_produtos:
            tree_produtos.heading(col, text=col)
            tree_produtos.column(col, width=100, anchor=CENTER)
        
        tree_produtos.column('Produto', width=200, anchor=W)
        
        # Preenche a tabela de produtos
        total_compras = 0
        total_vendas = 0
        total_lucro = 0
        
        for item in dados_produtos:
            produto_id, nome, qtd_entrada, qtd_saida, total_compra, total_venda = item
            lucro = total_venda - total_compra
            tree_produtos.insert('', 'end', values=(nome, qtd_entrada, qtd_saida, f"R$ {total_compra:.2f}", f"R$ {total_venda:.2f}", f"R$ {lucro:.2f}"))
            total_compras += total_compra
            total_vendas += total_venda
            total_lucro += lucro
            
        # Adiciona linha de totais
        tree_produtos.insert('', 'end', values=('TOTAL', '', '', f"R$ {total_compras:.2f}", f"R$ {total_vendas:.2f}", f"R$ {total_lucro:.2f}"))
        
        tree_produtos.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Cria frame para serviços
        frame_servicos = LabelFrame(frame_resultados, text="Serviços Realizados", bg=COLOR_CARD, fg=COLOR_TEXT, font=("Segoe UI", 11, "bold"))
        frame_servicos.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Cria tabela para serviços
        cols_servicos = ('Serviço', 'Qtd', 'Total (R$)', 'Barbeiro', 'Qtd por Barbeiro', 'Total por Barbeiro (R$)')
        tree_servicos = ttk.Treeview(frame_servicos, columns=cols_servicos, show='headings', height=8, style='Treeview')
        
        for col in cols_servicos:
            tree_servicos.heading(col, text=col)
            tree_servicos.column(col, width=100, anchor=CENTER)
        
        tree_servicos.column('Serviço', width=150, anchor=W)
        tree_servicos.column('Barbeiro', width=100, anchor=W)
        
        # Preenche a tabela de serviços
        for item in dados_servicos:
            servico, qtd, total, barbeiro, qtd_barbeiro, total_barbeiro = item
            tree_servicos.insert('', 'end', values=(servico, qtd, f"R$ {total:.2f}", barbeiro, qtd_barbeiro, f"R$ {total_barbeiro:.2f}"))
            
        tree_servicos.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Cria frame para resumo final
        frame_resumo = LabelFrame(frame_resultados, text="RESUMO DO PERÍODO", bg=COLOR_CARD, fg=COLOR_TEXT, font=("Segoe UI", 11, "bold"))
        frame_resumo.pack(fill="both", padx=5, pady=5)
        
        # Adiciona informações do resumo
        Label(frame_resumo, text=f"Total em Serviços: R$ {total_servicos:.2f}", bg=COLOR_CARD, fg=COLOR_TEXT, font=("Segoe UI", 10)).pack(anchor='w', padx=10, pady=2)
        Label(frame_resumo, text=f"Total em Produtos: R$ {total_lucro:.2f}", bg=COLOR_CARD, fg=COLOR_TEXT, font=("Segoe UI", 10)).pack(anchor='w', padx=10, pady=2)
        Label(frame_resumo, text=f"Total Geral: R$ {(total_servicos + total_lucro):.2f}", bg=COLOR_CARD, fg=COLOR_TEXT, font=("Segoe UI", 10, "bold")).pack(anchor='w', padx=10, pady=2)
    
    # Botão para carregar
    btn_carregar = Button(frame_filtros, text="Carregar 🔄", command=carregar, bg='white', fg='black', activebackground='#E5E5E5')
    btn_carregar.pack(side=LEFT, padx=10)
    
    # Carrega os dados iniciais
    carregar()

# --- 4. Configuração da Janela Principal ---



root = Tk()
root.title("Gestão de Estoque - BARBEARIA")
root.geometry("1280x800")
root.configure(bg='#1F1F1F')

# Tipografia base
FONT_BASE = ("Segoe UI", 12)
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 12)

# Paleta Dark
COLOR_BG = "#1F1F1F"
COLOR_CARD = "#2C2C2C"
COLOR_GOLD = "#DAA520"
COLOR_GOLD_ACTIVE = "#E5B73B"
COLOR_BLUE = "#3B82F6"
COLOR_TEXT = "#FFFFFF"
COLOR_TEXT_SECONDARY = "#B0B0B0"
COLOR_ALERT = "#B91C1C"

# Paleta Light para pop-ups e fechamento de caixa
LIGHT_BG = "#E8E8E8"            # Fundo cinza suave
LIGHT_CARD = "#F5F5F5"          # Campos e áreas internas
LIGHT_BUTTON = "#F2D27A"        # Botão dourado suave
LIGHT_BUTTON_ACTIVE = "#EAC45E" # Dourado ativo/hover
LIGHT_TEXT = "#000000"

def apply_dark_theme():
    style = ttk.Style()
    # Tenta usar tema padrão; se falhar, usa clam
    try:
        style.theme_use('vista')
    except tk.TclError:
        style.theme_use('clam')

    # Notebook
    style.configure('TNotebook', background=COLOR_BG)
    style.configure('TNotebook.Tab', padding=(14, 10), font=("Segoe UI", 12, "bold"),
                    background=COLOR_CARD, foreground=COLOR_TEXT_SECONDARY)
    style.map('TNotebook.Tab',
              background=[('selected', COLOR_BG)],
              foreground=[('selected', COLOR_GOLD)])

    # Treeview
    style.configure('Treeview',
                    background=COLOR_BG,
                    fieldbackground=COLOR_BG,
                    foreground=COLOR_TEXT,
                    rowheight=28,
                    font=("Segoe UI", 12, "bold"))
    style.configure('Treeview.Heading',
                    background=COLOR_GOLD,
                    foreground='#000000',
                    font=("Segoe UI", 12, "bold"))
    style.map('Treeview', background=[('selected', COLOR_BLUE)])

    # Variante clara para Estoque
    style.configure('Light.Treeview',
                    background='#FFFFFF',
                    fieldbackground='#FFFFFF',
                    foreground='#000000',
                    rowheight=28,
                    font=("Segoe UI", 12, "bold"))
    style.configure('Light.Treeview.Heading',
                    background=COLOR_GOLD,
                    foreground='#000000',
                    font=("Segoe UI", 12, "bold"))
    style.map('Light.Treeview', background=[('selected', '#BBD4F2')], foreground=[('selected', '#000000')])

    # Botões (ttk)
    style.configure('Primary.TButton',
                    background=COLOR_GOLD,
                    foreground='#000000',
                    padding=10,
                    font=("Segoe UI", 12, "bold"))
    style.map('Primary.TButton', background=[('active', COLOR_GOLD_ACTIVE)])

    style.configure('Secondary.TButton',
                    background=COLOR_BLUE,
                    foreground='#FFFFFF',
                    padding=10,
                    font=("Segoe UI", 12, "bold"))
    style.map('Secondary.TButton', background=[('active', '#2563EB')])

def estilizar_botao(botao, variante='primary'):
    """Aplica estilo dark aos botões tk ou ttk sem alterar lógica."""
    # Para ttk.Button, usamos estilos nomeados
    if isinstance(botao, ttk.Button):
        if variante == 'primary':
            botao.configure(style='Primary.TButton')
        else:
            botao.configure(style='Secondary.TButton')
        botao.configure(cursor='hand2')
        return
    # Para tk.Button
    if isinstance(botao, Button):
        if variante == 'primary':
            botao.configure(bg=COLOR_GOLD, fg='#000000', activebackground=COLOR_GOLD_ACTIVE,
                            relief='flat', bd=0, font=FONT_BASE, cursor='hand2')
        else:
            botao.configure(bg=COLOR_BLUE, fg='#FFFFFF', activebackground='#2563EB',
                            relief='flat', bd=0, font=FONT_BASE, cursor='hand2')

apply_dark_theme()

# Helper genérico para confirmar ações críticas de exclusão
def confirm_and_run(prompt, action, *args, **kwargs):
    if messagebox.askyesno("Confirmação", prompt):
        return action(*args, **kwargs)
    return False

# Topo com logo e título
top_bar = Frame(root, bg=COLOR_BG)
top_bar.pack(fill='x', pady=10)

logo_label = None
try:
    import os
    logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
    if Image and ImageTk and os.path.exists(logo_path):
        img = Image.open(logo_path).resize((120, 120))
        logo_img = ImageTk.PhotoImage(img)
        logo_label = Label(top_bar, image=logo_img, bg=COLOR_BG)
        logo_label.image = logo_img
        logo_label.pack(pady=5)
except Exception:
    pass

title_lbl = Label(top_bar, text='Barbearia — Gestão', bg=COLOR_BG, fg=COLOR_GOLD, font=FONT_TITLE)
title_lbl.pack()
subtitle_lbl = Label(top_bar, text='Estoque, Serviços e Caixa', bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY, font=FONT_SUBTITLE)
subtitle_lbl.pack()

container = Frame(root, bg=COLOR_BG)
container.pack(pady=10, padx=10, fill="both", expand=True)

# Barra lateral à esquerda
sidebar = Frame(container, bg=COLOR_BG)
sidebar.pack(side="left", fill="y")

# Utilitário para criar tiles laterais estilo cartão com ícone e texto
def criar_tile(parent, titulo, icone_texto, on_click):
    tile_bg = COLOR_CARD
    tile_bg_hover = '#3A3A3A'
    frame = Frame(parent, bg=tile_bg, bd=0, relief='flat')
    frame.pack(pady=6, padx=8, anchor='w', fill='x')
    frame.configure(width=220, height=80)
    frame.pack_propagate(False)

    icone = Label(frame, text=icone_texto, bg=tile_bg, fg=COLOR_GOLD, font=("Segoe UI", 18, "bold"))
    icone.pack(pady=(10,0))
    titulo_lbl = Label(frame, text=titulo, bg=tile_bg, fg=COLOR_TEXT, font=("Segoe UI", 12, "bold"))
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

# Área central com notebook (abas)
notebook = ttk.Notebook(container)
notebook.pack(side="left", padx=10, fill="both", expand=True)

def add_tab_header(parent, titulo, subtitulo):
    hdr = Frame(parent, bg=COLOR_BG)
    hdr.pack(fill='x', pady=10)
    Label(hdr, text=titulo, bg=COLOR_BG, fg=COLOR_GOLD, font=FONT_TITLE).pack()
    Label(hdr, text=subtitulo, bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY, font=FONT_SUBTITLE).pack()

# Aba "Estoque" - migra a tabela existente
frame_tabela = Frame(notebook, bg=COLOR_BG)
notebook.add(frame_tabela, text="Estoque")
add_tab_header(frame_tabela, "Estoque 📦", "Produtos e quantidades em estoque")

colunas = ('ID', 'Produto', 'Categoria', 'Qtd. Atual', 'Qtd. Mínima', 'Preço Custo', 'Preço Venda')
tree = ttk.Treeview(frame_tabela, columns=colunas, show='headings', style='Light.Treeview')

tree.column('ID', width=50, anchor=CENTER)
tree.column('Produto', width=250, anchor=W)
tree.column('Categoria', width=120, anchor=CENTER)
tree.column('Qtd. Atual', width=100, anchor=CENTER)
tree.column('Qtd. Mínima', width=100, anchor=CENTER)
tree.column('Preço Custo', width=100, anchor=CENTER)
tree.column('Preço Venda', width=100, anchor=CENTER)

for col in colunas:
    tree.heading(col, text=col)

# Estilo visual da Treeview e cabeçalhos
style = ttk.Style()
# Tags para listras e alerta dentro da tree principal (dark)
tree.tag_configure('odd', background='#FFFFFF')
tree.tag_configure('even', background='#F5F5F5')
tree.tag_configure('alerta', background='#FFE4E6')

# Busca rápida acima da tabela
Label(frame_tabela, text="Buscar Produto:", bg=COLOR_BG, fg=COLOR_TEXT).pack(pady=5)
search_entry = Entry(frame_tabela, bg='white', fg='black', insertbackground='black')
search_entry.pack(pady=5)

def filtrar_produtos(event=None):
    termo = search_entry.get().lower()
    for item in tree.get_children():
        valores = tree.item(item)['values']
        nome = str(valores[1]).lower()
        tree.detach(item)
        if termo in nome:
            tree.reattach(item, '', 'end')

search_entry.bind('<KeyRelease>', filtrar_produtos)

tree.pack(side="left", fill="both", expand=True)

scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Aba "Serviços" com sub-abas para Barbeiro 1 e Barbeiro 2
tab_servico = Frame(notebook, bg=COLOR_BG)
notebook.add(tab_servico, text="Serviços")
add_tab_header(tab_servico, "Registrar Serviços 💈", "Escolha o barbeiro e o serviço")

def montar_aba_servico():
    # Tabela de preços fixa (valores estáticos, não editáveis)
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

    # Notebook interno com duas abas: Barbeiro 1 e Barbeiro 2
    servicos_notebook = ttk.Notebook(tab_servico)
    servicos_notebook.pack(fill='both', expand=True, padx=10, pady=10)

    tab_b1 = Frame(servicos_notebook, bg=COLOR_BG)
    tab_b2 = Frame(servicos_notebook, bg=COLOR_BG)
    servicos_notebook.add(tab_b1, text="Barbeiro 1")
    servicos_notebook.add(tab_b2, text="Barbeiro 2")

    def montar_form_servico(parent, barbeiro_nome):
        Label(parent, text="Serviço:", bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_BASE).pack(pady=10)
        servico_var = StringVar(value=list(tabela_precos.keys())[0])
        servico_combo = ttk.Combobox(
            parent,
            values=list(tabela_precos.keys()),
            textvariable=servico_var,
            state="readonly"
        )
        servico_combo.pack(pady=5)

        Label(parent, text="Valor (R$):", bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_BASE).pack(pady=10)
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
            if registrar_servico(servico_var.get().title(), valor_var.get(), barbeiro_nome):
                messagebox.showinfo("Sucesso", "Serviço registrado com sucesso!")

        btn_salvar = ttk.Button(parent, text="💾 Salvar", command=salvar_servico)
        estilizar_botao(btn_salvar, 'primary')
        btn_salvar.pack(pady=12)

    montar_form_servico(tab_b1, "Barbeiro 1")
    montar_form_servico(tab_b2, "Barbeiro 2")

# Menu lateral
Label(sidebar, text="Menu", bg=COLOR_BG, fg=COLOR_TEXT, font=("Segoe UI", 12, "bold")).pack(anchor='w', padx=10, pady=(0,8))

criar_tile(sidebar, "Novo Produto", "➕", abrir_janela_cadastro)
criar_tile(sidebar, "Entrada de Estoque", "⬆", lambda: abrir_janela_movimentacao("ENTRADA"))
criar_tile(sidebar, "Saída de Estoque", "⬇", lambda: abrir_janela_movimentacao("SAÍDA"))
criar_tile(sidebar, "Definir Preços", "💲", abrir_janela_precos)
criar_tile(sidebar, "Fechamento de Caixa", "🧾", lambda: abrir_janela_fechamento_caixa())

# Atualiza a listagem inicial e inicia o loop principal
def montar_tab_movimentacoes():
    tab_mov = Frame(notebook, bg=COLOR_BG)
    notebook.add(tab_mov, text="Movimentações")
    add_tab_header(tab_mov, "Movimentações 🔄", "Entrada e saída de estoque")

    Label(tab_mov, text="Use os botões laterais para registrar movimentações.",
          bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY, font=FONT_BASE).pack(pady=10)
    return tab_mov

def montar_tab_caixa():
    tab_caixa = Frame(notebook, bg=COLOR_BG)
    notebook.add(tab_caixa, text="Fechamento de Caixa")
    add_tab_header(tab_caixa, "Fechamento de Caixa 🧾", "Relatórios por período")

    Label(tab_caixa, text="Use o botão lateral para abrir o fechamento de caixa.",
          bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY, font=FONT_BASE).pack(pady=10)
    return tab_caixa

# Inicializa a aba de serviço
montar_aba_servico()

# Rodapé com relógio
class BarberShopApp:
    """Encapsula configuração de banco, tema e ciclo principal da UI."""
    def __init__(self):
        setup_db()
        self.root = root
        apply_dark_theme()

    def run(self):
        atualizar_listagem()
        self.root.mainloop()

status_bar = Frame(root, bg=COLOR_BG)
status_bar.pack(fill='x', padx=10, pady=10)
status_label = Label(status_bar, text="", bg=COLOR_BG, fg=COLOR_TEXT_SECONDARY, font=FONT_BASE)
status_label.pack()

def atualizar_clock():
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    status_label.configure(text=f"Pronto • {agora}")
    root.after(1000, atualizar_clock)

atualizar_clock()

# Atalhos de teclado
root.bind('<Control-n>', lambda e: abrir_janela_cadastro())
root.bind('<F5>', lambda e: atualizar_listagem())

if __name__ == "__main__":
    app = BarberShopApp()
    app.run()
