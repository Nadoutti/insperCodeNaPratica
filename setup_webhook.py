import os
import time

from tally import Tally
from tally.models import Form, WebhookCreated, WebhookEventType

from app.config import conf

CLEAR_SCREEN_CMD = "cls" if os.name == "nt" else "clear"


def clear_screen() -> None:
    os.system(CLEAR_SCREEN_CMD)


def print_separator(char: str = "=", length: int = 60) -> None:
    print(char * length)


def print_header(title: str) -> None:
    print_separator()
    print(f"[#] {title}")
    print_separator()


client = Tally(api_key=conf.TALLY_API_KEY)


def select_form(page: int = 1) -> Form | None:
    """Permite ao usuário selecionar um formulário da lista disponível."""
    print("[@] Carregando formulários...")

    try:
        forms = client.forms.all(page=page)
    except Exception as e:
        print(f"[!] Erro ao carregar formulários: {e}")
        return None

    clear_screen()

    if not forms.items:
        print("[!] Nenhum formulário encontrado.")
        return None

    print_header("SELECIONE O FORMULÁRIO")

    for i, form in enumerate(forms.items, 1):
        print(f"  [{i}] {form.name}")

    if forms.has_more:
        print(f"\n  [0] -> Próxima página (página {page + 1})")

    print("\n  [q] Cancelar")
    print_separator()

    try:
        choice = input("[?] Sua escolha: ").strip().lower()

        if choice == "q":
            return None

        choice_int = int(choice)

        if choice_int == 0 and forms.has_more:
            return select_form(forms.page + 1)

        if 1 <= choice_int <= len(forms.items):
            return forms.items[choice_int - 1]

        print("[!] Opção inválida.")
        input("[@] Pressione Enter para continuar...")
        return select_form(page)

    except ValueError:
        print("[!] Por favor, digite um número válido.")
        input("[@] Pressione Enter para continuar...")
        return select_form(page)


def display_webhooks(webhooks: list) -> None:
    """Exibe a lista de webhooks formatada."""
    print("\n[>] Webhooks atuais:")
    print_separator("-")
    for i, wh in enumerate(webhooks, 1):
        print(f"  [{i}] ID: {wh.id}")
        print(f"      URL: {wh.url}")
        print(f"      Secret: {wh.signing_secret[:20]}...")
        print(f"      Events: {', '.join(wh.event_types)}")
        print()


def get_deletion_choice() -> str | None:
    """Solicita ao usuário qual ação tomar com webhooks existentes."""
    print("\n[*] OPÇÕES:")
    print_separator("-")
    print("  [0] Manter todos e criar novo webhook")
    print("  [1] Apagar todos e criar novo webhook")
    print("  [2] Selecionar webhooks específicos para apagar")
    print("  [q] Cancelar operação")
    print_separator()

    return input("[?] Sua escolha: ").strip().lower()


def delete_webhooks_by_indices(webhooks: list, indices_str: str) -> list:
    """Apaga webhooks específicos baseado nos índices fornecidos."""
    try:
        indices = [
            int(x.strip()) - 1 for x in indices_str.split(",") if x.strip().isdigit()
        ]

        deleted = []
        for idx in sorted(set(indices), reverse=True):
            if 0 <= idx < len(webhooks):
                wh = webhooks[idx]
                try:
                    client.webhooks.delete(wh.id)
                    print(f"  [+] Webhook {wh.id} apagado")
                    deleted.append(wh)
                except Exception as e:
                    print(f"  [-] Erro ao apagar webhook {wh.id}: {e}")

        return deleted

    except ValueError:
        print("[!] Formato inválido. Use números separados por vírgula (ex: 1,3,5)")
        return []


def setup_webhook(form: Form) -> WebhookCreated | None:
    """Configura webhook para o formulário selecionado."""
    clear_screen()
    print_header("CONFIGURANDO WEBHOOK")
    print(f"[@] Formulário: {form.name}")
    print(f"[@] ID: {form.id}")
    print_separator()

    try:
        webhooks = list(client.webhooks)
        form_webhooks = [wh for wh in webhooks if wh.form_id == form.id]
    except Exception as e:
        print(f"[!] Erro ao buscar webhooks: {e}")
        return None

    if form_webhooks:
        display_webhooks(form_webhooks)
        choice = get_deletion_choice()

        if choice == "q":
            print("[@] Operação cancelada.")
            return None

        elif choice == "1":
            print("\n[*] Apagando todos os webhooks...")
            for wh in form_webhooks:
                try:
                    client.webhooks.delete(wh.id)
                    print(f"  [+] Webhook {wh.id} apagado")
                except Exception as e:
                    print(f"  [-] Erro ao apagar webhook {wh.id}: {e}")

        elif choice == "2":
            indices_str = input("\n[?] Números dos webhooks (ex: 1,2,3): ")
            delete_webhooks_by_indices(form_webhooks, indices_str)
    else:
        print("[@] Nenhum webhook encontrado para este formulário.")

    print("\n[*] Criando novo webhook...")
    print(f"[@] URL: {conf.TALLY_WEBHOOK_URL}")

    try:
        new_webhook = client.webhooks.create(
            form_id=form.id,
            url=conf.TALLY_WEBHOOK_URL,
            event_types=[WebhookEventType.FORM_RESPONSE],
            signing_secret=conf.TALLY_WEBHOOK_SECRET,
            external_subscriber="insper-code-na-pratica-webhook-listener",
        )

        print_separator()
        print("[+] WEBHOOK CRIADO COM SUCESSO!")
        print_separator()
        print(f"[@] ID: {new_webhook.id}")
        print(f"[@] URL: {new_webhook.url}")
        print_separator()

        return new_webhook

    except Exception as e:
        print(f"[!] Erro ao criar webhook: {e}")
        return None


def main() -> None:
    """Função principal do script."""
    try:
        clear_screen()
        print_separator("=", 60)
        print("[#] TALLY WEBHOOK CONFIGURATOR")
        print_separator("=", 60)

        me = client.users.me()
        print(f"[@] Usuário: {me.full_name} ({me.id})\n")
    except Exception as e:
        print(f"[!] Erro ao autenticar: {e}")
        return

    time.sleep(2)

    form = select_form()

    if form is None:
        print("\n[!] Nenhum formulário selecionado. Encerrando.")
        return

    webhook = setup_webhook(form)

    if webhook is None:
        print("\n[!] Configuração de webhook não concluída.")
    else:
        print("\n[+] Processo concluído com sucesso!")


if __name__ == "__main__":
    main()
