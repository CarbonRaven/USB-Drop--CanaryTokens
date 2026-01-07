"""Shortcut generator service for creating URL shortcut files."""

import plistlib
from typing import Dict, List, Tuple


class ShortcutGenerator:
    """Generates URL shortcut files for Windows and macOS."""

    def generate_windows_url(self, target_url: str, icon_url: str = None) -> bytes:
        """
        Generate a Windows .url shortcut file.

        Args:
            target_url: The URL the shortcut should open
            icon_url: Optional URL for the shortcut icon

        Returns:
            .url file content as bytes
        """
        lines = [
            "[InternetShortcut]",
            f"URL={target_url}",
        ]

        if icon_url:
            lines.append(f"IconFile={icon_url}")
            lines.append("IconIndex=0")

        # Windows uses CRLF line endings
        content = "\r\n".join(lines) + "\r\n"
        return content.encode('utf-8')

    def generate_macos_webloc(self, target_url: str) -> bytes:
        """
        Generate a macOS .webloc shortcut file.

        Args:
            target_url: The URL the shortcut should open

        Returns:
            .webloc file content as bytes (XML plist format)
        """
        plist_data = {
            'URL': target_url
        }
        return plistlib.dumps(plist_data)

    def generate_both(self, target_url: str, base_filename: str) -> List[Tuple[str, bytes]]:
        """
        Generate both Windows and macOS shortcut files.

        Args:
            target_url: The URL the shortcut should open
            base_filename: Base filename without extension

        Returns:
            List of tuples (filename, content_bytes)
        """
        return [
            (f"{base_filename}.url", self.generate_windows_url(target_url)),
            (f"{base_filename}.webloc", self.generate_macos_webloc(target_url)),
        ]

    def generate_for_type(
        self,
        target_url: str,
        filename: str,
        shortcut_type: str
    ) -> List[Tuple[str, bytes]]:
        """
        Generate shortcut files based on specified type.

        Args:
            target_url: The URL the shortcut should open
            filename: Base filename (extension will be replaced/added)
            shortcut_type: 'windows', 'macos', or 'both'

        Returns:
            List of tuples (filename, content_bytes)
        """
        # Remove any existing extension
        base_name = filename
        for ext in ['.url', '.webloc', '.lnk']:
            if filename.lower().endswith(ext):
                base_name = filename[:-len(ext)]
                break

        results = []

        if shortcut_type in ['windows', 'both']:
            results.append((
                f"{base_name}.url",
                self.generate_windows_url(target_url)
            ))

        if shortcut_type in ['macos', 'both']:
            results.append((
                f"{base_name}.webloc",
                self.generate_macos_webloc(target_url)
            ))

        return results

    def generate_desktop_ini(self, token_url: str) -> bytes:
        """
        Generate a Windows desktop.ini file with icon pointing to token URL.

        When Windows Explorer opens a folder with this desktop.ini,
        it may attempt to fetch the icon URL, triggering the token.

        Args:
            token_url: The canary token URL

        Returns:
            desktop.ini file content as bytes
        """
        content = f"""[.ShellClassInfo]
IconResource={token_url},0
[ViewState]
Mode=
Vid=
FolderType=Documents
"""
        # Windows uses CRLF and typically UTF-16 LE for desktop.ini
        # But UTF-8 also works in modern Windows
        return content.encode('utf-8')

    def generate_folder_token_files(self, token_url: str) -> List[Tuple[str, bytes]]:
        """
        Generate all files needed for a Windows folder token.

        This creates:
        - desktop.ini with icon URL pointing to token
        - hidden system attributes should be set on both files

        Args:
            token_url: The canary token URL

        Returns:
            List of tuples (filename, content_bytes)
        """
        return [
            ("desktop.ini", self.generate_desktop_ini(token_url)),
        ]


# Singleton instance
shortcut_generator = ShortcutGenerator()
