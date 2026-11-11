"""Catálogo central de tipos de email.

Cada tipo mapeia para um subject em português e um nome de template. Os
templates HTML e texto ficam em ``notifications/templates/notifications/`` com
os nomes ``<template>.html`` e ``<template>.txt``.
"""


class EmailType:
    MATRICULA_CONFIRMADA = 'MATRICULA_CONFIRMADA'
    MATRICULA_NOVA_REITOR = 'MATRICULA_NOVA_REITOR'


# tipo -> (subject, nome do template)
REGISTRY = {
    EmailType.MATRICULA_CONFIRMADA: (
        'Matrícula confirmada', 'matricula_confirmada',
    ),
    EmailType.MATRICULA_NOVA_REITOR: (
        'Nova matrícula confirmada', 'matricula_nova_reitor',
    ),
}
