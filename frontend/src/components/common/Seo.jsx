import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { INSTITUICAO, HERO } from '@/lib/config'

// Endereço público do site: base dos links canônicos e do og:url.
export const SITE_URL = (import.meta.env.VITE_SITE_URL || 'https://itzait.com.br').replace(/\/$/, '')

const DESCRICAO_PADRAO =
  'Instituto de Teologia Zait (ITZ) — formação teológica em São Luís - MA, ' +
  'com excelência acadêmica e compromisso com a fé.'

// Cria (ou reaproveita) uma tag no <head> e define seus atributos.
function tagHead(seletor, criar) {
  let el = document.head.querySelector(seletor)
  if (!el) {
    el = criar()
    document.head.appendChild(el)
  }
  return el
}

function meta(atributo, chave, conteudo) {
  const el = tagHead(`meta[${atributo}="${chave}"]`, () => {
    const m = document.createElement('meta')
    m.setAttribute(atributo, chave)
    return m
  })
  el.setAttribute('content', conteudo)
}

// Título, descrição, link canônico e Open Graph da página atual.
// O Google executa o JavaScript do site, então lê estes valores ao indexar.
export default function Seo({ titulo, descricao, imagem, noindex = false }) {
  const { pathname } = useLocation()

  useEffect(() => {
    const tituloCompleto = titulo ? `${titulo} | ${INSTITUICAO.nome}` : `${INSTITUICAO.nome} (${INSTITUICAO.sigla})`
    const desc = (descricao || DESCRICAO_PADRAO).replace(/\s+/g, ' ').trim().slice(0, 300)
    const url = SITE_URL + (pathname === '/' ? '/' : pathname.replace(/\/$/, ''))

    document.title = tituloCompleto
    meta('name', 'description', desc)
    meta('name', 'robots', noindex ? 'noindex, nofollow' : 'index, follow')
    meta('property', 'og:title', tituloCompleto)
    meta('property', 'og:description', desc)
    meta('property', 'og:url', url)
    meta('property', 'og:image', imagem || HERO.imagem)

    const canonical = tagHead('link[rel="canonical"]', () => {
      const l = document.createElement('link')
      l.rel = 'canonical'
      return l
    })
    canonical.href = url
  }, [titulo, descricao, imagem, noindex, pathname])

  return null
}
