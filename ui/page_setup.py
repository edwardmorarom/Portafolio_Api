from ui.dashboard_ui import (
    aplicar_estilos_globales,
    render_sidebar_brand,
    render_sidebar_panel,
)


def setup_dashboard_page(
    title="Dashboard Riesgo",
    subtitle="Universidad Santo Tomás",
    logo_path="assets/escudo_santo_tomas.png",
    modo_default="General",
    filtros_label="Parámetros Técnicos Avanzados",
    filtros_expanded=False,
):
    """
    Wrapper global para todas las páginas del dashboard.
    """

    # 1. Estilos globales
    aplicar_estilos_globales()

    # 2. Sidebar (branding arriba)
    render_sidebar_brand(
        title=title,
        subtitle=subtitle,
        logo_path=logo_path,
    )

        # 3. Panel de filtros
    modo, filtros_sidebar = render_sidebar_panel(
        modo_default=modo_default,
        filtros_label=filtros_label,
        filtros_expanded=filtros_expanded,
    )

    # 4. Reaplicar estilos según modo activo
    aplicar_estilos_globales(modo=modo)

    return modo, filtros_sidebar