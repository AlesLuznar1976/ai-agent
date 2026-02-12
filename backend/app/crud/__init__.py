"""CRUD operacije za ai_agent bazo"""

from app.crud.uporabniki import (
    get_uporabnik_by_id,
    get_uporabnik_by_username,
    create_uporabnik,
    update_uporabnik,
    update_zadnja_prijava,
    list_uporabniki,
)
from app.crud.projekti import (
    get_projekt_by_id,
    list_projekti,
    create_projekt,
    update_projekt,
    get_casovnica,
    add_casovnica_event,
    get_next_project_number,
)
from app.crud.emaili import (
    get_email_by_id,
    get_email_by_outlook_id,
    list_emaili,
    create_email,
    update_email,
    list_nekategorizirani,
)
from app.crud.dokumenti import (
    get_dokument_by_id,
    list_dokumenti,
    create_dokument,
    delete_dokument,
)
from app.crud.chat_history import (
    add_message,
    get_user_history,
    get_project_history,
    clear_user_history,
)
from app.crud.akcije import (
    create_pending_action,
    get_pending_action,
    list_pending_actions,
    confirm_action,
    reject_action,
    fail_action,
)
