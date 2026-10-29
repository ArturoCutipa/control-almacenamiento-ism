from django.core.management.base import BaseCommand

from apps.alertas.services import generar_alertas


class Command(BaseCommand):
    help = "Genera las alertas de vencimiento y bloquea los lotes vencidos (programar a diario con cron)."

    def add_arguments(self, parser):
        parser.add_argument("--plazo", type=int, default=None, help="Días de anticipación (por defecto 30).")

    def handle(self, *args, **opciones):
        r = generar_alertas(plazo=opciones["plazo"])
        self.stdout.write(self.style.SUCCESS(
            f"Lotes revisados: {r['revisados']} | alertas nuevas: {r['nuevas']} | vencidos bloqueados: {r['vencidos']}"))
