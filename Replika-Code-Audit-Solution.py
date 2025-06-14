# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# 🤖 Auditor de Código com IA (Gemini & Python) 🚀
#
# Autor: Elias Andrade
# GitHub: https://github.com/chaos4455
# LinkedIn: https://www.linkedin.com/in/itilmgf/
#
# Descrição:
# Esta aplicação de desktop (PyQt5) permite que desenvolvedores auditem
# arquivos de código-fonte Python usando a IA Generativa do Google (Gemini).
# O usuário pode arrastar e soltar arquivos, fornecer um prompt de auditoria
# personalizado e receber relatórios detalhados em HTML.
#
# O projeto demonstra como a IA pode ser uma ferramenta poderosa para:
# - Garantir a conformidade com regras de negócio.
# - Melhorar a qualidade do código e a documentação.
# - Acelerar revisões de código (code reviews).
# - Auxiliar no versionamento e na validação de lógicas complexas.
#
# Como Adaptar:
# A "inteligência" da auditoria reside na função `build_audit_prompt`.
# Modifique o prompt dentro dessa função para adaptar a ferramenta a
# qualquer domínio: auditar C#, Java, verificar padrões de segurança
# específicos, validar configurações de infraestrutura como código (IaC), etc.
# -----------------------------------------------------------------------------

import sys
import os
import time
import logging
from datetime import datetime
import re
import threading
import hashlib

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
                             QListWidget, QListWidgetItem, QProgressBar, QTextEdit,
                             QMessageBox, QHBoxLayout, QGroupBox,
                             QSizePolicy, QComboBox, QFileDialog)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRunnable, QThreadPool, QSize, pyqtSlot, QTimer
from PyQt5.QtGui import QIcon, QDragEnterEvent, QDropEvent, QColor

# --- Constantes de Configuração ---
APP_VERSION = "2.0-Public-Generic"
CONFIG = {
    # --- IMPORTANTE: CONFIGURAÇÃO DA API KEY ---
    # A chave de API agora é lida da variável de ambiente 'GEMINI_API_KEY'.
    # Isso é uma prática de segurança essencial. NUNCA coloque chaves no código.
    # Para rodar, defina a variável de ambiente no seu terminal:
    # Windows: set GEMINI_API_KEY="SUA_CHAVE_AQUI"
    # Linux/macOS: export GEMINI_API_KEY="SUA_CHAVE_AQUI"
    "API_KEY": os.environ.get("GEMINI_API_KEY", ""),
    "AVAILABLE_MODELS": ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest", "gemini-pro"],
    "DEFAULT_MODEL": "gemini-1.5-flash-latest",
    "AUDIT_SUBFOLDER_NAME": "auditoria-codigo",
    "LOG_FILENAME": "code_audit_app.log",
    "APP_ICON_PATH": "app_icon.png", # Crie um ícone 'app_icon.png' ou use o fallback
    "FALLBACK_ICON_PATH": "icon.png", # Ícone de fallback
    "MAX_THREADS_DIVISOR": 2, # Usa metade dos cores da CPU para processamento paralelo
    "API_TIMEOUT_SECONDS": 400,
    "MAX_FILENAME_LENGTH": 150,
    "THUMBNAIL_SIZE": QSize(32, 32),
    # Parâmetros da Geração da IA (ajuste para mais criatividade ou mais precisão)
    "DEFAULT_TEMPERATURE": 0.2, # Baixa temperatura para respostas mais factuais e consistentes
    "DEFAULT_TOP_P": 0.9,
    "DEFAULT_TOP_K": 32,
    "DEFAULT_MAX_TOKENS": 8192,
}

# --- Verificação de Dependência e Inicialização da IA (Google AI) ---
GOOGLE_AI_AVAILABLE = False
try:
    import google.generativeai as genai
    import google.api_core.exceptions

    # Verifica se a API Key foi carregada da variável de ambiente
    if CONFIG["API_KEY"]:
        try:
            genai.configure(api_key=CONFIG["API_KEY"])
            GOOGLE_AI_AVAILABLE = True
            print("✅ Biblioteca google.generativeai carregada e API Key configurada via variável de ambiente.")
        except Exception as config_e:
            print(f"❌ Erro ao configurar google.generativeai com a API Key: {config_e}")
            logging.error(f"Erro ao configurar google.generativeai com a API Key: {config_e}")
    else:
        print("⚠️ AVISO: A variável de ambiente 'GEMINI_API_KEY' não foi encontrada ou está vazia. Funcionalidade de IA desabilitada.")
        logging.warning("AVISO: Variável de ambiente GEMINI_API_KEY ausente. IA desabilitada.")
except ImportError:
    print("❌ AVISO: Biblioteca 'google-generativeai' não encontrada. Funcionalidade de IA desabilitada.")
    print("   Instale com: pip install google-generativeai")
    logging.error("Biblioteca google-generativeai não encontrada.")
except Exception as import_e:
    print(f"❌ Erro inesperado ao importar/configurar google.generativeai: {import_e}")
    logging.error(f"Erro inesperado ao importar/configurar google.generativeai: {import_e}", exc_info=True)

# Fallback para o caso da biblioteca da IA não estar disponível
if not GOOGLE_AI_AVAILABLE:
    class DummyGenAI:
        def configure(*args, **kwargs): pass
        class GenerativeModel:
            def __init__(self, *args, **kwargs): pass
            def generate_content(self, *args, **kwargs):
                class DummyResponse:
                    text = "Erro: A biblioteca google.generativeai não está disponível ou a API Key não foi configurada."
                return DummyResponse()
    genai = type('DummyGenAIModule', (object,), {'GenerativeModel': DummyGenAI.GenerativeModel, 'configure': DummyGenAI.configure})()

# Colorama para logs coloridos no console
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    # Cria uma classe dummy se colorama não estiver instalado
    class DummyColor:
        def __getattr__(self, name): return ""
    Fore = Style = DummyColor()

# --- Configuração do Logging ---
logging.basicConfig(
    filename=CONFIG["LOG_FILENAME"],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
    encoding='utf-8'
)
logging.info(f"--- Aplicação de Auditoria de Código Iniciada (Versão {APP_VERSION}) ---")


def configure_generation():
    """Retorna o dicionário de configuração para a geração de conteúdo pela IA."""
    return {
        "temperature": CONFIG["DEFAULT_TEMPERATURE"],
        "top_p": CONFIG["DEFAULT_TOP_P"],
        "top_k": CONFIG["DEFAULT_TOP_K"],
        "max_output_tokens": CONFIG["DEFAULT_MAX_TOKENS"],
        "response_mime_type": "text/plain",
    }


def send_code_to_gemini(model_name, generation_config, prompt_content):
    """Envia o prompt para a API Gemini e retorna a resposta."""
    if not GOOGLE_AI_AVAILABLE:
        logging.error("Tentativa de chamar send_code_to_gemini sem IA disponível.")
        return "Erro: Funcionalidade de IA indisponível. Verifique a instalação e a API Key."
    try:
        model = genai.GenerativeModel(model_name=model_name, generation_config=generation_config)
        
        logging.info(f"Enviando requisição para o modelo {model_name}...")
        print(f"{Fore.CYAN}Enviando requisição para {model_name}...{Style.RESET_ALL}")

        response = model.generate_content(prompt_content, request_options={'timeout': CONFIG["API_TIMEOUT_SECONDS"]})

        # Extrai o texto da resposta de forma segura
        response_text = getattr(response, 'text', '').strip()
        if not response_text:
            logging.warning("API retornou uma resposta vazia.")
            return "Erro: A API da IA retornou uma resposta vazia."

        logging.info(f"Resposta recebida ({len(response_text)} caracteres).")
        print(f"{Fore.GREEN}Resposta recebida da Gemini ({len(response_text)} caracteres).{Style.RESET_ALL}")
        return response_text

    except (genai.PermissionDenied, google.api_core.exceptions.PermissionDenied) as e:
        emsg = "Erro de Permissão/Autenticação com a API Gemini. A sua API Key é válida e está habilitada?"
        logging.error(f"{emsg} Detalhe: {e}", exc_info=True)
        print(f"{Fore.RED}{emsg}{Style.RESET_ALL}")
        return f"Erro: {emsg}"
    except (genai.DeadlineExceeded, google.api_core.exceptions.DeadlineExceeded) as e:
        emsg = f"Timeout ({CONFIG['API_TIMEOUT_SECONDS']}s) ao contatar a API Gemini. A rede está estável?"
        logging.error(f"{emsg} Detalhe: {e}", exc_info=True)
        print(f"{Fore.RED}{emsg}{Style.RESET_ALL}")
        return f"Erro: {emsg}"
    except Exception as e:
        emsg = f"Erro inesperado ao comunicar com a API: {type(e).__name__}"
        logging.exception("Erro inesperado em send_code_to_gemini:")
        print(f"{Fore.RED}{emsg} - {e}{Style.RESET_ALL}")
        return f"Erro: {emsg}"


def sanitize_filename(name):
    """Limpa uma string para ser usada como um nome de arquivo seguro."""
    if not name: name = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    name_str = re.sub(r'[\\/*?:"<>|]+', '', str(name))
    name_str = re.sub(r'\s+', '_', name_str)
    return name_str[:CONFIG["MAX_FILENAME_LENGTH"]]


def get_file_metadata(file_path):
    """Extrai metadados e conteúdo de um arquivo de texto."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return {
            "full_path": os.path.abspath(file_path),
            "filename": os.path.basename(file_path),
            "size_bytes": os.path.getsize(file_path),
            "lines": len(content.splitlines()),
            "sha256": hashlib.sha256(content.encode('utf-8', 'ignore')).hexdigest(),
            "modified_time": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
            "content_for_prompt": content
        }
    except Exception as e:
        logging.error(f"Erro ao ler metadados do arquivo {file_path}: {e}", exc_info=True)
        return None

# --- Componentes da GUI (PyQt5) ---

class DropArea(QLabel):
    """Área de arrastar e soltar arquivos."""
    dropped_files = pyqtSignal(list)
    VALID_EXTENSIONS = ['.py'] # Facilmente extensível para ex: ['.py', '.js', '.java']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setText("📂 Arraste arquivos Python (.py) aqui 🐍\nOu clique para selecionar")
        self.setObjectName("DropArea")
        self.setAcceptDrops(True)
        self.reset_style_idle()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.window().open_file_dialog_from_drop_area()

    def reset_style_idle(self): self.setStyleSheet("DropArea#DropArea { border: 3px dashed #28A745; background-color: #E6FFED; border-radius: 8px; }")
    def set_style_dragging(self): self.setStyleSheet("DropArea#DropArea { border: 3px solid #007BFF; background-color: #E7F3FF; }")
    def set_style_processing(self): self.setStyleSheet("DropArea#DropArea { border: 3px solid #DC3545; background-color: #FDEDED; }")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls(): event.acceptProposedAction(); self.set_style_dragging()
    def dragLeaveEvent(self, event): self.reset_style_idle()
    def dropEvent(self, event: QDropEvent):
        self.reset_style_idle()
        files = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile() and os.path.splitext(url.toLocalFile())[1].lower() in self.VALID_EXTENSIONS]
        if files: self.dropped_files.emit(files)


class WorkerSignals(QObject):
    """Sinais emitidos por um worker thread."""
    finished_file = pyqtSignal(str, str, str) # path_original, path_relatorio, titulo_relatorio
    error_file = pyqtSignal(str, str) # path_original, msg_erro
    single_file_status = pyqtSignal(str, str) # path_original, status_msg


class AuditWorker(QRunnable):
    """Worker que executa a auditoria de um único arquivo em uma thread separada."""
    def __init__(self, file_path, model_name, generation_config, user_prompt_addition):
        super().__init__()
        self.signals = WorkerSignals()
        self.file_path = file_path
        self.model_name = model_name
        self.generation_config = generation_config
        self.user_prompt_addition = user_prompt_addition

    @pyqtSlot()
    def run(self):
        base_filename = os.path.basename(self.file_path)
        try:
            self.signals.single_file_status.emit(self.file_path, "Lendo arquivo...")
            file_meta = get_file_metadata(self.file_path)
            if not file_meta: raise ValueError("Falha ao ler metadados do arquivo.")

            self.signals.single_file_status.emit(self.file_path, "Construindo prompt...")
            prompt = self.build_audit_prompt(file_meta, self.user_prompt_addition)

            self.signals.single_file_status.emit(self.file_path, f"Enviando para IA...")
            ai_response = send_code_to_gemini(self.model_name, self.generation_config, prompt)
            
            if not ai_response or ai_response.startswith("Erro:"):
                raise RuntimeError(f"Falha na API: {ai_response}")

            self.signals.single_file_status.emit(self.file_path, "Gerando relatório...")
            html_content = self.extract_html_from_markdown(ai_response)
            if not html_content:
                raise RuntimeError("A IA não retornou um bloco HTML válido.")

            report_title = self.extract_title_from_html(html_content) or f"Relatorio_Auditoria_{base_filename}"
            audit_folder = os.path.join(os.path.dirname(self.file_path), CONFIG["AUDIT_SUBFOLDER_NAME"])
            os.makedirs(audit_folder, exist_ok=True)
            
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"{sanitize_filename(os.path.splitext(base_filename)[0])}_audit_{ts}.html"
            report_filepath = os.path.join(audit_folder, report_filename)

            self.signals.single_file_status.emit(self.file_path, "Salvando...")
            with open(report_filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            self.signals.finished_file.emit(self.file_path, report_filepath, report_title)

        except Exception as e:
            emsg = f"({type(e).__name__}): {e}"
            logging.error(f"Erro no worker para {base_filename}: {emsg}", exc_info=True)
            self.signals.error_file.emit(self.file_path, emsg)

    def extract_html_from_markdown(self, md_text):
        """Extrai o bloco de código HTML de uma resposta em Markdown."""
        match = re.search(r"```html\s*(<!DOCTYPE html.*?>.*?</html>)\s*```", md_text, re.IGNORECASE | re.DOTALL)
        if match: return match.group(1).strip()
        if md_text.strip().lower().startswith("<!doctype html"): return md_text.strip()
        logging.warning("Bloco ```html ... ``` não encontrado na resposta da IA.")
        return None

    def extract_title_from_html(self, html_content):
        """Extrai o conteúdo da tag <title> do HTML."""
        match = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None

    def build_audit_prompt(self, file_meta, user_prompt_addition):
        """
        --- 🧠 O CORAÇÃO DA FERRAMENTA: ENGENHARIA DE PROMPT 🧠 ---

        Este método constrói o prompt que será enviado para a IA.
        É aqui que você define a "personalidade" e os objetivos do auditor de IA.

        COMO ADAPTAR ESTE PROMPT PARA SUAS NECESSIDADES:
        1. Mude a Persona: Em `system_instruction`, altere a primeira linha.
           - Para Java: "Você é um Engenheiro de Software Sênior especialista em Java e no ecossistema Spring."
           - Para Segurança: "Você é um especialista em segurança da informação (AppSec) focado em encontrar vulnerabilidades em código web."
        
        2. Altere os Pontos de Análise: Modifique os tópicos na seção "PONTOS DE ANÁLISE OBRIGATÓRIOS".
           - Adicione seus próprios critérios: "5. Conformidade com Padrões Internos: Verifique se o código segue as diretrizes de estilo da 'Empresa X'..."
           - Remova os que não são relevantes.

        3. Use o `user_prompt_addition`: O texto que o usuário digita na GUI é inserido
           aqui. Incentive o uso de prompts específicos para auditorias direcionadas.

        O prompt atual é um bom ponto de partida genérico para Python, focando em
        qualidade, lógica, segurança e boas práticas.
        """
        
        system_instruction = (
            "Você é um Auditor de Código Sênior e Analista de Qualidade de Software. Sua tarefa é realizar uma análise crítica e detalhada do código-fonte fornecido, atuando como um revisor técnico (code reviewer) experiente e meticuloso. Seja objetivo, construtivo e preciso."
        )

        main_task = (
            f"\n--- CÓDIGO-FONTE PARA ANÁLISE ---\n"
            f"Arquivo: `{file_meta['filename']}`\n"
            f"```python\n{file_meta['content_for_prompt']}\n```\n\n"
            
            "--- PONTOS DE ANÁLISE OBRIGATÓRIOS ---\n"
            "Analise o código acima e avalie CADA um dos seguintes pontos. Para cada ponto, forneça um status (Implementado ✅, Parcialmente Implementado ⚠️, Não Implementado ❌, ou Observação ℹ️), uma explicação detalhada e, quando relevante, inclua trechos de código como evidência (escapados para HTML).\n\n"
            
            "1.  **Lógica de Negócio e Requisitos 🎯:** O código parece implementar uma lógica clara e coesa? Com base no código, qual parece ser o objetivo principal? Existem partes que parecem confusas, incompletas ou potencialmente incorretas em relação a um objetivo de negócio hipotético?\n\n"
            
            "2.  **Qualidade e Boas Práticas (Clean Code) 🧼:** O código é legível e bem estruturado? Avalie o uso de nomes de variáveis e funções, comentários (são úteis ou apenas ruído?), complexidade de funções (são curtas e focadas?), e aderência geral aos princípios do Clean Code e PEP8.\n\n"
            
            "3.  **Segurança e Vulnerabilidades 🛡️:** Existem vulnerabilidades de segurança óbvias? Verifique a presença de: \n"
            "   - Chaves de API, senhas ou outras credenciais 'hardcoded' no código.\n"
            "   - Falta de validação de entradas (se aplicável).\n"
            "   - Uso de bibliotecas conhecidamente vulneráveis ou métodos inseguros (ex: `eval()`, `pickle` com dados não confiáveis).\n\n"

            "4.  **Manutenibilidade e Escalabilidade 🏗️:** O código é fácil de manter e modificar? Avalie o nível de acoplamento entre os componentes, a modularidade e se o design permitiria adicionar novas funcionalidades ou escalar o desempenho sem uma refatoração massiva.\n\n"
            
            "5.  **Tratamento de Erros e Resiliência 🩹:** Como o código lida com erros e exceções? Existe um tratamento adequado com blocos `try-except`? O logging é utilizado para registrar eventos importantes ou erros? O que aconteceria em um cenário de falha (ex: falha de rede, arquivo não encontrado)?\n\n"
            
            "--- ANÁLISE ADICIONAL REQUISITADA PELO USUÁRIO ---\n"
            f"Além da análise padrão, verifique os seguintes pontos específicos solicitados pelo usuário:\n\n"
            f"**Critérios do Usuário:** \"{user_prompt_addition if user_prompt_addition else 'Nenhum critério adicional foi fornecido.'}\""
        )
        
        output_format_instruction = (
            "\n--- FORMATO DE SAÍDA OBRIGATÓRIO: DOCUMENTO HTML5 ---\n"
            "A sua resposta DEVE ser um ÚNICO bloco ```html ... ``` contendo um documento HTML5 completo e bem formatado. NADA DEVE SER ESCRITO FORA DESTE BLOCO.\n\n"
            
            "**Estrutura do HTML:**\n"
            "1.  **`<head>`:** Inclua `<meta charset=\"UTF-8\">`, um `<title>` informativo como `Relatório de Auditoria: {fn}`, e um `<style>` CSS embutido com um design limpo e profissional (use cores como azul escuro, cinza, e destaques verde/amarelo/vermelho para status).\n"
            "2.  **`<body>`:**\n"
            "   - **Cabeçalho:** Título principal como `<h1>Relatório de Auditoria de Código: {fn}</h1>`.\n"
            "   - **Detalhes do Arquivo:** Uma tabela com os metadados: Nome, Tamanho, Linhas, SHA256, Data da Auditoria.\n"
            "   - **Sumário Geral:** Um parágrafo resumindo suas conclusões gerais sobre a qualidade do código.\n"
            "   - **Análise Detalhada:** Crie uma seção (ex: `div` com uma classe `card`) para CADA um dos pontos de análise obrigatórios e para a análise do usuário.\n"
            "     - Cada seção deve ter um `<h4>` com o título do ponto (ex: `<h4>🎯 Lógica de Negócio</h4>`).\n"
            "     - Inclua o status com seu emoji correspondente.\n"
            "     - Forneça sua análise detalhada em parágrafos.\n"
            "     - Mostre evidências de código dentro de `<pre><code>...</code></pre>`, garantindo que os caracteres HTML como `<` e `>` sejam escapados (`<`, `>`).\n"
            "   - **Rodapé:** Inclua um rodapé simples com `Gerado por Auditor de Código IA` e o ano."
        ).format(fn=file_meta['filename'])
        
        # O prompt é uma lista de partes, que pode ser mais robusto para modelos multimodais
        return [system_instruction, main_task, output_format_instruction]


class MainWindow(QWidget):
    """Janela principal da aplicação."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"🕵️ Auditor de Código IA v{APP_VERSION}")
        self.setGeometry(100, 100, 900, 750)
        self.setWindowIcon(QIcon(CONFIG["APP_ICON_PATH"]))

        self.py_file_paths = []
        self.list_item_map = {}
        self.is_processing = False
        
        self.thread_pool = QThreadPool.globalInstance()
        max_threads = max(1, os.cpu_count() // CONFIG["MAX_THREADS_DIVISOR"]) if os.cpu_count() else 2
        self.thread_pool.setMaxThreadCount(max_threads)
        logging.info(f"ThreadPool configurado com um máximo de {max_threads} threads.")

        self._create_widgets()
        self._setup_layout()
        self._connect_signals()
        self.apply_styles()
        
        QTimer.singleShot(100, self.check_ai_readiness)

    def _create_widgets(self):
        self.drop_area = DropArea(self)
        self.file_list = QListWidget()
        self.file_list.setToolTip("Dê um duplo clique em um item para removê-lo.")
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(CONFIG["AVAILABLE_MODELS"])
        self.model_combo.setCurrentText(CONFIG["DEFAULT_MODEL"])

        self.user_prompt_input = QTextEdit()
        self.user_prompt_input.setPlaceholderText("Opcional: Descreva aqui as regras de negócio ou pontos específicos que a IA deve auditar...")
        self.user_prompt_input.setFixedHeight(80)

        self.analyze_button = QPushButton(QIcon.fromTheme("system-run"), " Analisar Código com IA 🚀")
        self.analyze_button.setObjectName("AnalyzeButton")
        self.analyze_button.setEnabled(False)

        self.clear_button = QPushButton(QIcon.fromTheme("edit-clear"), " Limpar Tudo")
        self.clear_button.setObjectName("ClearButton")

        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)
        self.results_area.setPlaceholderText("Status e resultados da auditoria aparecerão aqui...")

        self.status_label = QLabel("Pronto para auditar. Adicione arquivos.")
        self.overall_progress_bar = QProgressBar()

    def _setup_layout(self):
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.drop_area, 1)
        top_layout.addWidget(self.file_list, 2)
        
        model_group = QGroupBox("🤖 Modelo Gemini")
        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_combo)
        model_group.setLayout(model_layout)

        prompt_group = QGroupBox("💬 Prompt Adicional (Suas Regras)")
        prompt_layout = QVBoxLayout()
        prompt_layout.addWidget(self.user_prompt_input)
        prompt_group.setLayout(prompt_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.analyze_button)
        btn_layout.addWidget(self.clear_button)
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label, 1)
        status_layout.addWidget(self.overall_progress_bar)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(model_group)
        main_layout.addWidget(prompt_group)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(QLabel("📋 Log de Resultados:"))
        main_layout.addWidget(self.results_area)
        main_layout.addLayout(status_layout)

    def _connect_signals(self):
        self.drop_area.dropped_files.connect(self.add_files_to_list)
        self.file_list.itemDoubleClicked.connect(self.remove_file_item)
        self.analyze_button.clicked.connect(self.start_analysis)
        self.clear_button.clicked.connect(self.clear_all)

    def apply_styles(self):
        # Estilos podem ser adicionados aqui para melhorar a aparência
        self.setStyleSheet("""
            QWidget { font-size: 10pt; }
            QGroupBox { font-weight: bold; }
            QPushButton#AnalyzeButton { background-color: #27AE60; color: white; font-weight: bold; padding: 8px; }
            QPushButton#AnalyzeButton:disabled { background-color: #95a5a6; }
            QPushButton#ClearButton { background-color: #c0392b; color: white; font-weight: bold; padding: 8px; }
            QProgressBar::chunk { background-color: #2ECC71; }
        """)

    def check_ai_readiness(self):
        """Verifica e alerta o usuário sobre o status da IA na inicialização."""
        if not GOOGLE_AI_AVAILABLE:
            if not CONFIG["API_KEY"]:
                msg = "A variável de ambiente 'GEMINI_API_KEY' não foi definida. A análise por IA está desativada."
                QMessageBox.critical(self, "Configuração Necessária", msg)
            else:
                 msg = "A biblioteca 'google-generativeai' não foi encontrada. Instale com 'pip install google-generativeai'."
                 QMessageBox.warning(self, "Dependência Ausente", msg)

    @pyqtSlot(list)
    def add_files_to_list(self, files):
        count = 0
        for file_path in files:
            if file_path not in self.py_file_paths:
                self.py_file_paths.append(file_path)
                item = QListWidgetItem(QIcon.fromTheme("text-x-python"), os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)
                self.file_list.addItem(item)
                self.list_item_map[file_path] = item
                count += 1
        if count > 0:
            self.analyze_button.setEnabled(True)
            self.results_area.append(f"ℹ️ {count} arquivo(s) adicionado(s) à fila.")

    @pyqtSlot(QListWidgetItem)
    def remove_file_item(self, item):
        path = item.data(Qt.UserRole)
        self.py_file_paths.remove(path)
        self.list_item_map.pop(path, None)
        self.file_list.takeItem(self.file_list.row(item))
        self.analyze_button.setEnabled(bool(self.py_file_paths))
        self.results_area.append(f"ℹ️ Arquivo removido da fila: {os.path.basename(path)}")
        
    def start_analysis(self):
        if not self.py_file_paths:
            QMessageBox.warning(self, "Fila Vazia", "Adicione arquivos para analisar.")
            return
        if not GOOGLE_AI_AVAILABLE:
            self.check_ai_readiness()
            return

        self.set_ui_processing_state(True)
        self.files_to_process = len(self.py_file_paths)
        self.files_processed = 0
        self.overall_progress_bar.setValue(0)
        
        self.results_area.clear()
        self.results_area.append(f"🚀 Iniciando análise de {self.files_to_process} arquivo(s)...")

        model = self.model_combo.currentText()
        gen_cfg = configure_generation()
        user_prompt = self.user_prompt_input.toPlainText().strip()

        for file_path in self.py_file_paths:
            worker = AuditWorker(file_path, model, gen_cfg, user_prompt)
            worker.signals.finished_file.connect(self.on_worker_finished)
            worker.signals.error_file.connect(self.on_worker_error)
            worker.signals.single_file_status.connect(self.update_list_item_status)
            self.thread_pool.start(worker)

    def on_worker_finished(self, orig_path, report_path, report_title):
        self.results_area.append(f"✅ Sucesso: '{os.path.basename(orig_path)}'.\n   📄 Relatório salvo em: {report_path}")
        item = self.list_item_map.get(orig_path)
        if item:
            item.setText(f"{os.path.basename(orig_path)} (✅ Concluído)")
            item.setForeground(QColor("green"))
        self.update_overall_progress()

    def on_worker_error(self, orig_path, error_msg):
        self.results_area.append(f"❌ Erro em '{os.path.basename(orig_path)}': {error_msg}")
        item = self.list_item_map.get(orig_path)
        if item:
            item.setText(f"{os.path.basename(orig_path)} (❌ Erro)")
            item.setForeground(QColor("red"))
        self.update_overall_progress()

    def update_list_item_status(self, file_path, status):
        item = self.list_item_map.get(file_path)
        if item:
            item.setText(f"{os.path.basename(file_path)} ({status})")
    
    def update_overall_progress(self):
        self.files_processed += 1
        progress = int((self.files_processed / self.files_to_process) * 100)
        self.overall_progress_bar.setValue(progress)
        self.status_label.setText(f"Processando: {self.files_processed} de {self.files_to_process}")

        if self.files_processed == self.files_to_process:
            self.set_ui_processing_state(False)
            self.status_label.setText("Análise concluída!")
            self.results_area.append("\n🏁 Análise de todos os arquivos concluída! 🏁")
            QMessageBox.information(self, "Concluído", "A análise de todos os arquivos foi finalizada.")

    def set_ui_processing_state(self, is_processing):
        self.is_processing = is_processing
        self.drop_area.setEnabled(not is_processing)
        self.file_list.setEnabled(not is_processing)
        self.analyze_button.setEnabled(not is_processing and bool(self.py_file_paths))
        self.clear_button.setEnabled(not is_processing)
        self.user_prompt_input.setReadOnly(is_processing)
        
        if is_processing:
            self.drop_area.set_style_processing()
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            self.drop_area.reset_style_idle()
            QApplication.restoreOverrideCursor()

    def clear_all(self):
        self.py_file_paths.clear()
        self.file_list.clear()
        self.list_item_map.clear()
        self.results_area.clear()
        self.user_prompt_input.clear()
        self.overall_progress_bar.setValue(0)
        self.status_label.setText("Pronto para auditar. Adicione arquivos.")
        self.analyze_button.setEnabled(False)

    def open_file_dialog_from_drop_area(self):
        if self.is_processing: return
        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar Arquivos Python", "", "Python Files (*.py);;All Files (*)")
        if files:
            self.add_files_to_list(files)
            
    def closeEvent(self, event):
        if self.is_processing:
            reply = QMessageBox.question(self, 'Sair?', 'Uma análise está em andamento. Deseja realmente sair?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.thread_pool.clear() # Tenta cancelar as tarefas
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        logging.info("Aplicação GUI iniciada.")
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(f"Erro fatal na aplicação: {e}", exc_info=True)
        print(f"{Fore.RED}ERRO FATAL: {e}{Style.RESET_ALL}")
        # Tenta mostrar uma caixa de diálogo de erro mesmo em caso de falha grave
        try:
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Critical)
            error_box.setText("Ocorreu um erro fatal e a aplicação precisa ser fechada.")
            error_box.setInformativeText(str(e))
            error_box.setWindowTitle("Erro Crítico")
            error_box.exec_()
        except:
            pass
        sys.exit(1)
