import { Mail, Phone, MessageCircle, AtSign, MapPin } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { CONTATO, whatsappLink } from '@/lib/config'

const Item = ({ icon: Icon, children }) => (
  <div className="flex items-start gap-3">
    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
      <Icon className="h-4 w-4" />
    </span>
    <div className="text-sm">{children}</div>
  </div>
)

export default function ContactInfo() {
  return (
    <div className="space-y-5">
      <Item icon={Mail}>
        <p className="font-medium">Email</p>
        <a href={`mailto:${CONTATO.email}`} className="text-muted-foreground hover:text-primary">
          {CONTATO.email}
        </a>
      </Item>
      <Item icon={Phone}>
        <p className="font-medium">Telefone</p>
        <span className="text-muted-foreground">{CONTATO.telefone}</span>
      </Item>
      <Item icon={MapPin}>
        <p className="font-medium">Endereço</p>
        <span className="text-muted-foreground">{CONTATO.endereco}</span>
      </Item>
      <Item icon={AtSign}>
        <p className="font-medium">Instagram</p>
        <a href={CONTATO.instagram} target="_blank" rel="noreferrer" className="text-muted-foreground hover:text-primary">
          Siga o ITZ
        </a>
      </Item>
      <Button asChild className="w-full sm:w-auto">
        <a href={whatsappLink('Olá! Gostaria de mais informações sobre o ITZ.')} target="_blank" rel="noreferrer">
          <MessageCircle className="mr-2 h-4 w-4" />
          Falar no WhatsApp
        </a>
      </Button>
    </div>
  )
}
