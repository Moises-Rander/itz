import { MapPin } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import PageHeader from '@/components/common/PageHeader'
import LeadForm from '@/components/forms/LeadForm'
import ContactInfo from '@/components/common/ContactInfo'
import { CONTATO } from '@/lib/config'

export default function Contato() {
  // Forma embutível do Google Maps (output=embed). Usamos coordenadas para o
  // pino cair no local exato; a URL de "place" comum não pode ser usada em iframe.
  const mapaSrc = `https://maps.google.com/maps?q=${encodeURIComponent(
    CONTATO.mapaCoords
  )}&z=16&output=embed`

  return (
    <>
      <PageHeader
        title="Fale conosco"
        subtitle="Estamos à disposição para tirar suas dúvidas e ajudar no que precisar."
      />
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-2">
          <Card>
            <CardContent>
              <h2 className="text-xl font-semibold">Envie uma mensagem</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Preencha o formulário e retornaremos o mais breve possível.
              </p>
              <div className="mt-6">
                <LeadForm full />
              </div>
            </CardContent>
          </Card>

          <div>
            <h2 className="text-xl font-semibold">Informações de contato</h2>
            <div className="mt-6">
              <ContactInfo />
            </div>

            <div className="mt-8">
              <h3 className="mb-3 flex items-center gap-2 font-semibold">
                <MapPin className="h-4 w-4 text-primary" /> Onde estamos
              </h3>
              <div className="overflow-hidden rounded-2xl border">
                <iframe
                  title="Mapa do ITZ"
                  src={mapaSrc}
                  className="h-64 w-full"
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
