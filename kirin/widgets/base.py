"""Base widget class for shared functionality."""

from pathlib import Path

import anywidget
import traitlets


class BaseWidget(anywidget.AnyWidget):
    """Base class for Kirin widgets with shared functionality."""

    _css = Path(__file__).parent / "assets" / "shared.css"

    # Python state synchronized with JavaScript
    data = traitlets.Dict(default_value={}).tag(sync=True)

    @property
    def template_name(self) -> str:
        """Return the template filename for this widget.

        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must define template_name")

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
        template = env.get_template(self.template_name)

        # Include CSS from widget (read file if Path object)
        css_content = self._css
        if isinstance(css_content, Path):
            css_content = css_content.read_text()

        # Include JavaScript for file interactions (if template needs it)
        js_file = Path(__file__).parent / "assets" / "file_interactions.js"
        file_interactions_js = ""
        if js_file.exists():
            file_interactions_js = js_file.read_text()

        # Render template
        return template.render(
            data=data,
            css_content=css_content,
            file_interactions_js=file_interactions_js,
        )
