from __future__ import annotations

from .base import BaseResource
from ..models.tracking import TrackingHistoryEvent, TrackingResponse, TrackingState


class TrackingResource(BaseResource):
    def track_state(self, guide: str) -> TrackingState:
        url = self._endpoints.url(self._endpoints.track_state, guide=guide)
        data = self.request("GET", url)
        
        print("Raw response data:", data)  # Debugging line
        print("Type of response data:", type(data))  # Debugging line

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data)}")
        if data.get("success") is False:
            raise ValueError(f"API error: {data.get('message', 'Unknown error')}")

        detail = data["detail"]
        return TrackingState(
            guide=detail["guia"],
            current_status=detail["estatus_actual"],
            estimated_delivery_date=detail["fecha_estimada_entrega"],
            history=[
                TrackingHistoryEvent(
                    date=e["fecha"],
                    location=e["ubicacion"],
                    status=e["estatus"],
                    description=e["descripcion"],
                )
                for e in detail.get("historial", [])
            ],
        )
    
    def track_detail(self, guide: str) -> TrackingResponse:
        url = self._endpoints.url(self._endpoints.track_detail, guide=guide)
        data = self.request("GET", url)
        
        print("Raw response data:", data)  # Debugging line
        print("Type of response data:", type(data))  # Debugging line


        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data)}")
        if data.get("success") is False:
            raise ValueError(f"API error: {data.get('message', 'Unknown error')}")
        _details = data["detail"]
        details = []
        for _detail in _details:
            detail = {
                "id":_detail.get("id"),
                "code":_detail.get("codigo"),
                "description":_detail.get("descripcion"),
                "internal_family": _detail.get("familia_interna"),
                "generic_family": _detail.get("familia_generica"),
                "tracking_number": _detail.get("guia"),
                "estimated_date": _detail.get("fecha_estimada"),
                "date": _detail.get("fecha"),
                "time": _detail.get("hora"),
                "carrier_id": _detail.get("id_mensajeria"),
                "carrier_name": _detail.get("nombre_mensajeria"),
                "tracking_link": _detail.get("tracking_link"),
                "timezone": _detail.get("zona_horaria"),
            }
            details.append(detail)
        data["detail"] = details

        return TrackingResponse.model_validate(data)
