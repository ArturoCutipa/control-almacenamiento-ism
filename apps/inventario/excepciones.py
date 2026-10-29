class ReglaNegocioError(Exception):
    """Error de validación de una regla de negocio; su mensaje se muestra al usuario."""


class StockInsuficienteError(ReglaNegocioError):
    pass


class CapacidadExcedidaError(ReglaNegocioError):
    pass


class LoteNoDisponibleError(ReglaNegocioError):
    pass
