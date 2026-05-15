#!/bin/bash
set -e

echo "Aguardando o banco de dados..."
until python -c "
import socket
s = socket.socket()
s.settimeout(2)
s.connect(('db', 5432))
s.close()
" 2>/dev/null; do
  echo "Banco ainda não disponível, aguardando..."
  sleep 2
done

echo "Banco disponível! Rodando migrations..."
alembic upgrade head

echo "Iniciando API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000