"""
HTML Dashboard Renderer

Responsible for assembling the complete HTML document by combining:
- CSS styles from DashboardStyles
- HTML structure from DashboardHTML
- JavaScript from DashboardScripts

This renderer follows the template method pattern, assembling independent
components into a cohesive HTML document.

Design Philosophy:
    - Single Responsibility: Only responsible for HTML document assembly
    - Dependency Inversion: Depends on abstract component interfaces
    - Open/Closed: Open for extension (new components) without modification

Author: Claude Code
Version: 2.0.0 (Refactored modular design)
"""

from app.routes.dashboard.components import (
    DashboardStyles,
    DashboardScripts,
    DashboardHTML,
)


class HTMLRenderer:
    """
    Assembles complete HTML dashboard from component parts.

    This class uses the template method pattern to combine CSS, HTML structure,
    and JavaScript into a self-contained HTML document. The resulting HTML has
    no external dependencies and can be served directly as HTMLResponse.

    Attributes:
        None (stateless renderer)

    Methods:
        render() -> str: Generate complete HTML document

    Example:
        ```python
        renderer = HTMLRenderer()
        html_content = renderer.render()
        return HTMLResponse(content=html_content)
        ```
    """

    def render(self) -> str:
        """
        Render complete HTML dashboard.

        Assembles all UI components (styles, structure, scripts) into a
        self-contained HTML5 document. The document includes:
        - Complete DOCTYPE and HTML5 boilerplate
        - Embedded CSS in <style> tag
        - Semantic HTML structure
        - Embedded JavaScript in <script> tag
        - Responsive viewport meta tag
        - Character encoding declaration

        Returns:
            str: Complete HTML document ready for HTMLResponse

        Note:
            The HTML is self-contained with no external dependencies.
            All assets (CSS, JS) are embedded for simplicity and performance.
        """
        styles = DashboardStyles.get_styles()
        scripts = DashboardScripts.get_scripts()
        html_structure = DashboardHTML.get_structure()

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auth API - Technical Dashboard</title>
    <style>
{styles}
    </style>
</head>
<body>
{html_structure}
    <script>
{scripts}
    </script>
</body>
</html>"""
