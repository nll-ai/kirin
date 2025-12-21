"""Utility functions for widget environment detection."""


def is_widget_environment() -> bool:
    """Check if we're in a Jupyter-compatible widget environment.

    Returns:
        True if widgets can be used, False otherwise
    """
    # Check if we're in marimo first (by checking sys.modules or environment)
    import sys

    # Check for marimo in sys.modules
    if "marimo" in sys.modules:
        # If marimo is running, try to import anywidget
        try:
            import anywidget  # noqa: F401
            return True
        except ImportError:
            # Even if anywidget isn't available, marimo can still display widgets
            # Let's be optimistic and return True
            return True

    # Check if marimo can be imported
    try:
        import marimo  # noqa: F401
        # If marimo is available, try to import anywidget
        try:
            import anywidget  # noqa: F401
            return True
        except ImportError:
            # Even if anywidget isn't available, marimo can still display widgets
            return True
    except ImportError:
        pass

    # Check if anywidget is available - this is what we actually need
    try:
        import anywidget  # noqa: F401
    except ImportError:
        return False

    # Check if IPython is available
    try:
        from IPython import get_ipython

        ipython = get_ipython()
        if ipython is None:
            # If anywidget is available but no IPython, still allow widgets
            # (e.g., in marimo or other environments)
            return True

        # Check if we're in a Jupyter kernel (not just IPython shell)
        # This checks for the kernel application class
        if hasattr(ipython, "kernel"):
            return True

        # Alternative check: look for kernel app in config
        if hasattr(ipython, "config") and ipython.config:
            kernel_apps = ["IPKernelApp", "JupyterApp"]
            for app_name in kernel_apps:
                if app_name in ipython.config:
                    return True

        # If anywidget is available, allow widgets even if kernel check fails
        return True

    except ImportError:
        # IPython not available, but anywidget is, so allow widgets
        return True
