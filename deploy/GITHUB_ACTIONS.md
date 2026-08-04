# GitHub Actions — CI + deploy automático

Push na branch **`main`** dispara ([.github/workflows/main.yml](../.github/workflows/main.yml)):

1. **CI** — ruff, migrations check, `check --deploy`, testes backend (com Postgres),
   typecheck + build + testes do frontend.
2. **Deploy** — SSH no Hetzner: `git reset --hard origin/main` +
   `docker compose -f deploy/docker-compose.prod.yml up -d --build`.

> **Mesma VPS do pokefit, isolado.** O vanguard vive em `/opt/vanguard`, com seu
> próprio compose, containers e porta (`127.0.0.1:8002`) — não toca no pokefit.
> Como é a **mesma máquina**, os secrets de deploy são os **mesmos** do pokefit.

## Secrets (Repository secrets)

**Settings → Secrets and variables → Actions → Repository secrets**

| Secret | Valor | Observação |
|--------|--------|-----------|
| `DEPLOY_HOST` | `178.105.169.230` | mesma VPS do pokefit |
| `DEPLOY_USER` | `root` | |
| `DEPLOY_SSH_KEY` | chave **privada** completa (`BEGIN…END`) | pode reusar a mesma chave já autorizada no VPS |
| `DEPLOY_SSH_PASSPHRASE` | senha da chave | **só** se a privada tiver passphrase |

Como a VPS é a mesma, a chave pública que você já colocou em
`~/.ssh/authorized_keys` para o pokefit **já serve** — basta colar a mesma privada
em `DEPLOY_SSH_KEY` deste repositório (secrets não são compartilhados entre repos).

## Preparar o servidor (uma vez)

```bash
ssh root@178.105.169.230
sudo mkdir -p /var/www/vanguard/{static,media}
cd /opt && git clone git@github.com:<voce>/vanguard.git vanguard
cd vanguard && git remote set-url origin git@github.com:<voce>/vanguard.git
cd deploy && cp .env.production.example .env && nano .env   # secret + senha do banco
```

Depois disso, todo push em `main` faz o deploy sozinho. Nginx + TLS seguem o
[DEPLOY.md](DEPLOY.md) (passo 3), uma vez só.

## Por que o CI precisa de Postgres

Diferente do pokefit (sqlite no CI), o vanguard usa **Postgres** nos testes
(FTS/trigram, constraints). O workflow sobe um `services: postgres:16` e roda o
`pytest` contra ele.

## Ver logs

GitHub → **Actions** → **main** → job **Deploy to Hetzner**. No VPS:

```bash
cd /opt/vanguard/deploy
docker compose -f docker-compose.prod.yml logs --tail=80 web
```

## Erros comuns

| Log | Causa | Solução |
|-----|--------|---------|
| `ssh: no key found` | Secret vazio / sem `BEGIN PRIVATE KEY` | Recolar `DEPLOY_SSH_KEY` (privada inteira) |
| `passphrase protected` | Chave com senha | Criar `DEPLOY_SSH_PASSPHRASE` ou usar chave com `-N ""` |
| `unable to authenticate` | Pública não está no VPS | `authorized_keys` no servidor; teste `ssh -i` no Mac |
| CI falha em `pytest` | Serviço Postgres não subiu | Ver health check do service `postgres` no log do job |
