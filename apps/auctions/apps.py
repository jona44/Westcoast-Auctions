from django.apps import AppConfig


class AuctionsConfig(AppConfig):
    name = 'apps.auctions'
    label = 'auctions'

    def ready(self):
        import apps.auctions.signals
