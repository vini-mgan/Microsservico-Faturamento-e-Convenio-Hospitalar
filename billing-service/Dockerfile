FROM python:3.13-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos de dependências
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar tabelas no banco (será executado na inicialização se necessário)
# O serviço cria tabelas automaticamente se não existirem

# Expor porta
EXPOSE 8000

# Comando para rodar a aplicação
CMD ["python3", "run.py"]

