// Gera dist/sitemap.xml depois do build: páginas fixas + cursos e formações
// com turma aberta (lidos da API). Se a API não responder, publica só as
// páginas fixas em vez de quebrar o deploy.
import { writeFileSync } from 'node:fs'

const SITE = (process.env.VITE_SITE_URL || 'https://itzait.com.br').replace(/\/$/, '')
const API = (process.env.VITE_API_URL || 'https://api.itzait.com.br/api').replace(/\/$/, '')

const paginas = ['/', '/cursos', '/sobre', '/contato', '/termos']

try {
  const resp = await fetch(`${API}/catalogo/`, { signal: AbortSignal.timeout(15000) })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  for (const item of await resp.json()) {
    paginas.push(item.tipo === 'formacao' ? `/formacoes/${item.slug}` : `/cursos/${item.slug}`)
  }
} catch (erro) {
  console.warn(`sitemap: catálogo indisponível (${erro.message}); só páginas fixas.`)
}

const urls = paginas.map((p) => `  <url><loc>${SITE}${p}</loc></url>`).join('\n')
writeFileSync(
  'dist/sitemap.xml',
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
)
console.log(`sitemap: ${paginas.length} URLs`)
