"""
SMB Service - kreacija projektnih map na \\Luznar\izdelki share.

Ob kreaciji projekta iz agent emaila avtomatsko ustvari strukturo:
  {STRANKA}\{PRJ-številka} - {izdelek}\
    01_Emaili\
    02_Gerber\
    03_BOM\
    04_Pick_Place\
    05_Dokumentacija\
    06_Slike\
"""

import re
import unicodedata

from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol.open import (
    Open,
    CreateDisposition,
    CreateOptions,
    FileAttributes,
    ShareAccess,
    ImpersonationLevel,
    FilePipePrinterAccessMask,
)

from app.config import get_settings


SUBFOLDERS = [
    "01_Emaili",
    "02_Gerber",
    "03_BOM",
    "04_Pick_Place",
    "05_Dokumentacija",
    "06_Slike",
]


def _sanitize_name(name: str) -> str:
    """Sanitize ime za uporabo v filesystem poti."""
    # Remove diacritics
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_only = nfkd.encode("ASCII", "ignore").decode("ASCII")
    # Remove illegal chars for Windows
    sanitized = re.sub(r'[<>:"/\\|?*]', "", ascii_only)
    # Collapse whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized or "NEZNANO"


def _smb_mkdir(tree: TreeConnect, path: str) -> None:
    """Ustvari mapo na SMB share (ignore če že obstaja)."""
    try:
        dir_open = Open(tree, path)
        dir_open.create(
            impersonation_level=ImpersonationLevel.Impersonation,
            desired_access=FilePipePrinterAccessMask.FILE_LIST_DIRECTORY,
            file_attributes=FileAttributes.FILE_ATTRIBUTE_DIRECTORY,
            share_access=ShareAccess.FILE_SHARE_READ | ShareAccess.FILE_SHARE_WRITE,
            create_disposition=CreateDisposition.FILE_OPEN_IF,
            create_options=CreateOptions.FILE_DIRECTORY_FILE,
        )
        dir_open.close()
    except Exception as e:
        # If folder already exists, ignore
        if "STATUS_OBJECT_NAME_COLLISION" in str(e):
            pass
        else:
            raise


def create_project_folder(stranka_ime: str, projekt_stevilka: str, izdelek_ime: str = "") -> str:
    """Ustvari projektno mapo na SMB share.

    Struktura:
        \\server\share\{STRANKA}\{PRJ-številka} - {izdelek}\
            01_Emaili\
            02_Gerber\
            03_BOM\
            04_Pick_Place\
            05_Dokumentacija\
            06_Slike\

    Args:
        stranka_ime: Ime stranke (bo uppercase + sanitized)
        projekt_stevilka: Številka projekta (npr. PRJ-2026-004)
        izdelek_ime: Ime izdelka (opcijsko)

    Returns:
        UNC pot do ustvarjene projektne mape
    """
    settings = get_settings()

    # Sanitize names
    stranka_folder = _sanitize_name(stranka_ime).upper()
    if izdelek_ime:
        projekt_folder = f"{projekt_stevilka} - {_sanitize_name(izdelek_ime)}"
    else:
        projekt_folder = projekt_stevilka

    # Connect to SMB
    server = settings.smb_server
    conn = Connection(uuid=f"luznar-{server}", server_name=server, port=445)
    conn.connect()

    try:
        session = Session(conn, username=settings.smb_username, password=settings.smb_password)
        session.connect()

        try:
            tree = TreeConnect(session, f"\\\\{server}\\{settings.smb_share}")
            tree.connect()

            try:
                # Create stranka folder
                _smb_mkdir(tree, stranka_folder)

                # Create project folder
                projekt_path = f"{stranka_folder}\\{projekt_folder}"
                _smb_mkdir(tree, projekt_path)

                # Create subfolders
                for subfolder in SUBFOLDERS:
                    _smb_mkdir(tree, f"{projekt_path}\\{subfolder}")

                unc_path = f"\\\\{server}\\{settings.smb_share}\\{projekt_path}"
                print(f"SMB: Created project folder: {unc_path}")
                return unc_path

            finally:
                tree.disconnect()
        finally:
            session.disconnect()
    finally:
        conn.disconnect()
