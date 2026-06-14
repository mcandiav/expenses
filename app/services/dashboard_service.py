from app.repositories.dashboard_repository import DashboardResumen, obtener_resumen


class DashboardService:
    @staticmethod
    def obtener_resumen() -> DashboardResumen:
        return obtener_resumen()
