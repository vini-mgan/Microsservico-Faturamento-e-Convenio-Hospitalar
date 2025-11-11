# Projeto de Arquitetura de Sistemas - Microsserviço de Faturamento & Convênios

Microsserviço de faturamento e gestão de convênios médicos. Implementado com FastAPI, seguindo padrões de arquitetura de microsserviços, observabilidade e segurança.

## Arquitetura

- **API REST**: FastAPI com documentação automática (Swagger/OpenAPI)
- **Banco de Dados**: MySQL para persistência de dados
- **Cache**: Redis para cache de tabelas TUSS e verificações de elegibilidade
- **Eventos**: Kafka para comunicação assíncrona entre serviços
- **Observabilidade**: Prometheus para métricas e health checks avançados

## Tecnologias

- **Python 3.13**
- **FastAPI**: Framework web moderno e rápido
- **SQLAlchemy**: ORM para MySQL
- **Redis**: Cache em memória
- **Kafka**: Streaming de eventos
- **Prometheus**: Métricas e monitoramento
- **Docker & Docker Compose**: Containerização

## 📋 Funcionalidades

### Claims (Guias)
- Criação de guias de faturamento
- Consulta e atualização de guias
- Listagem com filtros (paciente, status)
- Publicação de eventos `ClaimSubmitted` no Kafka

### Invoices (Contas)
- Criação de contas vinculadas a guias
- Consulta e listagem de contas
- Liquidação de contas
- Publicação de eventos `InvoiceSettled` no Kafka

### Eligibility (Elegibilidade)
- Verificação de elegibilidade de pacientes com convênios
- Cache Redis para otimização (TTL de 1 hora)
- Histórico de verificações

### Observabilidade
- Health checks básicos, readiness e liveness
- Métricas Prometheus (HTTP, negócio, dependências)
- Logging estruturado
- SLOs (Service Level Objectives)

### Segurança
- OAuth2/OIDC (configurável)
- RBAC/ABAC (Role-Based e Attribute-Based Access Control)
- TLS/mTLS (configurável)
- Middleware de autenticação e autorização

## Instalação e Execução

### Execução com Docker

```bash
cd billing-service
docker-compose up -d
```

- Verifique se os serviços estão rodando:
```bash
curl http://localhost:8000/health
```


### Execução Local 

1. Instale as dependências:
```bash
cd billing-service
pip install -r requirements.txt
```

2. Configure MySQL, Redis e Kafka localmente

3. Execute o serviço:
```bash
python3 run.py
```

- Documentação interativa:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints Principais

### Health Checks
- `GET /health` - Health check básico
- `GET /health/ready` - Readiness check (verifica dependências)
- `GET /health/live` - Liveness check

### Claims
- `POST /claims/` - Criar guia
- `GET /claims/{claim_id}` - Buscar guia por ID
- `GET /claims/` - Listar guias (com filtros opcionais)
- `PATCH /claims/{claim_id}` - Atualizar guia

### Invoices
- `POST /invoices/` - Criar conta
- `GET /invoices/{invoice_id}` - Buscar conta por ID
- `GET /invoices/` - Listar contas (com filtros opcionais)
- `POST /invoices/{invoice_id}/settle` - Liquidar conta

### Eligibility
- `POST /eligibility/check` - Verificar elegibilidade
- `GET /eligibility/history` - Histórico de verificações

### Métricas
- `GET /metrics` - Métricas do Prometheus
