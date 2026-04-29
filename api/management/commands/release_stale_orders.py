
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from api.models import Order

class Command(BaseCommand):
    help= "Release inventory for stale orders in processing state older that X minutes."

    def add_arguments(self, parser):
        parser.add_argument("--minutes", type= int, default=30, help= "Age in minutes to consider an order stale")
        
    def handle(self, *args, **options):
        minutes= options["minutes"]
        cutoff= timezone.now()-timedelta(minutes=minutes)
        stale_orders= Order.objects.filter(status= Order.STATUS_PROCESSING, created_at__lte=cutoff)
        total= stale_orders.count()
        self.stdout.write(f"Found {total} stale orders (older than {minutes} minutes). Releasing inventory...")
        for order in stale_orders:
            for item in order.items.select_related("product"):
                p= item.product
                if p:
                    p.inventory= p.inventory + item.quantity
                    p.save(update_fields= ["inventory"])
            order.status= Order.STATUS_CANCELLED
            order.save(update_fields=["status"])
        self.stdout.write("Done.")