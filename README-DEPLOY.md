# Deploy do ITZ — Render (backend) + Vercel (frontend)

Guia passo a passo para colocar o sistema no ar em `itzait.com.br`
(troque pelo domínio escolhido — tudo é por variável de ambiente).

Arquitetura:

```
itzait.com.br        → Frontend (Vercel, estático)
api.itzait.com.br    → Backend Django + gunicorn (Render)
                        ├── PostgreSQL (Render)
                        ├── Mídia → Cloudflare R2 (S3) — imagens públicas
                        ├── Email → Resend/SES (SMTP)
                        └── Asaas (produção) → webhook em /api/webhooks/asaas/
```

---

## Pré-requisitos
- Contas: **GitHub**, **Render**, **Vercel**, **Cloudflare** (R2 + DNS), **Resend** (email), **Asaas** (produção).
- Node 20 para buildar o front localmente (`nvm use 20`).

---

## Passo 0 — Subir o código no GitHub
```bash
cd /Users/moises/itz
git init
git add .
git commit -m "ITZ: sistema completo (backend + frontend)"
# crie um repositório vazio no GitHub e:
git remote add origin git@github.com:SEU_USUARIO/itz.git
git branch -M main
git push -u origin main
```
Confirme que `.env`, `db.sqlite3`, `venv/`, `media/`, `staticfiles/`, `frontend/node_modules/` e `frontend/.env` **não** foram commitados.

## Passo 1 — Comprar o domínio
- **[registro.br](https://registro.br)** → registre `itzait.com.br` (~R$40/ano).
- Recomendado: mover o DNS para o **Cloudflare** (grátis) — facilita subdomínios e CDN.
  No Cloudflare: *Add site* → siga a troca de nameservers no registro.br.

## Passo 2 — Storage de mídia (Cloudflare R2)
Só há imagens públicas (cursos, professores, institucional) — um bucket basta.

1. Cloudflare → **Storage & databases → R2** → *Create bucket* `itz-media`.
2. Tornar o bucket público:
   - `itz-media → Settings → Custom Domains → Add` → `cdn.itzait.com.br` (requer o domínio no Cloudflare), **ou** `Public Development URL → Enable` (dá uma URL `pub-xxxx.r2.dev` para começar/testar).
   - O domínio/URL público resultante vira `AWS_S3_CUSTOM_DOMAIN`.
3. Credenciais: **R2 → Overview → `{ } API` → Manage API Tokens → Create** com permissão *Object Read & Write* (aplicada ao bucket). Anote `Access Key ID`, `Secret Access Key` e o **Endpoint S3** (`https://<ACCOUNT_ID>.r2.cloudflarestorage.com`).
   - Variáveis: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME=itz-media`, `AWS_S3_ENDPOINT_URL=...`, `AWS_S3_CUSTOM_DOMAIN=cdn.itzait.com.br` (ou a URL `pub-xxxx.r2.dev`).

## Passo 3 — Email (Resend)
1. [resend.com](https://resend.com) → *Add Domain* `itzait.com.br` → adicione os registros **SPF/DKIM** no DNS (Cloudflare). Sem isso os emails caem no spam.
2. Crie uma API key e obtenha as credenciais **SMTP** (host `smtp.resend.com`, porta `587`, user `resend`, senha = a API key).

## Passo 4 — Backend no Render (Blueprint)
1. Render → **New → Blueprint** → conecte o repo. O `render.yaml` cria o **Web Service** `itz-api` + o **Postgres** `itz-db`.
2. Em **itz-api → Environment**, preencha as variáveis marcadas `sync:false`:
   - Email: `EMAIL_HOST=smtp.resend.com`, `EMAIL_HOST_USER=resend`, `EMAIL_HOST_PASSWORD=<api key>`, `REITOR_EMAIL=<email do reitor>` (recebe os dados de cada nova matrícula).
   - Asaas: `ASAAS_API_KEY=<chave de produção>`, `ASAAS_WEBHOOK_TOKEN=<gere um token forte>`.
   - R2: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_CUSTOM_DOMAIN`.
   - (opcional) `SENTRY_DSN`.
   - Confira que `DEBUG=False`, `ALLOWED_HOSTS=api.itzait.com.br`, `USE_S3=True` e as URLs de front/back estão certas.
3. O deploy roda automaticamente: `collectstatic` + `migrate` (build) e `gunicorn` (start).
4. **Domínio**: itz-api → *Settings → Custom Domains* → adicione `api.itzait.com.br` (Render dá o alvo do CNAME).
5. **Superusuário**: itz-api → *Shell* →
   ```bash
   python manage.py createsuperuser
   ```

## Passo 5 — Frontend no Vercel
1. Vercel → **Add New → Project** → importe o repo → **Root Directory: `frontend`** (framework Vite, detectado).
2. **Environment Variables**:
   - `VITE_API_URL = https://api.itzait.com.br/api`
   - `VITE_CONTATO_*`, `VITE_HERO_IMAGEM` etc. (veja `frontend/.env.example`).
   > Vite "assa" essas variáveis no build — se mudar, faça *Redeploy*.
3. Deploy. O `frontend/vercel.json` garante o fallback de SPA (deep links).
4. **Domínio**: Vercel → *Settings → Domains* → adicione `itzait.com.br` e `www.itzait.com.br`.

## Passo 6 — DNS (Cloudflare)
| Tipo  | Nome | Valor |
|-------|------|-------|
| CNAME | `api` | alvo fornecido pelo Render |
| A/CNAME | `@` (raiz) e `www` | alvos fornecidos pela Vercel |
| CNAME | `cdn` | endpoint público do bucket R2 (se usar) |
| TXT/CNAME | SPF/DKIM | fornecidos pelo Resend |

HTTPS é emitido automaticamente por Render e Vercel.

## Passo 7 — Asaas (produção)
1. Asaas → **Integrações → Webhooks** → *Adicionar*:
   - URL: `https://api.itzait.com.br/api/webhooks/asaas/`
   - Token de autenticação: **o mesmo** valor de `ASAAS_WEBHOOK_TOKEN`.
   - Eventos: `PAYMENT_CONFIRMED` e `PAYMENT_RECEIVED`.
2. Teste com um pagamento real de valor baixo (ou primeiro em sandbox com `ASAAS_FAKE`/sandbox key).

## Passo 8 — Conteúdo inicial (Django Admin)
Acesse `https://api.itzait.com.br/admin/` e cadastre:
1. **Professores** (marque *exibir na home* para os destaques).
2. **Cursos** (cada disciplina avulsa: ementa, carga horária, imagem).
3. **Graduações** → módulos (na própria tela) → *editar cursos* de cada módulo.
4. **Turmas de curso**: datas, vagas, preço, professores e horários. Status *Publicada* para aparecer.
5. **Turmas de graduação**: escolha uma turma de curso para cada curso da grade e o preço do pacote.
6. **Taxas de parcelamento** (acréscimo de 2x a 12x repassado ao aluno; sem linha = sem juros).
7. Opcional: **Promoções** e **Cupons**.
- **Conteúdo institucional** (seções `HERO`, `SOBRE`, `MISSAO`, `VISAO`, `VALORES`), **Membros da equipe** e **Depoimentos** — lembre de marcar *publicado/ativo*.

## Passo 9 — Checklist final
- [ ] `https://itzait.com.br` abre e consome a API (Home mostra cursos/depoimentos).
- [ ] Login no `/admin/` funciona sob HTTPS (cookies seguros).
- [ ] Matrícula de teste com PIX (valor baixo): QR Code → pagamento → página confirma sozinha → emails "matrícula confirmada" (aluno) e "nova matrícula" (reitor).
- [ ] Matrícula de teste com cartão parcelado; depois *Cancelar e estornar* no Admin e confira o estorno no Asaas.
- [ ] Emails chegam (não no spam) — SPF/DKIM ok.

---

## Manutenção
- **Migrações**: a cada `git push` na `main`, o Render re-builda e roda `migrate` automaticamente.
- **Backups**: ative o backup automático do Postgres no Render; no R2, ative *versioning* do bucket.
- **Logs/erros**: veja logs no Render; configure `SENTRY_DSN` para alertas de erro.
- **Rodar testes localmente**: `python manage.py test`.

## Alternativa: VPS + Docker
Se preferir um único servidor (mais barato em escala, mais trabalho): VPS (Hetzner/DigitalOcean) + Docker Compose (gunicorn + Postgres + Nginx) + Certbot para HTTPS. Posso gerar os `Dockerfile`/`docker-compose.yml`/Nginx se optar por esse caminho.
