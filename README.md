# Nutrients - Projeto Integrador (2024)

Aplicacao Django para definir metas nutricionais (TMB/macros), montar refeicoes com dados da Tabela TACO e gerar um plano diario com impressao.

## 1. Stack atual

- Python 3.10+ (testado em 3.14 local)
- Django 5.2.x
- Django REST Framework
- django-allauth
- SQLite (local) ou Postgres via `DATABASE_URL` (deploy)
- Frontend com Django Templates + JS puro

## 2. Funcionalidades principais

- Cadastro/login/logout de usuario.
- Tela de objetivo (TMB, gasto diario, macros).
- Planejador de dieta com refeicoes e itens dinamicos.
- Busca de alimentos na API TACO sem recarregar pagina.
- Cadastro de novo alimento na API TACO (POST com token).
- Tela de revisao/impressao em formato profissional.
- Endpoint de healthcheck: `/health/`.

## 3. Setup local rapido (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

App: `http://127.0.0.1:8000/`

## 4. Variaveis de ambiente

Use `.env.example` como referencia.

Obrigatorias para producao:

- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY=<valor forte>`
- `DJANGO_ALLOWED_HOSTS=<dominio1,dominio2>`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://seu-dominio`
- `DATABASE_URL=postgresql://...`
- `REDIS_URL=redis://...`
- `TACO_API_BASE_URL=https://api-taco.exemplo.com`
- `DJANGO_SITE_ID=1`

Integracao TACO:

- `TACO_API_TOKEN=<token DRF para escrita>`
- `TACO_API_TIMEOUT=8`
- `TACO_API_WRITE_TIMEOUT=10`
- `TACO_SEARCH_CACHE_SECONDS=60`
- `LOGIN_MAX_ATTEMPTS=5`
- `LOGIN_BLOCK_SECONDS=300`

Cache Redis:

- `CACHE_KEY_PREFIX=nutrients`
- `CACHE_TIMEOUT_SECONDS=300`
- `CACHE_SOCKET_TIMEOUT_SECONDS=5`
- `CACHE_SOCKET_CONNECT_TIMEOUT_SECONDS=5`

Banco no deploy:

- `DATABASE_URL=postgresql://...`
- `DJANGO_DB_SSL_REQUIRE=true`
- `DJANGO_DB_CONN_MAX_AGE=600`

Runtime web (opcional):

- `WEB_CONCURRENCY=2`
- `GUNICORN_TIMEOUT=60`
- `GUNICORN_KEEPALIVE=5`

## 5. Deploy mais facil (Railway)

Este repo ja possui:

- `Procfile` apontando para `scripts/deploy/start.sh`
- startup padronizado: `collectstatic`, `migrate --noinput`, `gunicorn`
- fail-fast em producao para envs obrigatorias

Passo a passo:

1. Suba o repositório no GitHub.
2. Na Railway, crie um projeto e conecte o repo.
3. Adicione os services:
   - `PostgreSQL` (gera `DATABASE_URL`)
   - `Redis` (gera `REDIS_URL`)
4. No service web, configure env vars:
   - `DJANGO_DEBUG=false`
   - `DJANGO_SECRET_KEY=<valor forte>`
   - `DJANGO_ALLOWED_HOSTS=<dominio railway>`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://<dominio railway>`
   - `DATABASE_URL=<url postgres>`
   - `REDIS_URL=<url redis>`
   - `TACO_API_BASE_URL=<url publica da API TACO>`
   - `TACO_API_TOKEN=<token para escrita>`
   - `DJANGO_SITE_ID=1`
5. Garanta start command usando `Procfile` (ou configure manualmente: `bash scripts/deploy/start.sh`).
6. Faça deploy.

Healthcheck de monitoramento:

- `GET /health/` deve retornar `200` com status `ok`.

## 6. Seguranca aplicada

- Configuracao sensivel por ambiente.
- Bloqueio de startup em producao sem `DJANGO_SECRET_KEY`.
- Bloqueio de startup em producao sem `DJANGO_ALLOWED_HOSTS`.
- `SECURE_SSL_REDIRECT`, HSTS, cookies `Secure` (quando `DEBUG=false`).
- `X_FRAME_OPTIONS=DENY`, `SECURE_CONTENT_TYPE_NOSNIFF`.
- Token da API TACO lido por env var (`TACO_API_TOKEN`), nunca hardcoded.
- Limite de taxa DRF (`AnonRateThrottle` / `UserRateThrottle`).
- Bloqueio temporario por tentativas de login repetidas (`LOGIN_MAX_ATTEMPTS`).
- Cadastro com politica de senha forte (minimo 12 + maiuscula + minuscula + numero + simbolo).

## 7. Performance aplicada

- Gunicorn para WSGI em producao.
- WhiteNoise para servir arquivos estaticos.
- `conn_max_age` para conexoes de banco via `DATABASE_URL`.
- Busca TACO otimizada para evitar chamada duplicada em `create_diet`.
- Cache Redis (multi-instancia) para busca e throttle.
- `select_related` e agregacoes usadas nos pontos criticos.

## 8. Testes

Suite atual: `nutri/tests/`

- testes de views (auth, fluxo de dieta, API TACO, registro)
- testes de contrato de template (assets/layout esperado)
- testes de healthcheck

Rodar:

```powershell
python manage.py test nutri.tests
```

## 9. Checklist recomendado antes de producao

1. Rotacionar token TACO (token antigo exposto em conversa).
2. Definir `DJANGO_SECRET_KEY` forte e unica.
3. Configurar dominio real em `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS`.
4. Definir `DATABASE_URL` (Postgres) e `REDIS_URL` (obrigatorio em producao).
5. Definir `TACO_API_BASE_URL` publica (nao usar localhost em producao).
6. Definir `TACO_API_TOKEN` para habilitar POST de alimentos.
7. Rodar `python manage.py test nutri.tests` no pipeline de CI.
8. Rodar `python manage.py makemigrations --check` antes de cada deploy.
9. Validar fluxo critico apos deploy: login, TMB, criar dieta, salvar, imprimir, busca TACO e POST TACO.

## 10. CI automatizado (GitHub Actions)

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
