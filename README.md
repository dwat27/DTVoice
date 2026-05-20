# DTVoice

> ⚠️ **Este projeto é um WIP (Work In Progress)** — pode conter bugs e está em desenvolvimento ativo.

**DTVoice** é um aplicativo Windows de conversão de fala em texto que usa um modelo local Whisper otimizado para Português Brasileiro. Pressione um atalho global e comece a ditar — o texto aparece onde seu cursor está.

## ✨ Funcionalidades

- 🎤 **Conversão de fala em texto** — transcreve áudio em texto usando IA local
- 🌍 **Otimizado para Português Brasileiro** — modelo `remynd/whisper-small-pt` (~466MB)
- ⌨️ **Atalho global** — Left Ctrl + Left Win para iniciar/parar gravação
- 📋 **3 modos de saída**:
  - **Injeção direta**: texto digitado onde está o cursor
  - **Área de transferência**: texto copiado para colar
  - **Popup**: notificação com opção de copiar
- 🔒 **Privacidade** — todo processamento é local, nada vai para a nuvem
- 💾 **Funciona offline** — após baixar o modelo, funciona sem internet
- 🖥️ **Bandeja do sistema** — roda minimizado, indicator visual de estado

## 📋 Requisitos

- **Sistema Operacional**: Windows 10/11 (64-bit)
- **Python**: Não necessário (executável standalone incluso)
- **Microfone**: Necessário para gravação

## 📥 Instalação

### Opção 1: Executável pré-compilado (Recomendado)

1. Baixe o arquivo `DTVoice.exe` da página de [Releases](https://github.com/dwat27/DTVoice/releases)
2. Execute `DTVoice.exe --startup` para adicionar ao iniciar do Windows (opcional)
3. Execute `DTVoice.exe --minimize` para iniciar minimizado na bandeja

### Opção 2: Executar pelo código-fonte

```powershell
# Clonar o repositório
git clone https://github.com/dwat27/DTVoice.git
cd dtvoice

# Criar ambiente virtual
python -m venv venv
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar
python main.py --minimize
```

## 🚀 Como Usar

### Iniciar Gravação
Pressione **Left Ctrl + Left Win** simultaneamente para iniciar a gravação.

### Parar Gravação
Pressione **Left Ctrl + Left Win** novamente para parar e transcrever.

### Menu da Bandeja
- **Iniciar Gravação** / **Parar Gravação** — controle manual
- **Configurações** — mostra configurações atuais (apenas leitura na v1)
- **Sair** — fecha o aplicativo

### Opções de Linha de Comando

```powershell
dtvoice.exe --help          # Mostra ajuda
dtvoice.exe --version       # Mostra versão
dtvoice.exe --startup        # Adiciona ao iniciar do Windows
dtvoice.exe --no-startup     # Remove do iniciar do Windows
dtvoice.exe --minimize       # Inicia minimizado na bandeja
```

## ⚙️ Configuração

### Local dos Arquivos
- **Logs**: `%APPDATA%/dtvoice/logs/`
- **Modelo**: `%APPDATA%/dtvoice/models/` (baixado automaticamente na primeira transcrição)

### Modelo de Linguagem
O app usa o modelo `remynd/whisper-small-pt` do Hugging Face (~466MB):
- **WER**: ~10% (taxa de erro de palavra)
- **Otimizado**: Português Brasileiro
- **Performance**: CPU-friendly, funciona em máquinas modestas

### Configurações Atuais (v1)
| Configuração | Valor |
| ------------ | ----- |
| Atalho | Left Ctrl + Left Win |
| Modo de saída | Injeção → Área de transferência → Popup |
| Auto-stop | 60 segundos |
| Detecção de silêncio | 3 segundos |



## 🧠 Modelos de IA Suportados

O DTVoice suporta vários modelos Whisper. O modelo padrão é otimizado para Português Brasileiro, mas você pode escolher outros modelos mais tarde.

### Modelos Disponíveis

| Modelo | Idioma | Tamanho | WER | Descrição |
| ------ | ------- | ------- | --- | --------- |
| `remynd/whisper-small-pt` | PT-BR | 466 MB | ~10% | Recomendado para PT-BR |
| `Systran/faster-whisper-small-pt` | PT-BR | 466 MB | ~8% | Variante mais rápida para PT-BR |
| `Systran/faster-whisper-base` | Multi | 140 MB | ~12% | Multi-idioma, menor |
| `Systran/faster-whisper-medium` | Multi | 1500 MB | ~6% | Multi-idioma, maior precisão |
| `Systran/faster-whisper-large-v3` | Multi | 3100 MB | ~4% | Multi-idioma, máxima precisão |
| `openai/whisper-base` | Multi | 140 MB | ~15% | OpenAI base, multi-idioma |
| `openai/whisper-small` | Multi | 466 MB | ~11% | OpenAI small, multi-idioma |

### Trocar Modelo

Na versão atual, o modelo pode ser trocado pelo menu da bandeja:
1. Clique no ícone DTVoice na bandeja
2. Vá em **Configurações** → **Trocar Modelo**
3. Selção o modelo desejado

> ⚠️ Ao trocar de modelo, o novo modelo será baixado automaticamente na primeira vez.

### Como Funciona
- Cada modelo é baixado para `%APPDATA%/dtvoice/models/{model_id}/`
- Modelos baixados ficam disponíveis offline
- Você pode ter múltiplos modelos instalados simultaneamente

## 🔧 Tecnologias

| Componente | Tecnologia |
| ---------- | ---------- |
| Modelo de IA | [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) + Whisper |
| Captura de áudio | sounddevice |
| Atalho global | pynput |
| Bandeja do sistema | pystray + Pillow |
| Injeção de texto | Win32 API (WM_SETTEXT) |
| Notificações | plyer |
| Área de transferência | pyperclip |

## 📁 Estrutura do Projeto

```
dtvoice/
├── main.py                  # Ponto de entrada + integração
├── system_tray.py           # Ícone da bandeja + menu
├── hotkey.py                # Listener de atalho global
├── audio_capture.py         # Gravação de áudio (16kHz mono)
├── transcriber.py           # Pipeline de transcrição Whisper
├── model_loader.py          # Carregamento preguiçoso do modelo
├── recording_state_machine.py  # Máquina de estados da gravação
├── output_dispatcher.py     # Dispatcher de modos de saída
├── text_injector.py         # Injeção de texto Win32
├── clipboard_output.py      # Integração com área de transferência
├── popup_ui.py              # Notificações popup
├── config.py                # Configurações do aplicativo
├── requirements.txt         # Dependências Python
├── pyproject.toml          # Configuração do projeto
└── dtvoice.spec            # Spec do PyInstaller
```

## 🐛 Problemas Conhecidos

- **Permissão de microfone**: Na primeira execução, o Windows pode pedir permissão para o microfone. Conceda pelo Settings > Privacy > Microphone.
- **Instalação sem admin**: O app não requer privilégios de administrador. Se precisar de ajuda, execute como administrator uma vez para registrar o atalho global.

## 🔒 Privacidade

**DTVoice é 100% offline e seguro para dados.**

### O que coletamos:
- **Nada**. O aplicativo não coleta, transmite ou armazena nenhum dado pessoal em servidores externos.

### Como funcionam os dados:
| Dado | Armazenamento | Onde |
| ---- | ------------- | ---- |
| Histórico de transcrições | Local | `%APPDATA%/dtvoice/history.json` |
| Configurações | Local | `%APPDATA%/dtvoice/settings.json` |
| Modelo de IA | Local | `%APPDATA%/dtvoice/models/` |
| Logs | Local | `%APPDATA%/dtvoice/logs/` |

### Permissões necessárias:
- **Microfone**: Para gravar áudio (apenas quando você inicia gravação)
- **Registro do Windows**: Apenas `HKCU\...\Run` para iniciar com o sistema (opcional)

### Seus direitos:
- Todos os dados ficam no seu PC
- Você pode apagar o histórico a qualquer momento (Configurações > Histórico > Limpar)
- Não há telemetry, analytics ou conexão com servidores externos

### Compliance:
- ✅ **LGPD (Brasil)**: Dados 100% locais, nenhum dado pessoal enviado para fora
- ✅ **GDPR (UE)**: Sem coleta de dados
- ✅ **CCPA (Califórnia)**: Sem venda de dados

## 🚧 Roadmap

- [x] Interface gráfica para configurações
- [x] Seleção de idioma/modelo
- [x] Histórico de transcrições
- [x] Atalhos customizáveis
- [x] Tema claro/escuro

## 📄 Licença

Este projeto está licenciado sob a MIT License — see [LICENSE](LICENSE) for details.

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor, abra uma issue primeiro para discutir mudanças maiores.

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'feat: nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

Desenvolvido com ❤️ para a comunidade brasileira de usuários de Windows.