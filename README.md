# Insper Code Na Prática - Sistema de Processamento de Formulários

## 📋 Visão Geral

Sistema de processamento de formulários que recebe eventos de webhook do Tally.so, processa as respostas de forma assíncrona e gera relatórios personalizados para participantes.

## 🏗️ Arquitetura do Sistema

### Componentes Principais

- **Flask API**: Recebe webhooks do Tally.so
- **Redis**: Broker de mensagens para Celery
- **Celery Workers**: Processamento assíncrono das tarefas
- **PostgreSQL**: Armazenamento das respostas dos formulários
- **Docker**: Containerização de todos os serviços

### Fluxo de Dados

```mermaid
graph TD
    A[Tally.so] -->|Webhook Event| B[Flask API]
    B -->|Salva resposta| C[PostgreSQL]
    B -->|Envia task| D[Redis Queue]
    D -->|Processa task| E[Celery Worker]
    E -->|1. Calcula scores| F[Score Engine]
    E -->|2. Gera PDF| G[PDF Generator]
    E -->|3. Envia email| H[SMTP Server]
    F -->|Resultado| I[Email com PDF]
    G -->|PDF| I
    H -->|Email| J[Participante]
```

## 🔄 Processo de Processamento

### 1. Recebimento do Webhook
- Flask API recebe evento do Tally.so
- Valida e salva resposta no banco de dados
- Retorna ID do registro para uso na Task

### 2. Processamento Assíncrono
O Celery Worker executa 3 tarefas principais:

#### 📊 Cálculo de Scores
- Analisa respostas do formulário
- Aplica algoritmos de pontuação
- Gera métricas personalizadas

#### 📄 Geração de PDF
- Utiliza template base fornecido
- Preenche com dados do participante
- Gera relatório personalizado

#### 📧 Envio de Email
- Configuração SMTP
- Anexa PDF gerado
- Envia para o participante

## 🐳 Infraestrutura Docker

### Serviços Containerizados

```mermaid
graph LR
    A[Flask API Container] --> B[PostgreSQL Container]
    A --> C[Redis Container]
    C --> D[Celery Worker Container]
    D --> B
    D --> E[SMTP Server]
```

## 🚀 Como Executar

### Desenvolvimento Local
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar Flask API
python main.py

# Executar Celery Worker (terminal separado)
celery -A app.celery worker --loglevel=info
```

### Produção com Docker
```bash
# Subir todos os serviços
docker compose up -d

# Verificar logs
docker compose logs -f
```

## 🔧 Configuração

### Variáveis de Ambiente
```env
DATABASE_URL=postgresql://admin:password@postgres:5432/insper_forms
REDIS_URL=redis://redis:6379/0
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
TALLY_WEBHOOK_SECRET=your-webhook-secret
```

**Desenvolvido pelo Insper Code para Na Prática** 🎓
