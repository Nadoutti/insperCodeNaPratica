from tally import Tally

from app.config import Config

if Config.TALLY_API_KEY is None:
    raise ValueError("TALLY_API_KEY is not set")


tally_client = Tally(Config.TALLY_API_KEY)


def setup_webhook():
    for webhook in tally_client.webhooks:
        if webhook.url == Config.DOMAIN + "/api/v1/webhooks/tally":
            return

    # TODO: obter form_id de algum lugar a fim de chamar:

    # tally_client.webhooks.create(
    #     url=Config.DOMAIN + "/api/v1/webhooks/tally",
    #     form_id="1",
    #     external_subscriber="Insper Code <> Na Prática",
    #     signing_secret="secret", # TODO: obter de algum lugar
    # )
