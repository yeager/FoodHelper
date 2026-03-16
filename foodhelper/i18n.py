"""Internationalization support for the application."""

import gettext
import locale
import os


def setup_i18n(domain, localedir=None):
    """Set up internationalization for the application.
    
    Args:
        domain: The translation domain name (usually the app name)
        localedir: Path to locale directory (optional)
    """
    if localedir is None:
        # Look for locale data relative to this module
        localedir = os.path.join(os.path.dirname(__file__), '..', 'locale')
        if not os.path.exists(localedir):
            localedir = None
    
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        # Fallback if system locale is not available
        pass
    
    # Set up gettext
    try:
        if localedir and os.path.exists(localedir):
            gettext.bindtextdomain(domain, localedir)
            gettext.textdomain(domain)
        else:
            # No locale directory found, use system default
            gettext.textdomain(domain)
    except Exception:
        # If gettext setup fails, continue without translation
        pass
    
    # Return the translation function
    return gettext.gettext


# Set up translation function
_ = gettext.gettext
