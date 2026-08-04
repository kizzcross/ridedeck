# Deploy — RideDeck (vanguard.kizzcross.com.br)

Roda **no mesmo VPS Hetzner do pokefit** (`178.105.169.230`), isolado em seus
próprios containers (db/redis/web/celery), atrás do mesmo nginx do host.

| | pokefit | **vanguard** |
|---|---|---|
| Domínio | pokefit.kizzcross.com.br | **vanguard.kizzcross.com.br** |
| Porta interna | 127.0.0.1:8001 | **127.0.0.1:8002** |
| Static/media | /var/www/pokefit/ | **/var/www/vanguard/** |
| DB/volume | pokefit / pgdata | vanguard / vg_pgdata |

> A stack sobe **isolada**: não toca no pokefit. Só compartilham a máquina e o nginx.

## 0. DNS
Aponte um registro **A** `vanguard.kizzcross.com.br → 178.105.169.230`.

## 1. Código no servidor
```bash
ssh root@178.105.169.230
sudo mkdir -p /var/www/vanguard/{static,media}
cd /opt   # ou onde o pokefit já vive
git clone <repo-do-vanguard> vanguard   # ou copie a pasta do projeto
cd vanguard/deploy
cp .env.production.example .env
nano .env   # gere o DJANGO_SECRET_KEY e defina POSTGRES_PASSWORD
```

Gerar o secret:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

## 2. Subir os containers
```bash
cd /opt/vanguard/deploy
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f web   # acompanha migrate + gunicorn
```
O `entrypoint.sh` roda `migrate` e `collectstatic` sozinho. O app fica em
`127.0.0.1:8002` (não exposto publicamente).

## 3. Nginx (host) + TLS
```bash
sudo cp /opt/vanguard/deploy/nginx/vanguard.conf /etc/nginx/sites-available/vanguard
sudo ln -sf /etc/nginx/sites-available/vanguard /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d vanguard.kizzcross.com.br
```
Certbot reescreve o `vanguard.conf` para 443 + redirect de 80.

## 4. Importar o catálogo + criar o admin (uma vez)
```bash
cd /opt/vanguard/deploy
# Catálogo real G+D (~15k cartas) + enriquecimento de nation/clan:
docker compose -f docker-compose.prod.yml exec web python manage.py import_catalog --source tcgcsv --series G,D --drop-fixture
docker compose -f docker-compose.prod.yml exec web python manage.py enrich_clans
# Platform Admin:
docker compose -f docker-compose.prod.yml exec web python manage.py create_platform_admin voce@exemplo.com --username voce
```

## 5. Atualizações (deploy de nova versão)
```bash
cd /opt/vanguard && git pull
cd deploy && docker compose -f docker-compose.prod.yml up -d --build
```
`migrate`/`collectstatic` rodam de novo no boot. Zero downtime não é garantido
(reinício rápido do container `web`).

## Notas de arquitetura em produção
- O **Django serve o SPA**: `SERVE_SPA=true` faz o WhiteNoise servir o build do
  Vite (`frontend_dist/` + `/assets/*`) e um catch-all devolve `index.html` para
  as rotas do React Router. O frontend chama a API **same-origin** (`/api/v1`).
- Admin/DRF static vão para `/static/` (servido pelo nginx via volume).
- Uploads em `/var/www/vanguard/media/` (volume persistente).
- Backups do banco: `docker compose exec db pg_dump -U vanguard vanguard > backup.sql`.

## CI/CD (automático)
Já configurado em [`.github/workflows/main.yml`](../.github/workflows/main.yml):
push em `main` roda o CI (ruff, migrations check, `check --deploy`, testes
backend com Postgres, typecheck + build + testes do frontend) e, passando, faz o
**deploy via SSH** (`git reset --hard` + `docker compose up -d --build`).

Setup dos secrets (mesma VPS/chave do pokefit, repo próprio) em
[`GITHUB_ACTIONS.md`](GITHUB_ACTIONS.md). Depois disso, o passo 5 acontece
sozinho a cada push.
