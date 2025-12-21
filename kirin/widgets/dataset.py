"""Dataset widget for interactive HTML representation."""

from pathlib import Path

import anywidget
import traitlets


class DatasetWidget(anywidget.AnyWidget):
    """Interactive dataset widget with files and commit history."""

    _esm = Path(__file__).parent / "assets" / "dataset.js"
    _css = Path(__file__).parent / "assets" / "shared.css"

    # Python state synchronized with JavaScript
    data = traitlets.Dict(default_value={}).tag(sync=True)
    expanded_files = traitlets.List(default_value=[]).tag(sync=True)

    def _repr_html_(self) -> str:
        """Generate HTML representation of the widget.

        Returns:
            HTML string with widget embedded and static fallback
        """
        # Get the widget's mimebundle to extract model_id
        bundle = self._repr_mimebundle_()
        if isinstance(bundle, tuple):
            widget_data = bundle[0]
        else:
            widget_data = bundle

        # Extract model_id from widget view JSON
        widget_view = widget_data.get("application/vnd.jupyter.widget-view+json", {})
        model_id = widget_view.get("model_id", "")

        # Generate HTML that includes both the widget container and static content
        # The widget will be rendered by the notebook frontend, but we also
        # include static HTML as a fallback and for testing
        data = self.data
        static_html = self._generate_static_html(data)

        return f'<div data-anywidget-id="{model_id}">{static_html}</div>'

    def _generate_static_html(self, data: dict) -> str:
        """Generate static HTML representation from data.

        Args:
            data: Widget data dictionary

        Returns:
            Static HTML string
        """
        from jinja2 import Environment, FileSystemLoader

        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("dataset.html")

        # Include CSS from widget (read file if Path object)
        css_content = self._css
        if isinstance(css_content, Path):
            css_content = css_content.read_text()

        # Render template
        return template.render(data=data, css_content=css_content)
