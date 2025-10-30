# 💈 Sistema de Gestão de Estoque e Caixa para Barbearias

## 💡 Sobre o Projeto

Este é o nosso **primeiro projeto pessoal de portfólio**, desenvolvido em colaboração com o **Nicolas**, com o objetivo de criar um sistema Desktop eficiente e moderno. O projeto utiliza **Python** com `Tkinter` e `SQLite`.

O *core* do sistema lida com funcionalidades universais para o varejo (estoque, vendas e apuração financeira), o que permite sua **rápida adaptação para gestão de qualquer tipo de pequeno comércio**, como lojas, cafeterias ou ateliês.

O desenvolvimento contou com o **uso moderado de ferramentas de IA** para otimização de código, documentação e refatoração da estrutura, garantindo maior robustez e aderência aos padrões de codificação.

## ✨ Funcionalidades em Destaque

* **⚠️ Alerta Visual de Estoque Baixo:** A tabela principal exibe em destaque (vermelho) produtos cuja quantidade está abaixo do mínimo configurado, garantindo reposição imediata.
* **🚀 Fechamento de Caixa Detalhado:** Geração de relatórios financeiros por período, calculando o **Lucro Líquido (R$)** da venda de produtos e totalizando os serviços/vendas por colaborador.
* **🔄 Controle de Movimentação:** Registro detalhado de **ENTRADA** (preço de custo) e **SAÍDA** (preço de venda) que atualiza o inventário e documenta as transações financeiras.
* **🧑‍💻 Gestão de Colaboradores/Serviços:** Módulo em abas (`ttk.Notebook`) para registro de serviços e acompanhamento da performance individual por barbeiro/colaborador.
* **🌙 Dark Theme Consistente:** Interface com um tema escuro unificado para melhor experiência de usuário, aplicado de forma consistente em todos os *widgets* e janelas secundárias.

## ⚙️ Tecnologias Utilizadas

| Tecnologia | Finalidade |
| :--- | :--- |
| **Python 3.x** | Linguagem principal e lógica de negócio. |
| **Tkinter / ttk** | Construção da Interface Gráfica (GUI) e aplicação de estilos. |
| **SQLite 3** | Banco de dados leve e local para persistência de dados. |
| **Pillow (PIL)** | (Se aplicável) Manipulação e exibição de imagens/ícones na UI. |

---

## 📸 Screenshots do Sistema

*(**NOTA:** Substitua os placeholders abaixo pelas suas capturas de tela reais. Este é o ponto mais importante!)*

| Tela Principal (Estoque com Alerta) | Janela de Fechamento de Caixa |
| :---: | :---: |
| ![Tela de Estoque demonstrando o alerta visual de falta de produtos.](https://br.pinterest.com/anacraudiaaa/tela-inicial/) | ![Janela de Fechamento de Caixa com resumo financeiro e filtros.](https://br.freepik.com/fotos-vetores-gratis/fechamento-caixa) |

---

## 🛠️ Como Rodar o Projeto

Siga os passos abaixo para clonar e executar o projeto em sua máquina.

### Pré-requisitos

* Python 3.8+
* Git

### Instalação

1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/Joaocasco/estoque-barbearia
    cd estoque-barbearia
    ```

2.  **Crie e Ative o Ambiente Virtual (Recomendado):**
    ```bash
    # Cria o ambiente
    python -m venv venv

    # Ativa o ambiente (Windows)
    .\venv\Scripts\activate

    # Ativa o ambiente (Linux/Mac)
    source venv/bin/activate
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    *(**NOTA:** Não se esqueça de rodar o comando `pip freeze > requirements.txt` no seu projeto para criar este arquivo.)*

4.  **Execute a Aplicação:**
    ```bash
    python estoque-final.py
    ```
    *(**NOTA:** Caso tenha refatorado o nome, substitua `estoque-final.py` pelo nome do seu arquivo principal, como `main.py`.)*

## 👥 Equipe e Agradecimentos

Este projeto foi desenvolvido por:

* **João Vitor De Souza Casco**
* **Nicolas Vinicius dos Santos Dias** (Colaborador)

Este projeto está licenciado sob a licença **MIT** *(Recomendação: Crie o arquivo LICENSE)*.
