# Deploy do ITZ: Cloud Run + Neon + Cloudflare

Passo a passo para colocar o sistema no ar em `itzait.com.br` gastando o mínimo
possível (R$ 0/mês no volume esperado; só o domínio é pago).

```
itzait.com.br / www  → Frontend estático (Cloudflare Pages)
api.itzait.com.br    → Backend Django (Google Cloud Run, escala a zero)
admin.itzait.com.br  → o mesmo backend (abre direto no /admin/) — opcional
cdn.itzait.com.br    → Imagens (Cloudflare R2)
Banco                → Neon Postgres (hiberna sozinho)
Email                → Resend (SMTP)
Pagamentos           → Asaas → webhook em api.itzait.com.br/api/webhooks/asaas/
```

| Serviço               | Plano                   | Observação                                          |
| --------------------- | ----------------------- | --------------------------------------------------- |
| Google Cloud Run      | gratuito (2 mi req/mês) | pede cartão; configure alerta de orçamento          |
| Neon                  | Free                    | 1 GB; hiberna após 5 min parado (~1 s para acordar) |
| Cloudflare Pages + R2 | Free                    | R2 grátis até 10 GB                                 |
| Resend                | Free                    | limite diário de envios, folgado para matrículas    |
| registro.br           | ~R$ 40/ano              | domínio                                             |

> **Cold start**: com o backend parado, a primeira requisição leva poucos segundos
> (Cloud Run + Neon acordando). A home já chama a API ao abrir, então quando o
> aluno chega no checkout o servidor costuma estar acordado.

Ordem recomendada: 1 → 9. Anote cada valor marcado com 📝: eles vão para o
arquivo de variáveis do passo 6.

---

## 1. Domínio e DNS

1. [registro.br](https://registro.br) → registre `itzait.com.br`.
2. [Cloudflare](https://dash.cloudflare.com) → _Add a domain_ → `itzait.com.br` → plano **Free**.
3. No registro.br, troque os servidores DNS pelos dois _nameservers_ que o
   Cloudflare mostrar. A propagação pode levar algumas horas.

## 2. Banco de dados — Neon

1. [neon.com](https://neon.com) → crie a conta → _New project_:
   - Nome: `itz` · Postgres: o mais recente · Região: **AWS US East (Ohio) — us-east-2**
     (a mais próxima do Cloud Run em us-central1).
2. _Connect_ → desmarque **Connection pooling** → copie a connection string
   (`postgresql://...neon.tech/neondb?sslmode=require`).
   📝 `DATABASE_URL`

## 3. Imagens — Cloudflare R2

1. Cloudflare → **R2 Object Storage** (pode pedir um meio de pagamento; só cobra
   acima do gratuito) → _Create bucket_ `itz-media`.
2. `itz-media` → _Settings_ → _Custom Domains_ → _Add_ `cdn.itzait.com.br`.
   📝 `AWS_S3_CUSTOM_DOMAIN=cdn.itzait.com.br`
3. R2 → _Manage API Tokens_ → _Create API token_ → permissão **Object Read & Write**,
   restrita ao bucket `itz-media`.
   📝 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` e o endpoint
   `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` (📝 `AWS_S3_ENDPOINT_URL`)

## 4. Email — Resend

1. [resend.com](https://resend.com) → _Domains_ → _Add domain_ `itzait.com.br`.
2. Adicione no DNS do Cloudflare os registros que o Resend mostrar (SPF/DKIM) e
   clique em _Verify_. Sem isso os emails caem no spam.
3. _API Keys_ → _Create_ (permissão _Sending access_). 📝 `EMAIL_HOST_PASSWORD`
   (host `smtp.resend.com`, porta 587, usuário `resend`).

## 5. Google Cloud — projeto e conta

1. [console.cloud.google.com](https://console.cloud.google.com) → crie o projeto **`itz`**.
   📝 o **ID do projeto** (aparece no seletor de projetos; ex.: `itz-123456`).
2. _Faturamento_ → vincule um cartão.
3. _Faturamento_ → **Orçamentos e alertas** → _Criar orçamento_ → R$ 5/mês,
   alertas em 50 %, 90 % e 100 %. Você recebe email antes de qualquer cobrança.
4. Abra o **Cloud Shell** (ícone `>_` no topo do console) e rode:

```bash
gcloud config set project itzait
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
gcloud artifacts repositories create itz --repository-format=docker --location=us-central1
```

## 6. Backend no Cloud Run (primeiro deploy, manual)

Ainda no Cloud Shell:

```bash
git clone https://github.com/Moises-Rander/itz.git && cd itz
gcloud builds submit --tag us-central1-docker.pkg.dev/$(gcloud config get project)/itz/itz-api:latest
```

Crie o arquivo de variáveis **pelo editor do Cloud Shell** (botão _Abrir editor_),
em `~/env.yaml` — fora da pasta do repositório, para nunca ser versionado:

```yaml
DEBUG: "False"
SECRET_KEY: "cole uma chave longa e aleatória" # gere com: python3 -c "import secrets;print(secrets.token_urlsafe(50))"
ALLOWED_HOSTS: "api.itzait.com.br,admin.itzait.com.br"
CSRF_TRUSTED_ORIGINS: "https://api.itzait.com.br,https://admin.itzait.com.br"
CORS_ALLOWED_ORIGINS: "https://itzait.com.br,https://www.itzait.com.br"
FRONTEND_URL: "https://itzait.com.br"
BACKEND_URL: "https://api.itzait.com.br"
NUM_PROXIES: "1"
DATABASE_URL: "postgresql://...neon.tech/neondb?sslmode=require"

EMAIL_BACKEND: "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST: "smtp.resend.com"
EMAIL_PORT: "587"
EMAIL_HOST_USER: "resend"
EMAIL_HOST_PASSWORD: "re_..."
EMAIL_USE_TLS: "True"
DEFAULT_FROM_EMAIL: "Instituto de Teologia Zait <noreply@itzait.com.br>"
ADMIN_EMAIL: "secretaria@itzait.com.br"
REITOR_EMAIL: "email-do-reitor@..."
INSTITUICAO_NOME: "Instituto de Teologia Zait"
INSTITUICAO_CONTATO_EMAIL: "contato@itzait.com.br"
INSTITUICAO_CONTATO_TELEFONE: "(98) 98833-9224"
SEDE_ENDERECO: "Rua Transjordânia, 235 - Recanto Vinhais, São Luís - MA, 65070-616"

# Comece pelo SANDBOX do Asaas; troque para produção depois do teste (passo 9).
ASAAS_FAKE: "False"
ASAAS_BASE_URL: "https://sandbox.asaas.com/api/v3"
ASAAS_API_KEY: "$aact_..."
ASAAS_WEBHOOK_TOKEN: "outra chave longa e aleatória"

USE_S3: "True"
AWS_ACCESS_KEY_ID: "..."
AWS_SECRET_ACCESS_KEY: "..."
AWS_STORAGE_BUCKET_NAME: "itz-media"
AWS_S3_ENDPOINT_URL: "https://<ACCOUNT_ID>.r2.cloudflarestorage.com"
AWS_S3_CUSTOM_DOMAIN: "cdn.itzait.com.br"
```

Crie o job de migrações, rode-o e publique o backend:

```bash
IMG=us-central1-docker.pkg.dev/$(gcloud config get project)/itz/itz-api:latest

gcloud run jobs create itz-migrate --image $IMG --region us-central1 \
  --env-vars-file ~/env.yaml --command python --args manage.py,migrate
gcloud run jobs execute itz-migrate --region us-central1 --wait

gcloud run deploy itz-api --image $IMG --region us-central1 --allow-unauthenticated \
  --env-vars-file ~/env.yaml --cpu 1 --memory 512Mi \
  --min-instances 0 --max-instances 2 --cpu-boost
```

O deploy mostra a URL do serviço (`https://itz-api-....run.app`). Abra
`<URL>/api/catalogo/` — deve responder `[]`.

**Administrador** — no seu computador, apontando para o Neon (o
`DATABASE_URL` só vale para este comando):

```bash
cd itz && source venv/bin/activate
DATABASE_URL='postgresql://...neon.tech/neondb?sslmode=require' python manage.py createsuperuser
```

Depois apague o `env.yaml` do Cloud Shell: `rm ~/env.yaml`. As variáveis ficam
guardadas no serviço e no job (para mudar uma depois: Cloud Run → `itz-api` →
_Editar e implantar nova revisão_ → _Variáveis_; repita no job `itz-migrate`).

## 7. Domínio da API + deploy automático

**Domínio `api.itzait.com.br`:**

```bash
gcloud domains verify itzait.com.br        # abre o Search Console: adicione o TXT no Cloudflare
gcloud beta run domain-mappings create --service itz-api --domain api.itzait.com.br --region us-central1
gcloud beta run domain-mappings create --service itz-api --domain admin.itzait.com.br --region us-central1   # opcional
```

No Cloudflare, crie os registros pedidos (normalmente `CNAME api → ghs.googlehosted.com`)
com a **nuvem cinza (DNS only)** — o certificado HTTPS é emitido pelo Google
(pode levar de 15 min a algumas horas).

**Deploy automático a cada push na `main`:**

1. Dê ao Cloud Build permissão para publicar:

```bash
PN=$(gcloud projects describe $(gcloud config get project) --format='value(projectNumber)')
SA=$PN-compute@developer.gserviceaccount.com
for R in run.admin iam.serviceAccountUser artifactregistry.writer logging.logWriter; do
  gcloud projects add-iam-policy-binding $(gcloud config get project) --member serviceAccount:$SA --role roles/$R
done
```

2. Console → **Cloud Build** → _Gatilhos_ → _Conectar repositório_ → GitHub →
   `Moises-Rander/itz` → _Criar gatilho_:
   - Região `us-central1` · Evento: _Push para uma ramificação_ · Ramificação `^main$`
   - Configuração: _Arquivo do Cloud Build_ → `cloudbuild.yaml`
   - Conta de serviço: a **Compute Engine default service account** (`...-compute@developer...`)

A partir daí, cada push na `main` monta a imagem, roda as migrações e publica.

## 8. Frontend — Cloudflare Pages

1. Cloudflare → **Workers & Pages** → _Create_ → _Pages_ → _Connect to Git_ →
   `Moises-Rander/itz`.
2. Configuração de build:
   - _Framework preset_: Vite · _Build command_: `npm run build`
   - _Build output directory_: `dist` · _Root directory_: `frontend`
3. _Environment variables_ (Production):
   - `NODE_VERSION` = `22`
   - `VITE_API_URL` = `https://api.itzait.com.br/api`
   - `VITE_CONTATO_EMAIL`, `VITE_CONTATO_TELEFONE`, `VITE_CONTATO_WHATSAPP`,
     `VITE_CONTATO_INSTAGRAM`, `VITE_CONTATO_ENDERECO`, `VITE_CONTATO_MAPA_COORDS`,
     `VITE_HERO_IMAGEM` (veja `frontend/.env.example`).
     > O Vite grava essas variáveis no build: se mudar alguma, faça _Retry deployment_.
4. _Custom domains_ → adicione `itzait.com.br` e `www.itzait.com.br`.

O arquivo `frontend/public/_redirects` já faz as rotas internas (ex.: `/cursos/hebraico-basico`)
funcionarem ao recarregar a página. Cada push na `main` publica o frontend sozinho.

## 9. Asaas

1. Asaas (sandbox primeiro) → **Integrações → Webhooks** → _Adicionar_:
   - URL: `https://api.itzait.com.br/api/webhooks/asaas/`
   - Token de autenticação: o mesmo `ASAAS_WEBHOOK_TOKEN` do passo 6
   - Eventos: `PAYMENT_CONFIRMED` e `PAYMENT_RECEIVED`
2. Cadastre um curso de teste no Admin e faça uma matrícula com PIX e outra com
   cartão (cartões de teste na documentação do Asaas).
3. Deu certo? Troque para produção: `ASAAS_BASE_URL=https://api.asaas.com/v3` e a
   chave de produção (no serviço **e** no job), e repita o cadastro do webhook na
   conta de produção.

## 10. Conteúdo inicial (Admin)

Acesse `https://admin.itzait.com.br/` e cadastre, nesta ordem:

1. **Professores** (marque _exibir na home_ para os destaques).
2. **Cursos**: resumo, descrição, carga horária, imagem e as **aulas** (na própria tela).
3. **Formações**: os mesmos dados do curso + os **módulos** (na própria tela) →
   _editar aulas_ de cada módulo.
4. **Turmas de curso** e **Turmas de formação**: datas, vagas, preço, professores e
   horários. Status _Publicada_ para aparecer; a matrícula fica aberta até o dia de início.
5. **Taxas de parcelamento** (acréscimo de 2x a 12x repassado ao aluno; sem linha = sem juros).
6. **Conteúdo institucional** (`HERO`, `SOBRE`, `MISSAO`, `VISAO`, `VALORES`),
   **Membros da equipe** e **Depoimentos**.
7. Opcional: **Promoções** e **Cupons**.

## 11. Checklist final

- [ ] `https://itzait.com.br` abre e mostra os cursos (consome a API).
- [ ] Login no `/admin/` funciona sob HTTPS.
- [ ] Matrícula com PIX (valor baixo): QR Code → pagamento → página confirma sozinha →
      emails "matrícula confirmada" (aluno) e "nova matrícula" (reitor).
- [ ] Matrícula com cartão parcelado; depois _Cancelar e estornar_ no Admin e confira o estorno no Asaas.
- [ ] Emails chegam (não no spam) — SPF/DKIM ok.
- [ ] Imagem enviada no Admin aparece no site (R2 + `cdn.itzait.com.br`).

---

## Manutenção

- **Deploy**: `git push` na `main` → Cloud Build (backend + migrações) e Cloudflare Pages (frontend).
- **Logs/erros**: Cloud Run → `itz-api` → _Registros_. Para alertas, configure `SENTRY_DSN`.
- **Custos**: o alerta de orçamento avisa. `--max-instances 2` limita o gasto mesmo com picos.
- **Backup**: o Neon guarda o histórico recente e permite restaurar um ponto no tempo;
  para algo permanente, rode periodicamente
  `pg_dump "$DATABASE_URL" > backup-$(date +%F).sql` no seu computador.
- **Testes locais**: `python manage.py test`.
