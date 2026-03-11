# Nutrients - Projeto Integrador (2024)

Aplicacao Django para definir metas nutricionais, montar refeicoes com dados da Tabela TACO e gerar um plano diario com revisao e impressao.

## 1. Stack atual

- Python 3.10+ (testado em 3.14 local)
- Django 5.2.x
- Django REST Framework
- django-allauth
- SQLite para desenvolvimento local
- Postgres via `DATABASE_URL` em producao
- Redis para cache/throttle em producao
- Frontend com Django Templates + JS puro

## 2. Funcionalidades principais

- Cadastro, login e logout
- Tela de objetivo com TMB, gasto diario e macros
- Planejador de dieta com refeicoes e itens dinamicos
- Busca de alimentos na API TACO sem recarregar a pagina
- Cadastro de novo alimento na API TACO via proxy interno
- Tela de revisao e impressao da dieta
- Healthcheck em `/health/`

## 3. Setup local rapido

Observacao: este projeto usa somente API TACO remota. Nao existe suporte para API local.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

App local: `http://127.0.0.1:8000/`

O projeto carrega `.env` automaticamente em `manage.py`, `conf/wsgi.py` e `conf/asgi.py`.

## 4. Variaveis de ambiente

Use `.env.example` como referencia.

Obrigatorias em producao:

- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY=<valor forte>`
- `DJANGO_ALLOWED_HOSTS=<dominio1,dominio2>`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://seu-dominio`
- `DATABASE_URL=postgresql://...`
- `REDIS_URL=redis://...`
- `DJANGO_SITE_ID=1`
- `TACO_API_BASE_URL=https://web-production-9a2e7.up.railway.app`
- `TACO_API_ALIMENTOS_READ_ENDPOINT=/alimentos/`
- `TACO_API_ALIMENTOS_WRITE_ENDPOINT=/alimentos/`

Integracao TACO:

- `TACO_API_BASE_URL` e obrigatoria em qualquer ambiente
- `TACO_API_BASE_URL` deve ser a base raiz publica da API
- `TACO_API_BASE_URL` nao pode usar `localhost`, `127.0.0.1` ou `0.0.0.0`
- `TACO_API_TOKEN` habilita escrita na API externa
- `TACO_API_TIMEOUT=8`
- `TACO_API_WRITE_TIMEOUT=10`
- `TACO_SEARCH_CACHE_SECONDS=60`

Cache e throttle:

- `REDIS_URL=redis://...`
- `CACHE_KEY_PREFIX=nutrients`
- `CACHE_TIMEOUT_SECONDS=300`
- `CACHE_SOCKET_TIMEOUT_SECONDS=5`
- `CACHE_SOCKET_CONNECT_TIMEOUT_SECONDS=5`

Runtime web:

- `WEB_CONCURRENCY=2`
- `GUNICORN_TIMEOUT=60`
- `GUNICORN_KEEPALIVE=5`

## 5. Deploy recomendado: Railway

O alvo oficial deste projeto e `Railway`.

Motivo tecnico:

- o projeto ja esta estruturado para `Django WSGI + Gunicorn + WhiteNoise`
- o bootstrap de producao ja existe em `Procfile` e `scripts/deploy/start.sh`
- a aplicacao exige `Postgres + Redis` em producao
- o fluxo operacional pode ficar reduzido a `git push`

`Vercel` nao e o alvo recomendado para esta stack. Ela exigiria adaptar o projeto para Python Functions/serverless, rever bootstrap, arquivos estaticos e operacao de migrations.

### 5.1 Contrato de runtime

Este repo ja possui:

- `Procfile` apontando para `bash scripts/deploy/start.sh`
- `scripts/deploy/start.sh` executando:
  - `python manage.py collectstatic --noinput`
  - `python manage.py migrate --noinput`
  - `gunicorn conf.wsgi:application --bind 0.0.0.0:$PORT`
- fail-fast em producao para envs obrigatorias

Nao e necessario rodar `collectstatic` ou `migrate` manualmente no deploy quando o service estiver usando esse bootstrap.

### 5.2 Fluxo principal: GitHub auto deploy

Fluxo diario do dev:

```powershell
git add .
git commit -m "sua mensagem"
git push
```

Configuracao inicial na Railway:

1. Suba o repositorio no GitHub.
2. Na Railway, crie um projeto a partir do repo.
3. Adicione os services gerenciados:
   - `PostgreSQL`
   - `Redis`
4. No service web, confirme que o start usa o `Procfile` ou configure `bash scripts/deploy/start.sh`.
5. No painel da Railway, habilite `Wait for CI` antes do auto deploy.
6. Gere o dominio publico do service web.

### 5.3 Env vars minimas do service web

Defina no painel da Railway:

- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY=<valor forte>`
- `DJANGO_ALLOWED_HOSTS=<seu-servico>.up.railway.app`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://<seu-servico>.up.railway.app`
- `DATABASE_URL=<fornecida pelo Postgres da Railway>`
- `REDIS_URL=<fornecida pelo Redis da Railway>`
- `DJANGO_SITE_ID=1`
- `TACO_API_BASE_URL=https://web-production-9a2e7.up.railway.app`
- `TACO_API_ALIMENTOS_READ_ENDPOINT=/alimentos/`
- `TACO_API_ALIMENTOS_WRITE_ENDPOINT=/alimentos/`
- `TACO_API_TOKEN=<token para escrita>`

Opcionais de runtime:

- `WEB_CONCURRENCY=2`
- `GUNICORN_TIMEOUT=60`
- `GUNICORN_KEEPALIVE=5`

### 5.4 Validacao apos deploy

Healthcheck obrigatorio:

- `GET /health/` deve retornar `200`

Fluxo funcional minimo:

1. login
2. salvar objetivo/TMB
3. abrir `Criar Dieta`
4. buscar alimentos na TACO
5. salvar dieta
6. abrir tela de impressao
7. testar POST local `/api/alimentos/criar/`

### 5.5 Fallback por Railway CLI

Se precisar operar sem o fluxo GitHub:

```powershell
railway login
railway link
railway up
```

Esse caminho e fallback. O fluxo oficial continua sendo `git push` com autodeploy.

## 6. Seguranca aplicada

- Configuracao sensivel por ambiente
- Bloqueio de startup em producao sem `DJANGO_SECRET_KEY`
- Bloqueio de startup em producao sem `DJANGO_ALLOWED_HOSTS`
- Bloqueio de startup em producao sem `DJANGO_CSRF_TRUSTED_ORIGINS`
- Bloqueio de startup em producao sem `DATABASE_URL`
- Bloqueio de startup em producao sem `REDIS_URL`
- Token da API TACO lido por env var, nunca hardcoded
- `SECURE_SSL_REDIRECT`, HSTS e cookies `Secure` com `DEBUG=false`
- `X_FRAME_OPTIONS=DENY` e `SECURE_CONTENT_TYPE_NOSNIFF`
- Rate limit DRF
- Bloqueio temporario por tentativas repetidas de login
- Politica de senha forte para cadastro

## 7. Performance aplicada

- Gunicorn para WSGI em producao
- WhiteNoise para servir arquivos estaticos
- `conn_max_age` para conexoes de banco
- Cache Redis para busca e throttle
- Busca TACO otimizada para evitar chamadas duplicadas
- Uso de `select_related` e agregacoes nos pontos criticos

## 8. Testes

Suite atual em `nutri/tests/`.

Cobertura principal:

- views de autenticacao
- fluxo de TMB e dieta
- integracao TACO
- healthcheck
- contratos de template

Rodar:

```powershell
python manage.py test nutri.tests
```

## 9. Checklist recomendado antes de producao

1. Rotacionar token TACO que tenha sido exposto fora do ambiente.
2. Definir `DJANGO_SECRET_KEY` forte e unica.
3. Configurar dominio real em `DJANGO_ALLOWED_HOSTS`.
4. Configurar `DJANGO_CSRF_TRUSTED_ORIGINS` com `https://`.
5. Confirmar `DATABASE_URL` do Postgres.
6. Confirmar `REDIS_URL` do Redis.
7. Confirmar `TACO_API_BASE_URL` publica e valida.
8. Confirmar `TACO_API_TOKEN` para escrita.
9. Rodar CI antes do deploy.

Runbook rapido de deploy Railway:

1. Confirmar repo conectado ao branch principal.
2. Confirmar `Wait for CI` habilitado.
3. Confirmar services `PostgreSQL` e `Redis` ativos.
4. Conferir envs obrigatorias no painel da Railway.
5. Validar `GET /health/` apos o deploy.

Runbook rapido de diagnostico TACO:

1. Conferir `TACO_API_BASE_URL`, `TACO_API_ALIMENTOS_READ_ENDPOINT`, `TACO_API_ALIMENTOS_WRITE_ENDPOINT` e `TACO_API_TOKEN`.
2. Confirmar que `TACO_API_BASE_URL` nao aponta para host local.
3. Validar `GET /health/`.
4. Validar busca local em `GET /api/alimentos/?search=arroz&page=1`.
5. Validar escrita local em `POST /api/alimentos/criar/`.
6. Lembrar que `/api/alimentos/criar/` e endpoint interno do Django; a escrita externa real vai para `POST /alimentos/` na API TACO.
7. Em erro `401/403`, revisar permissao/token no backend da API TACO.

Desbloqueio rapido local no PowerShell:

```powershell
$env:TACO_API_BASE_URL="https://web-production-9a2e7.up.railway.app"
$env:TACO_API_ALIMENTOS_READ_ENDPOINT="/alimentos/"
$env:TACO_API_ALIMENTOS_WRITE_ENDPOINT="/alimentos/"
python manage.py runserver
```

## 10. CI automatizado

Workflow em `.github/workflows/ci.yml` executa:

- `python manage.py check`
- `python manage.py makemigrations --check`
- `python manage.py test nutri.tests`
- smoke import de `conf.settings` em modo producao com envs minimas validas

## 11. Comandos uteis

```powershell
python manage.py check
python manage.py migrate
python manage.py migrate --plan
python manage.py collectstatic --noinput
python manage.py test nutri.tests
```
