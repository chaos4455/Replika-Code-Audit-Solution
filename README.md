# 🕵️ Replika AI - Auditor de Lógica de Negócios ⚙️

![Versão do App](https://img.shields.io/badge/version-1.5--AuditLogic--V7R5B1--RC1-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![PyQt5](https://img.shields.io/badge/UI-PyQt5-green?logo=qt)
![Licença](https://img.shields.io/badge/license-MIT-lightgrey)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Elias%20Andrade-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/itilmgf/)
[![GitHub](https://img.shields.io/badge/GitHub-chaos4455-black?style=flat&logo=github)](https://github.com/chaos4455)

---

### 👋 Olá, comunidade! Estou de volta com um projeto para inspirar!

Depois de um tempo focado em outros desafios, estou de volta para compartilhar algo que nasceu de uma necessidade real e que demonstra o poder incrível da Inteligência Artificial no nosso dia a dia como desenvolvedores.

Recentemente, me deparei com um desafio: precisei de uma solução rápida, eficiente e padronizada para **auditar e documentar o versionamento de alguns pipelines de ETL (Extração, Transformação e Carga) de código-fonte**. A lógica de negócios era complexa, com múltiplas regras e exceções, e o processo manual era lento e propenso a erros.

Foi aí que pensei: "E se eu usasse a IA para fazer o trabalho pesado?". Criei então o **Replika AI Auditor**, uma ferramenta desktop que usa o **Google Gemini** para analisar scripts Python, validar a implementação de regras de negócio específicas e gerar um relatório HTML detalhado e profissional em segundos.

Compartilho este projeto com toda a comunidade de desenvolvedores, estudantes e entusiastas de programação e IA, como uma ideia de como podemos transformar tarefas complexas e repetitivas em processos automatizados e inteligentes. A IA não é apenas para chatbots; é uma ferramenta poderosa de produtividade e qualidade!

### ✨ Demonstração Rápida

*(Dica: Grave um GIF rápido mostrando o app em ação e substitua a URL abaixo!)*


---

### 🎯 O Problema: Auditoria de Lógica de Negócios em Código

Auditar código-fonte para garantir que ele esteja alinhado com regras de negócio em constante evolução é um desafio:
*   **Manual e Lento:** Ler centenas de linhas de código para validar regras específicas consome um tempo precioso.
*   **Inconsistente:** Diferentes desenvolvedores podem interpretar as regras de formas ligeiramente diferentes.
*   **Documentação Desatualizada:** Manter uma documentação de auditoria manual e atualizada é um pesadelo.
*   **Versionamento Complexo:** Rastrear qual versão do código implementa qual versão da lógica de negócios é difícil.

### 🤖 A Solução: ETL de Código-Fonte com Inteligência Artificial

Esta ferramenta realiza um "ETL" no seu código:
1.  **Extrai (Extract):** Lê o conteúdo do seu script `.py`.
2.  **Transforma (Transform):** Envia o código para a API do Gemini com um **prompt de sistema altamente especializado**, que atua como um Auditor Sênior, instruindo a IA a validar uma lista rigorosa de regras de negócio (neste caso, a lógica `V7R5B1-RC1`).
3.  **Carrega (Load):** Recebe a análise da IA e a formata em um **relatório HTML completo e legível**, que serve como um artefato de documentação e auditoria para o seu versionamento.

---

### 🚀 Principais Funcionalidades

*   **🤖 Análise com IA Gemini:** Utiliza os modelos mais recentes do Google para uma análise de código profunda e contextual.
*   **📂 Interface Intuitiva:** Arraste e solte (`Drag & Drop`) seus arquivos `.py` para iniciar.
*   **📄 Relatórios HTML Detalhados:** Gera um documento HTML auto-contido com a análise, status de cada regra, evidências de código e recomendações.
*   **⚙️ Prompt de Auditoria Especializado:** O coração da ferramenta é o prompt que transforma o Gemini em um especialista na lógica de negócios `V7R5B1-RC1`, garantindo consistência na validação.
*   **⚡ Processamento Paralelo:** Audita múltiplos arquivos simultaneamente, aproveitando ao máximo os recursos do seu processador.
*   **✅ Fácil de Usar:** Sem configurações complexas. Apenas adicione sua chave de API e comece a usar.

---

### 🛠️ Começando

Para rodar este projeto, você precisará de Python, algumas bibliotecas e uma chave de API do Google AI.

#### 1. Pré-requisitos

*   Python 3.8 ou superior
*   Git

#### 2. Instalação

```bash
# Clone este repositório
git clone https://github.com/chaos4455/Replika-Code-Audit-Solution.git

# Entre no diretório do projeto
cdReplika-Code-Audit-Solution

# Instale as dependências (crie um arquivo requirements.txt)
pip install PyQt5 google-generativeai colorama
```

#### 3. 🔑 Obtendo sua Chave de API do Google (API Key)

A funcionalidade de IA depende de uma API Key. Você pode obtê-la gratuitamente.

**Opção 1: Google AI Studio (Recomendado para Iniciar)**

1.  Acesse o [Google AI Studio](https://aistudio.google.com/).
2.  Faça login com sua conta Google.
3.  Clique em **"Get API key"** no canto superior esquerdo.
4.  Clique em **"Create API key in new project"**.
5.  Copie a chave gerada. Ela se parecerá com `AIzaSy...`.

**Opção 2: Google Cloud / Vertex AI (Para usuários avançados/produção)**

Se você já usa o Google Cloud, pode habilitar a **Vertex AI API** no seu projeto e criar uma chave de API a partir do painel "APIs & Services".

#### 4. Configurando a Chave no Código

Abra o arquivo `.py` principal e insira a chave que você copiou no campo `API_KEY`:

```python
# --- Configuration Constants ---
CONFIG = {
    # ATENÇÃO: Cole sua chave aqui. NUNCA suba esta chave para um repositório público!
    "API_KEY": 'COLE_SUA_API_KEY_AQUI_AIzaSy...',
    # ... resto da configuração
}
```
> ⚠️ **AVISO DE SEGURANÇA:** Nunca, jamais, suba sua chave de API para um repositório público no GitHub. Se for o caso, use variáveis de ambiente ou um arquivo `.env` (adicionado ao `.gitignore`) para gerenciar suas chaves.

#### 5. Executando a Aplicação

Com tudo configurado, basta rodar o script:
```bash
Replika-Code-Audit-Solution.py
```

---

### 💻 Tecnologias Utilizadas

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyQt](https://img.shields.io/badge/PyQt-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8A2BE2?style=for-the-badge&logo=google-gemini&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

---

### 🤝 Contribuições

Sinta-se à vontade para abrir *issues* com sugestões, reportar bugs ou enviar *pull requests*. Toda contribuição é bem-vinda!

---

<div align="center">
    <p>Feito com ❤️ e 🤖 por <strong>Elias Andrade</strong></p>
    <p><strong>Replika AI Solutions</strong> - Maringá, Paraná 🇧🇷</p>
    <a href="https://www.linkedin.com/in/itilmgf/"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"/></a>
    <a href="https://github.com/chaos4455"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub"/></a>
</div>
